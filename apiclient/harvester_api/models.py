from copy import deepcopy
from json import dumps, loads

import yaml

MGMT_NETID = object()
DEFAULT_STORAGE_CLS = "harvester-longhorn"


class RestoreSpec:
    def __init__(self, new_vm, vm_name=None, namespace=None, delete_volumes=None):
        self.new_vm = new_vm
        self.vm_name = vm_name
        self.namespace = namespace
        self.delete_volumes = delete_volumes

    def __repr__(self):
        return (f"{__class__.__name__}({self.new_vm},"
                f" {self.vm_name}, {self.namespace}, {self.delete_volumes})")

    def to_dict(self, name, namespace, existing_vm):
        data = {
            "type": "harvesterhci.io.virtualmachinerestore",
            "metadata": {
                "generateName": f"restore-{name}-",
                "name": "",
                "namespace": self.namespace or namespace
            },
            "spec": {
                "target": {
                    "apiGroup": "kubevirt.io",
                    "kind": "VirtualMachine",
                    "name": self.vm_name
                },
                "virtualMachineBackupName": name,
                "virtualMachineBackupNamespace": namespace
            }
        }
        spec = data['spec']
        if self.new_vm:
            spec['newVM'] = self.new_vm
        else:
            spec['deletionPolicy'] = "delete" if self.delete_volumes else "retain"
            spec['target']['name'] = existing_vm

        return deepcopy(data)

    @classmethod
    def for_new(cls, vm_name, namespace=None):
        return cls(True, vm_name, namespace)

    @classmethod
    def for_existing(cls, delete_volumes=True):
        return cls(False, delete_volumes=delete_volumes)


class SnapshotRestoreSpec(RestoreSpec):
    @classmethod
    def for_new(cls, vm_name):
        return super().for_new(vm_name, None)

    @classmethod
    def for_existing(cls):
        return super().for_existing(False)


class VMSpec:
    # ref: https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstancespec
    # defaults
    cpu_sockets = cpu_threads = 1
    run_strategy = "RerunOnFailure"
    eviction_strategy = "LiveMigrate"
    hostname = machine_type = ""
    usbtablet = True
    _data = None

    # TODOs:
    # node selector(affinity)
    # userdata/networkdata enhancement
    # SSH Key

    def __init__(self, cpu_cores, memory, description="", reserved_mem="", os_type="",
                 mgmt_network=True, guest_agent=True):

        self._cloudinit_vol = {
            "disk": {
                "name": "cloudinitdisk",
                "disk": dict(bus="virtio")
            },
            "volume": {
                "name": "cloudinitdisk",
                "cloudInitNoCloud": {
                    "networkData": "",
                    "userData": "#cloud-config\npackage_update: true"
                }
            }
        }

        # default
        self.volumes, self.networks = [], []
        self._firmwares, self._features = dict(), dict()
        self.acpi = True
        # initial data
        self.cpu_cores = cpu_cores
        self.memory = memory
        self.mgmt_network = mgmt_network
        self.guest_agent = guest_agent
        self.description = description
        self.reserved_mem = reserved_mem
        self.os_type = os_type

    @property
    def mgmt_network(self):
        return bool([n for n in self.networks if n['network'].get('pod', None) is not None])

    @mgmt_network.setter
    def mgmt_network(self, enable):
        if enable:
            if not self.mgmt_network:
                self.add_network("default", MGMT_NETID)
        else:
            self.networks = [n for n in self.networks if n['network'].get('pod', None) is None]

    @property
    def acpi(self):
        return self._features['acpi'].get('enabled')

    @acpi.setter
    def acpi(self, enable):
        self._features['acpi'] = dict(enabled=enable)

    @property
    def efi_boot(self):
        return 'efi' in self._firmwares.get('bootloader', dict())

    @efi_boot.setter
    def efi_boot(self, enable):
        if enable:
            self._features['smm'] = dict(enabled=False)
            self._firmwares['bootloader'] = dict(efi=dict(secureBoot=False))
        else:
            self._features.pop('smm', None)
            self._firmwares.pop('bootloader', None)

    @property
    def secure_boot(self):
        return self.efi_boot and self._firmwares['bootloader']['efi'].get('secureBoot', False)

    @secure_boot.setter
    def secure_boot(self, enable):
        if enable:
            self.efi_boot = True
            self._firmwares['bootloader']['efi']['secureBoot'] = True
            self._features['smm']['enabled'] = True
        else:
            self.efi_boot = False
            self.efi_boot = True

    @property
    def guest_agent(self):
        return 'qemu-guest-agent.service' in self.user_data

    @guest_agent.setter
    def guest_agent(self, enable):
        cmd = 'systemctl enable --now qemu-guest-agent.service'
        userdata = yaml.safe_load(self.user_data) or dict()
        pkgs = userdata.get('packages', [])
        runcmds = [' '.join(c) for c in userdata.get('runcmd', [])]
        if enable:
            if 'qemu-guest-agent' not in pkgs:
                userdata.setdefault('packages', []).append('qemu-guest-agent')

            if cmd not in runcmds:
                userdata.setdefault('runcmd', []).append(cmd.split())
        else:
            userdata['packages'] = [p for p in pkgs if p != 'qemu-guest-agent']
            userdata['runcmd'] = [c.split() for c in runcmds if c != cmd]

        self.user_data = "#cloud-config\n" + yaml.dump(userdata)

    @property
    def user_data(self):
        return self._cloudinit_vol['volume']['cloudInitNoCloud'].get('userData', "")

    @user_data.setter
    def user_data(self, val):
        if isinstance(val, str):
            if val.split('\n', 1)[0] != "#cloud-config":
                val = f"#cloud-config\n{val}"
        self._cloudinit_vol['volume']['cloudInitNoCloud']['userData'] = val

    @property
    def network_data(self):
        return self._cloudinit_vol['volume']['cloudInitNoCloud'].get('networkData', "")

    @network_data.setter
    def network_data(self, val):
        self._cloudinit_vol['volume']['cloudInitNoCloud']['networkData'] = val

    def add_cd_rom(self, name, image_id, size=10, bus="SATA"):
        vol_spec = VolumeSpec(size, storage_cls=f"longhorn-{image_id.split('/')[1]}",
                              annotations={"harvesterhci.io/imageId": image_id})

        vol = {
            "claim": vol_spec,
            "disk": {
                "name": name,
                "cdrom": dict(bus=bus),
                "bootOrder": 1
            },
            "volume": {
                "name": name,
                "persistentVolumeClaim": dict(claimName="")
            }
        }

        self.volumes.append(vol)
        return vol

    def add_image(self, name, image_id, size=10, bus="virtio", type="disk"):
        vol_spec = VolumeSpec(size, storage_cls=f"longhorn-{image_id.split('/')[1]}",
                              annotations={"harvesterhci.io/imageId": image_id})

        vol = {
            "claim": vol_spec,
            "disk": {
                type: dict(bus=bus),
                "name": name,
                "bootOrder": 1
            },
            "volume": {
                "name": name,
                "persistentVolumeClaim": dict(claimName="")
            }
        }
        self.volumes.append(vol)
        return vol

    def add_container(self, name, docker_image, bus="virtio", type="disk"):
        vol = {
            "disk": {
                type: dict(bus=bus),
                "name": name,
                "bootOrder": 1
            },
            "volume": {
                "name": name,
                "containerDisk": dict(image=docker_image)
            }
        }

        self.volumes.append(vol)
        return vol

    def add_volume(self, name, size, type="disk", bus="virtio", storage_cls=DEFAULT_STORAGE_CLS):
        vol_spec = VolumeSpec(size, storage_cls)
        vol = {
            "claim": vol_spec,
            "disk": {
                type: dict(bus=bus),
                "name": name,
                "bootOrder": 1
            },
            "volume": {
                "name": name,
                "persistentVolumeClaim": dict(claimName="")
            }
        }

        self.volumes.append(vol)
        return vol

    def add_existing_volume(self, name, volume_name, type="disk"):
        vol = {
            "disk": {
                type: dict(bus="virtio"),
                "name": name,
                "bootOrder": 1
            },
            "volume": {
                "name": name,
                "persistentVolumeClaim": dict(claimName=volume_name)
            }
        }

        self.volumes.append(vol)
        return vol

    def add_network(self, name, net_uid, model="virtio", mac_addr=None):
        net = {
            "iface": dict(model=model, name=name),
            "network": dict(name=name)
        }

        if net_uid is MGMT_NETID:
            net['iface']["masquerade"] = dict()
            net['network']['pod'] = dict()
        else:
            net['iface']["bridge"] = dict()
            net['network']['multus'] = dict(networkName=net_uid)

        if mac_addr is not None:
            net['iface']['macAddress'] = mac_addr

        self.networks.append(net)
        return net

    def _update_bootorder(self):
        its = enumerate([v['disk'] for v in self.volumes if 'disk' in v], 1)
        for idx, disk in its:
            disk['bootOrder'] = idx

    def _update_volume_spec(self, name, namespace):
        volumes = []
        for v in deepcopy(self.volumes):
            if 'claim' in v:
                disk_name = v['volume']['name']
                v['claim'] = v['claim'].to_dict(f"{name}-{disk_name}", namespace)
                v['volume']['persistentVolumeClaim']['claimName'] = f"{name}-{disk_name}"
            volumes.append(v)
        return volumes

    def to_dict(self, name, namespace, hostname=""):
        self._update_bootorder()
        volumes = self._update_volume_spec(name, namespace) + [self._cloudinit_vol]
        mem = f"{self.memory}Gi" if isinstance(self.memory, int) else self.memory

        machine = dict(type=self.machine_type)
        cpu = dict(cores=self.cpu_cores, sockets=self.cpu_sockets, thread=self.cpu_threads)
        resources = dict(cpu=self.cpu_cores, memory=mem)

        volume_claims = dumps([v['claim'] for v in volumes if 'claim' in v])

        data = {
            "type": "kubevirt.io.virtualmachine",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": {
                    "harvesterhci.io/volumeClaimTemplates": volume_claims,
                    "field.cattle.io/description": self.description
                },
                "labels": {
                    "harvesterhci.io/creator": "harvester",
                    "harvesterhci.io/os": self.os_type
                }
            },
            "spec": {
                "runStrategy": self.run_strategy,
                "template": {
                    "metadata": {
                        "labels": {
                            "harvesterhci.io/vmName": name
                        }
                    },
                    "spec": {
                        "evictionStrategy": self.eviction_strategy,
                        "hostname": hostname or self.hostname or name,
                        "networks": [n['network'] for n in self.networks],
                        "volumes": [v['volume'] for v in volumes if 'volume' in v],
                        "domain": {
                            "machine": machine,
                            "cpu": cpu,
                            "resources": dict(limits=resources),
                            "features": self._features,
                            "firmware": self._firmwares,
                            "devices": {
                                "interfaces": [n['iface'] for n in self.networks],
                                "disks": [v['disk'] for v in volumes if 'disk' in v]
                            },
                        }
                    }
                }
            }
        }

        if self.usbtablet:
            inputs = [dict(bus="usb", name="tablet", type="tablet")]
            data['spec']['template']['spec']['domain']['devices']['inputs'] = inputs

        if self.reserved_mem:
            r_mem = self.reserved_mem
            r_mem = f"{r_mem}Mi" if isinstance(r_mem, (int, float)) else r_mem
            data['metadata']['annotations']["harvesterhci.io/reservedMemory"] = r_mem

        if self._data:
            self._data['metadata'].update(data['metadata'])
            self._data['spec'].update(data['spec'])
            return deepcopy(self._data)

        return deepcopy(data)

    @classmethod
    def from_dict(cls, data):
        if data['type'] != 'kubevirt.io.virtualmachine':
            raise ValueError("Only support extract data comes from 'kubevirt.io.virtualmachine'")

        data = deepcopy(data)
        spec, metadata = data.get('spec', {}), data.get('metadata', {})
        vm_spec = spec['template']['spec']

        os_type = metadata.get('labels', {}).get("harvesterhci.io/os", "")
        desc = metadata['annotations'].get("field.cattle.io/description", "")
        reserved_mem = metadata['annotations'].get("harvesterhci.io/reservedMemory", "")
        run_strategy = spec['runStrategy']
        # ???: volume template claims not load

        hostname = vm_spec['hostname']
        eviction_strategy = vm_spec['evictionStrategy']
        networks = vm_spec['networks']
        volumes = vm_spec['volumes']
        machine = vm_spec['domain']['machine']
        cpu = vm_spec['domain']['cpu']
        mem = vm_spec['domain']['resources']['limits']['memory']
        features = vm_spec['domain'].get('features', {})
        firmware = vm_spec['domain'].get('firmware', {})
        devices = vm_spec['domain']['devices']

        obj = cls(cpu['cores'], mem, desc, reserved_mem, os_type)
        obj.cpu_sockets, obj.cpu_threads = cpu.get('sockets', 1), cpu.get('threads', 1)
        obj.run_strategy = run_strategy
        obj.eviction_strategy = eviction_strategy
        obj.hostname = hostname
        obj.machine_type = machine.get('type', "")
        obj.usbtablet = devices.get('inputs') and bool(devices['inputs'][0])

        obj._features = features
        obj._firmwares = firmware
        obj.networks = [dict(iface=i, network=n) for i, n in zip(devices['interfaces'], networks)]
        obj.volumes = [dict(disk=d, volume=v) for d, v in zip(devices['disks'][:-1], volumes[:-1])]
        obj._cloudinit_vol = dict(disk=devices['disks'][-1], volume=volumes[-1])
        obj._data = data
        return obj


class VolumeSpec:
    volume_mode = "Block"
    _data = None

    def __init__(self, size, storage_cls=None, description=None, annotations=None):
        self.access_modes = ["ReadWriteMany"]

        self.size = size
        self.storage_cls = storage_cls
        self.description = description
        self.annotations = annotations

    def to_dict(self, name, namespace, image_id=None):
        annotations = self.annotations or dict()
        size = f"{self.size}Gi" if isinstance(self.size, (int, float)) else self.size
        data = {
            "type": "persistentvolumeclaim",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations
            },
            "spec": {
                "accessModes": self.access_modes,
                "resources": {
                    "requests": dict(storage=size)
                },
                "volumeMode": self.volume_mode
            }
        }

        if image_id is not None:
            annotations.update({"harvesterhci.io/imageId": image_id})
        if self.description is not None:
            annotations.update({"field.cattle.io/description": self.description})
        if self.storage_cls is not None:
            data['spec']['storageClassName'] = self.storage_cls

        if self._data:
            self._data['metadata'].update(data['metadata'])
            self._data['spec'].update(data['spec'])
            return deepcopy(self._data)

        return deepcopy(data)

    @classmethod
    def from_dict(cls, data):
        spec, metadata = data.get('spec', {}), data.get('metadata', {})
        annotations = metadata.get('annotations')
        size = spec['resources']['requests']['storage']
        storage_cls = spec.get('storageClassName')

        obj = cls(size, storage_cls, annotations.get("field.cattle.io/description"))
        obj.annotations = annotations
        obj._data = data

        return obj


class BaseSettingSpec:
    """ Base class for instance check and create"""
    _name = ""  # to point out the name of setting
    _default = False  # to point out to use default value

    def __init__(self, value=None):
        self.value = value or dict()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    @property
    def use_default(self):
        return self._default

    @use_default.setter
    def use_default(self, val):
        self._default = val

    def to_dict(self, data):
        return dict(value=dumps(self.value))

    @classmethod
    def from_dict(cls, data):
        for c in cls.__subclasses__():
            if c._name == data.get('metadata', {}).get('name'):
                return c.from_dict(data)
        return cls(data)


class BackupTargetSpec(BaseSettingSpec):
    _name = "backup-target"

    @property
    def type(self):
        return self.value.get('type')

    def clear(self):
        self.value = dict()

    @classmethod
    def from_dict(cls, data):
        value = loads(data.get('value', "{}"))
        return cls(value)

    @classmethod
    def S3(cls, bucket, region, access_id, access_secret, endpoint="", virtual_hosted=None):
        data = {
            "type": "s3",
            "endpoint": endpoint,
            "bucketName": bucket,
            "bucketRegion": region,
            "accessKeyId": access_id,
            "secretAccessKey": access_secret
        }
        if virtual_hosted is not None:
            data['virtualHostedStyle'] = virtual_hosted
        return cls(data)

    @classmethod
    def NFS(cls, endpoint):
        return cls(dict(type="nfs", endpoint=endpoint))


class StorageNetworkSpec(BaseSettingSpec):
    _name = "storage-network"

    @classmethod
    def disable(cls):
        obj = cls()
        obj.use_default = True
        return obj

    @classmethod
    def enable_with(cls, vlan_id, cluster_network, ip_range, *excludes):
        return cls({
            "vlan": vlan_id,
            "clusterNetwork": cluster_network,
            "range": ip_range,
            "exclude": excludes
        })

    @classmethod
    def from_dict(cls, data):
        value = loads(data.get('value', "{}"))
        return cls(value)

    def to_dict(self, data):
        if self.use_default or not self.value:
            return dict(value=None)
        return super().to_dict(data)


class OverCommitConfigSpec(BaseSettingSpec):
    _name = 'overcommit-config'

    @property
    def cpu(self):
        return self.value['cpu']

    @cpu.setter
    def cpu(self, val):
        self.value['cpu'] = val

    @property
    def memory(self):
        return self.value['memory']

    @memory.setter
    def memory(self, val):
        self.value['memory'] = val

    @property
    def storage(self):
        return self.value['storage']

    @storage.setter
    def storage(self, val):
        self.value['storage'] = val

    @classmethod
    def from_dict(cls, data):
        value = loads(data.get('value', '{}'))
        return cls(value)

    def to_dict(self, data):
        if self.use_default or not self.value:
            return dict(value=data['default'])
        return super().to_dict(data)
