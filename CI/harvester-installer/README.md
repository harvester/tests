# Introduction

This [Ansible] playbook automatically sets up harvester-installer CI [Jenkins].
Currently it only supports either openSUSE or Ubuntu.

# Prerequisites
- `ansible-galaxy collection install community.crypto`

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


## Troubleshooting:
- if there are issues, with Jenkins configuration, with the most recent versions of Jenkins (since the shift to systemd based configs for Jenkins), you'll need to be on the node and audit Jenkins with:
`journalctl -u jenkins.service` 
