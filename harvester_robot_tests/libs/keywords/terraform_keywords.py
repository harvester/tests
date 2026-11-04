""" Terraform Keyword Wrapper

Layer 3: Keyword wrapper (NO direct API calls)
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from terraform import Terraform  # noqa E402
from utility.utility import logging  # noqa E402


class terraform_keywords:
    """Terraform keyword wrapper - creates Terraform component and delegates"""

    # The component keeps the workspaces of the suite, so the suite teardown
    # must reach the instance the test cases used
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.terraform = Terraform()

    def init_workspace(self, workspace):
        logging(f'Initializing terraform workspace {workspace}')
        self.terraform.init_workspace(workspace)

    def add_virtual_machine(self, workspace, vm_name, image_id, namespace,
                            cpu, memory, disk_size):
        logging(f'Defining VM {vm_name} in terraform workspace {workspace}')
        self.terraform.add_virtual_machine(workspace, vm_name, image_id, namespace,
                                           cpu, memory, disk_size)

    def set_required_node_affinity(self, workspace, vm_name, key, value):
        logging(f'Requiring node label {key}={value} for VM {vm_name}')
        self.terraform.set_required_node_affinity(workspace, vm_name, key, value)

    def set_required_pod_anti_affinity(self, workspace, vm_name, *other_vm_names):
        logging(f'Keeping VM {vm_name} away from {", ".join(other_vm_names)}')
        self.terraform.set_required_pod_anti_affinity(workspace, vm_name, other_vm_names)

    def apply(self, workspace):
        self.terraform.apply(workspace)

    def plan_has_changes(self, workspace):
        return self.terraform.plan_has_changes(workspace)

    def destroy(self, workspace):
        logging(f'Destroying terraform workspace {workspace}')
        self.terraform.destroy(workspace)
