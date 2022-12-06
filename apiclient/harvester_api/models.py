class VMSpec:
    # ref: https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstancespec
    # defaults
    sockets = threads = 1
    run_strategy = "RerunOnFailure",
    eviction_strategy = "LiveMigrate"
    acpi = True
    # cpu, mem, volumes, networks
    # VolumeClaimTemplates
    # affinity

    def __init__(self, cpu=1, mem=1):
        pass

    def to_dict(self, name, hostname=None):
        acpi = dict(enabled=self.acpi)
        machine = dict()
        cpu = dict(sockets=self.sockets, thread=self.threads)
        devices = dict()
        resources = dict()
        networks = []
        volumes = []

        return {
            "runStrategy": self.run_strategy,
            "template": {
                "metadata": {
                    "labels": {
                        "harvesterhci.io/vmName": name
                    }
                },
                "spec": {
                    "evictionStrategy": self.eviction_strategy,
                    "hostname": hostname or name,
                    "networks": networks,
                    "volumes": volumes,
                    "domain": {
                        "machine": machine,
                        "cpu": cpu,
                        "devices": devices,
                        "resources": resources,
                        "features": dict(acpi=acpi)
                    }
                }
            }
        }
