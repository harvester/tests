"""
Harvester API Client - Standalone implementation for Robot Framework tests
This module provides a complete API client for interacting with Harvester HCI.
"""

import requests
import json
from urllib.parse import urljoin
from typing import Dict, Any, Tuple
import urllib3

# Disable SSL warnings for self-signed certificates in test environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HarvesterAPIException(Exception):
    """Base exception for Harvester API errors"""
    pass


class HarvesterAPIClient:
    """Main Harvester API Client"""

    def __init__(self, endpoint: str, username: str = "admin", password: str = "password",
                 verify_ssl: bool = False, token: str = None):
        """
        Initialize Harvester API client

        Args:
            endpoint: Harvester endpoint URL (e.g., https://harvester.example.com)
            username: Admin username
            password: Admin password
            verify_ssl: Whether to verify SSL certificates
            token: Authentication token (if already obtained)
        """
        self.endpoint = endpoint.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = token
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # Initialize resource managers
        self.vms = VMManager(self)
        self.images = ImageManager(self)
        self.volumes = VolumeManager(self)
        self.networks = NetworkManager(self)
        self.hosts = HostManager(self)
        self.backups = BackupManager(self)
        self.settings = SettingsManager(self)
        self.keypairs = KeypairManager(self)

        # Authenticate if token not provided
        if not self.token:
            self.authenticate()

    def authenticate(self):
        """Authenticate with Harvester and obtain token"""
        auth_url = urljoin(self.endpoint, '/v3-public/localProviders/local?action=login')

        payload = {
            "username": self.username,
            "password": self.password,
            "description": "Robot Framework Test Session",
            "responseType": "cookie",
            "ttl": 57600000
        }

        response = self.session.post(auth_url, json=payload, verify=self.verify_ssl)

        if response.status_code != 200:
            raise HarvesterAPIException(
                f"Authentication failed: {response.status_code} - {response.text}"
            )

        # Extract token from cookies
        self.token = self.session.cookies.get('R_SESS')
        if not self.token:
            raise HarvesterAPIException("Failed to obtain authentication token")

        return self.token

    def _request(self, method: str, path: str, **kwargs) -> Tuple[int, Any]:
        """
        Make HTTP request to Harvester API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path
            **kwargs: Additional arguments for requests

        Returns:
            Tuple of (status_code, response_data)
        """
        url = urljoin(self.endpoint, path)

        # Set default headers
        headers = kwargs.pop('headers', {})
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                verify=self.verify_ssl,
                **kwargs
            )

            # Try to parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = response.text

            return response.status_code, data

        except requests.exceptions.RequestException as e:
            raise HarvesterAPIException(f"Request failed: {str(e)}")

    def get(self, path: str, **kwargs) -> Tuple[int, Any]:
        """GET request"""
        return self._request('GET', path, **kwargs)

    def post(self, path: str, data: Dict = None, **kwargs) -> Tuple[int, Any]:
        """POST request"""
        if data:
            kwargs['json'] = data
        return self._request('POST', path, **kwargs)

    def put(self, path: str, data: Dict = None, **kwargs) -> Tuple[int, Any]:
        """PUT request"""
        if data:
            kwargs['json'] = data
        return self._request('PUT', path, **kwargs)

    def delete(self, path: str, **kwargs) -> Tuple[int, Any]:
        """DELETE request"""
        return self._request('DELETE', path, **kwargs)


class ResourceManager:
    """Base class for resource managers"""

    def __init__(self, client: HarvesterAPIClient):
        self.client = client
        self.api_version = 'v1'
        self.namespace = 'default'

    def _build_path(self, resource_type: str, name: str = None, namespace: str = None,
                    action: str = None) -> str:
        """Build API path for resource"""
        ns = namespace or self.namespace
        path = f"/{self.api_version}/{resource_type}"

        if ns:
            path = f"/{self.api_version}/namespaces/{ns}/{resource_type}"

        if name:
            path = f"{path}/{name}"

        if action:
            path = f"{path}?action={action}"

        return path


class VMManager(ResourceManager):
    """Virtual Machine resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'kubevirt.io.virtualmachines'

    def _build_vm_path(self, name: str = None, namespace: str = 'default',
                       action: str = None) -> str:
        """Build API path for VM resources - Harvester specific format"""
        # Harvester uses: /v1/kubevirt.io.virtualmachines/{namespace}/{name}
        path = f"/{self.api_version}/{self.resource_type}"

        if namespace:
            path = f"{path}/{namespace}"

        if name:
            path = f"{path}/{name}"

        if action:
            path = f"{path}?action={action}"

        return path

    def create(self, name: str, spec: 'VMSpec',
               namespace: str = 'default') -> Tuple[int, Dict]:
        """Create a virtual machine"""
        path = self._build_vm_path(namespace=namespace)
        vm_data = spec.to_dict(name, namespace)
        return self.client.post(path, data=vm_data)

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get virtual machine"""
        path = self._build_vm_path(name=name, namespace=namespace)
        return self.client.get(path)

    def get_status(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get virtual machine status"""
        return self.get(name, namespace)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List virtual machines"""
        path = self._build_vm_path(namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete virtual machine"""
        path = self._build_vm_path(name=name, namespace=namespace)
        return self.client.delete(path)

    def start(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Start virtual machine"""
        path = self._build_vm_path(name=name, namespace=namespace, action='start')
        return self.client.post(path)

    def stop(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Stop virtual machine"""
        path = self._build_vm_path(name=name, namespace=namespace, action='stop')
        return self.client.post(path)

    def restart(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Restart virtual machine"""
        path = self._build_vm_path(name=name, namespace=namespace, action='restart')
        return self.client.post(path)

    def migrate(self, name: str, target_node: str,
                namespace: str = 'default') -> Tuple[int, Dict]:
        """Migrate virtual machine to target node"""
        path = self._build_vm_path(name=name, namespace=namespace, action='migrate')
        data = {'nodeName': target_node}
        return self.client.post(path, data=data)

    def create_snapshot(self, name: str, snapshot_name: str,
                        namespace: str = 'default') -> Tuple[int, Dict]:
        """Create VM snapshot"""
        snapshot_path = f"/{self.api_version}/namespaces/{namespace}/virtualmachinesnapshots"
        snapshot_data = {
            'apiVersion': 'harvesterhci.io/v1beta1',
            'kind': 'VirtualMachineSnapshot',
            'metadata': {
                'name': snapshot_name,
                'namespace': namespace
            },
            'spec': {
                'source': {
                    'name': name,
                    'kind': 'VirtualMachine'
                }
            }
        }
        return self.client.post(snapshot_path, data=snapshot_data)

    def create_backup(self, name: str, backup_name: str,
                      namespace: str = 'default') -> Tuple[int, Dict]:
        """Create VM backup"""
        backup_path = f"/{self.api_version}/namespaces/{namespace}/virtualmachinebackups"
        backup_data = {
            'apiVersion': 'harvesterhci.io/v1beta1',
            'kind': 'VirtualMachineBackup',
            'metadata': {
                'name': backup_name,
                'namespace': namespace
            },
            'spec': {
                'source': {
                    'name': name,
                    'kind': 'VirtualMachine'
                }
            }
        }
        return self.client.post(backup_path, data=backup_data)

    class Spec:
        """VM Specification builder"""

        def __init__(self, cpu: int = 2, memory: str = "4Gi"):
            self.cpu = cpu
            self.memory = memory
            self.disks = []
            self.networks = []
            self.volumes = []
            self.numberOfReplicas = 3
            self.running = True

        def add_image(self, name: str, image_id: str):
            """Add image disk"""
            self.disks.append({
                'name': name,
                'disk': {'bus': 'virtio'},
                'bootOrder': 1
            })
            self.volumes.append({
                'name': name,
                'dataVolume': {
                    'name': f"{name}-dv"
                }
            })

        def add_network(self, name: str):
            """Add network interface"""
            self.networks.append({
                'name': name,
                'pod': {} if name == 'default' else {'name': name}
            })

        def add_volume(self, name: str, size: str):
            """Add additional volume"""
            self.volumes.append({
                'name': name,
                'dataVolume': {
                    'name': f"{name}-dv"
                }
            })

        def to_dict(self, vm_name: str, namespace: str) -> Dict:
            """Convert spec to Harvester VM definition"""
            interfaces = [
                {'name': net['name'], 'bridge': {}}
                for net in self.networks
            ]
            return {
                'apiVersion': 'kubevirt.io/v1',
                'kind': 'VirtualMachine',
                'metadata': {
                    'name': vm_name,
                    'namespace': namespace
                },
                'spec': {
                    'running': self.running,
                    'template': {
                        'spec': {
                            'domain': {
                                'cpu': {
                                    'cores': self.cpu,
                                    'sockets': 1,
                                    'threads': 1
                                },
                                'devices': {
                                    'disks': self.disks,
                                    'interfaces': interfaces
                                },
                                'resources': {
                                    'requests': {
                                        'memory': self.memory
                                    }
                                }
                            },
                            'networks': self.networks,
                            'volumes': self.volumes
                        }
                    }
                }
            }


# Alias for VMManager.Spec to resolve 'VMSpec' undefined error
VMSpec = VMManager.Spec


class ImageManager(ResourceManager):
    """Image resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'harvesterhci.io.virtualmachineimages'

    def _build_image_path(self, name: str = None,
                          namespace: str = 'default', action: str = None) -> str:
        """Build API path for image resources - Harvester specific format"""
        # Harvester uses: /v1/harvesterhci.io.virtualmachineimages/{namespace}/{name}
        path = f"/{self.api_version}/{self.resource_type}"

        if namespace:
            path = f"{path}/{namespace}"

        if name:
            path = f"{path}/{name}"

        if action:
            path = f"{path}?action={action}"

        return path

    def create_by_url(self, name: str, url: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Create image from URL"""
        path = self._build_image_path(namespace=namespace)
        image_data = {
            'apiVersion': 'harvesterhci.io/v1beta1',
            'kind': 'VirtualMachineImage',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'displayName': name,
                'sourceType': 'download',
                'url': url
            }
        }
        return self.client.post(path, data=image_data)

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get image"""
        path = self._build_image_path(name=name, namespace=namespace)
        return self.client.get(path)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List images"""
        path = self._build_image_path(namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete image"""
        path = self._build_image_path(name=name, namespace=namespace)
        return self.client.delete(path)


class VolumeManager(ResourceManager):
    """Volume resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'persistentvolumeclaims'

    def create(self, name: str, size: str, storage_class: str = 'longhorn',
               namespace: str = 'default') -> Tuple[int, Dict]:
        """Create persistent volume claim"""
        path = self._build_path(self.resource_type, namespace=namespace)
        pvc_data = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'accessModes': ['ReadWriteMany'],
                'resources': {
                    'requests': {
                        'storage': size
                    }
                },
                'storageClassName': storage_class,
                'volumeMode': 'Block'
            }
        }
        return self.client.post(path, data=pvc_data)

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get volume"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.get(path)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List volumes"""
        path = self._build_path(self.resource_type, namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete volume"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.delete(path)


class NetworkManager(ResourceManager):
    """Network resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'k8s.cni.cncf.io.network-attachment-definitions'

    def create(
        self,
        name: str,
        vlan_id: int,
        cluster_network: str,
        namespace: str = 'default'
    ) -> Tuple[int, Dict]:
        """Create VM network"""
        path = self._build_path(self.resource_type, namespace=namespace)
        network_data = {
            'apiVersion': 'k8s.cni.cncf.io/v1',
            'kind': 'NetworkAttachmentDefinition',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'config': json.dumps({
                    'cniVersion': '0.3.1',
                    'name': name,
                    'type': 'bridge',
                    'bridge': cluster_network,
                    'vlan': vlan_id
                })
            }
        }
        return self.client.post(path, data=network_data)

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get network"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.get(path)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List networks"""
        path = self._build_path(self.resource_type, namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete network"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.delete(path)


class HostManager(ResourceManager):
    """Host/Node resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'nodes'

    def get(self, name: str) -> Tuple[int, Dict]:
        """Get host/node"""
        path = f"/{self.api_version}/{self.resource_type}/{name}"
        return self.client.get(path)

    def list(self) -> Tuple[int, Dict]:
        """List all hosts/nodes"""
        path = f"/{self.api_version}/{self.resource_type}"
        return self.client.get(path)

    def update(self, name: str, data: Dict) -> Tuple[int, Dict]:
        """Update host/node"""
        path = f"/{self.api_version}/{self.resource_type}/{name}"
        return self.client.put(path, data=data)

    def cordon(self, name: str) -> Tuple[int, Dict]:
        """Cordon node"""
        code, node = self.get(name)
        if code == 200:
            node['spec']['unschedulable'] = True
            return self.update(name, node)
        return code, node

    def uncordon(self, name: str) -> Tuple[int, Dict]:
        """Uncordon node"""
        code, node = self.get(name)
        if code == 200:
            node['spec']['unschedulable'] = False
            return self.update(name, node)
        return code, node

    def drain(self, name: str) -> Tuple[int, Dict]:
        """Drain node"""
        # Implementation would involve cordoning and evicting pods
        return self.cordon(name)


class BackupManager(ResourceManager):
    """Backup resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'harvesterhci.io.virtualmachinebackups'

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get backup"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.get(path)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List backups"""
        path = self._build_path(self.resource_type, namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete backup"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.delete(path)


class SettingsManager(ResourceManager):
    """Settings resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'harvesterhci.io.settings'

    def get(self, name: str) -> Tuple[int, Dict]:
        """Get setting"""
        path = f"/{self.api_version}/{self.resource_type}/{name}"
        return self.client.get(path)

    def update(self, name: str, value: str) -> Tuple[int, Dict]:
        """Update setting"""
        code, setting = self.get(name)
        if code == 200:
            setting['value'] = value
            path = f"/{self.api_version}/{self.resource_type}/{name}"
            return self.client.put(path, data=setting)
        return code, setting


class KeypairManager(ResourceManager):
    """SSH Keypair resource manager"""

    def __init__(self, client: HarvesterAPIClient):
        super().__init__(client)
        self.resource_type = 'harvesterhci.io.keypairs'

    def create(self, name: str, public_key: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Create SSH keypair"""
        path = self._build_path(self.resource_type, namespace=namespace)
        keypair_data = {
            'apiVersion': 'harvesterhci.io/v1beta1',
            'kind': 'KeyPair',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'spec': {
                'publicKey': public_key
            }
        }
        return self.client.post(path, data=keypair_data)

    def get(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Get keypair"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.get(path)

    def list(self, namespace: str = 'default') -> Tuple[int, Dict]:
        """List keypairs"""
        path = self._build_path(self.resource_type, namespace=namespace)
        return self.client.get(path)

    def delete(self, name: str, namespace: str = 'default') -> Tuple[int, Dict]:
        """Delete keypair"""
        path = self._build_path(self.resource_type, name=name, namespace=namespace)
        return self.client.delete(path)


# Convenience function to create client
def create_harvester_api_client(
    endpoint: str,
    username: str = "admin",
    password: str = "password",
    verify_ssl: bool = False
) -> HarvesterAPIClient:
    """Create and return authenticated Harvester API client"""
    return HarvesterAPIClient(endpoint, username, password, verify_ssl)
