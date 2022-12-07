from json import dumps

import yaml

MGMT_NETID = object()


class VMSpec:
    # ref: https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstancespec
    # defaults
    cpu_sockets = cpu_threads = 1
    run_strategy = "RerunOnFailure",
    eviction_strategy = "LiveMigrate"
    hostname = None
    machine_type = ""
    usbtablet = True

    # TODOs:
    # node selector(affinity)
    # userdata/networkdata enhancement

    def __init__(self, cpu_cores, memory, mgmt_network=True):
        self.cpu_cores = cpu_cores
        self.memory = memory
        self.volumes, self.networks = [], []
        self._firmwares, self._features = dict(), dict()
        if mgmt_network:
            self.add_network("default", MGMT_NETID)

        # default
        self.acpi = True
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

    @property
    def acpi(self):
        return self._features['acpi'].get('enabled')

    @acpi.setter
    def acpi(self, enable):
        self._features['acpi'] = enable

    @property
    def efi_boot(self):
        return 'efi' in self._firmwares.get('bootloader', dict())

    @efi_boot.setter
    def efi_boot(self, enable):
        if enable:
            self._features['smm'] = dict(enabled=True)
            self._firmwares['bootloader'] = dict(efi=dict(secureBoot=True))
        else:
            self._features.pop('smm', None)
            self._firmwares.pop('bootloader', None)

    @property
    def secure_boot(self):
        return self.efi_boot and self._firmwares['bootloader']['efi']['secureBoot']

    @secure_boot.setter
    def secure_boot(self, enable):
        if enable:
            self.efi_boot = True
            self._firmwares['bootloader']['efi']['secureBoot'] = True
        else:
            self.efi_boot = False

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
        return self._cloudinit_vol['volume']['cloudInitNoCloud']['userData']

    @user_data.setter
    def user_data(self, val):
        self._cloudinit_vol['volume']['cloudInitNoCloud']['userData'] = val

    @property
    def network_data(self):
        return self._cloudinit_vol['volume']['cloudInitNoCloud']['networkData']

    @network_data.setter
    def network_data(self, val):
        self._cloudinit_vol['volume']['cloudInitNoCloud']['networkData'] = val

    def add_cd_rom(self, name, image_id, size=10, bus="SATA"):
        vol_spec = VolumeSpec(size, annotations={"harvesterhci.io/imageId": image_id})

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
        vol_spec = VolumeSpec(size, annotations={"harvesterhci.io/imageId": image_id})

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

    def add_volume(self, name, size, type="disk", bus="virtio", storage_cls=None):
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
        for v in self.volumes:
            if 'claim' in v:
                v['claim'] = v['claim'].to_dict(name, namespace)
                disk_name = v['volume']['name']
                v['volume']['persistentvolumeclaim']['claimName'] = f"{name}-{disk_name}"

    def to_dict(self, name, namespace, hostname=None):
        self._update_bootorder()
        self._update_volume_spec(name, namespace)
        volumes = self.volumes + [self._cloudinit_vol]
        mem = f"{self.memory}Gi" if isinstance(self.memory, int) else self.memory

        machine = dict(type=self.machine_type)
        cpu = dict(sockets=self.cpu_sockets, thread=self.cpu_threads)
        resources = dict(cpu=self.cpu_cores, memory=mem)

        volume_claims = dumps([v['claim'] for v in volumes if 'claim' in v])

        data = {
            "type": "kubevirt.io.virtualmachine",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": {
                    "harvesterhci.io/volumeClaimTemplates": volume_claims
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
                                "intrefaces": [n['iface'] for n in self.networks],
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

        return data


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
            return self._data

        return data

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
