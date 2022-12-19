# Introduction

This is the Ansible to stand up a Jenkins Node that will use harvester-installer to create the artifacts for Harvester, for a pipeline in Jenkins that is capable of running AirGap Harvester & AirGap Rancher provisioning over Vagrant that leverages ipxe-examples (airgap version).

# Setup New Jenkins

To setup [Jenkins] on a target host.

1. Make sure [Ansible] is installed. You can install the latest version
   of [Ansible] using [Python PIP].
2. Copy `settings.yml.sample` to `settings.yml`.
3. Edit `settings.yml` by providing the required configurations. The
   configurations are self-documented.
4. Edit `inventory.harvester-ci` to make sure the host IP and Ansible user are
   correct. **NOTE:** the Ansible user must have SSH access to the CI host and
   have sudo permissions.
5. Run the `install_jenkins.ym` playbook. For example:

```console
ansible-playbook -i inventor.harvester-ci --private-key <ansible user private key> install_jenkins.yml
```

# Add a Jenkins Slave

To add a Jenkins Slave.

1. Make sure [Ansible] is installed. You can install the latest version
   of [Ansible] using [Python PIP].
2. Copy `settings.yml.sample` to `settings.yml`.
3. Edit `settings.yml` by providing the required configurations. The
   configurations are self-documented.
4. Edit `inventory.harvester-ci` to make sure the host IP and Ansible user are
   correct. **NOTE:** the Ansible user must have SSH access to the CI host and
   have sudo permissions.
5. Install the required packages on the Jenkins Slave host by running the
   `install_jenkins_slave.yml` playbook. For example:

```console
ansible-playbook -i inventory.harvester-ci --private-key <ansible user private key> install_jenkins_slave.yml
```

6. Manually add the new node from Jenkins Master.

[Ansible]: https://www.ansible.com/
[Jenkins]: https://www.jenkins.io/
[Python PIP]: https://pip.pypa.io/en/stable/
