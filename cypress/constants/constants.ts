export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 60000, uploadTimeout: 600000, downloadTimeout: 120000, provisionTimeout: 1500000};
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public mockPassword = Cypress.env("mockPassword");
    public rancherUrl = Cypress.env("rancherUrl");
    public rancher_user = Cypress.env("rancherUser");
    public rancher_password = Cypress.env("rancherPassword");
    public rancher_vm_user = Cypress.env("rancher_vm_user");
    public rancher_vm_password = Cypress.env("rancher_vm_password");
    public vagrant_pxe_path = Cypress.env("vagrant_pxe_path");
    public setupUrl = '/auth/setup/';
    public loginUrl = '/auth/login/';
    public accountUrl = '/account'
    public dashboardUrl = '/harvester/c/local/harvesterhci.io.dashboard';
    public settingsUrl = '/harvester/c/local/harvesterhci.io.setting';
    public uiSourceUrl = '/harvester/c/local/harvesterhci.io.setting/ui-source?mode=edit';
    public hostsPage = '/harvester/c/local/harvesterhci.io.host';
    public supportPage = '/harvester/c/local/support';
    public vmPage = '/harvester/c/local/kubevirt.io.virtualmachine';
    public settingUrl = '/harvester/c/local/harvesterhci.io.setting';
    public volumePage = '/harvester/c/local/harvesterhci.io.volume';
    public imagePage = '/harvester/c/local/harvesterhci.io.virtualmachineimage';
    public virtualManagePage = '/c/local/harvesterManager/harvesterhci.io.management.cluster';
    public rancher_loginPage = '/dashboard/auth/login';
    public rancher_dashboardPage = 'dashboard/home';
    public rancher_settingPage = '/dashboard/c/local/settings/management.cattle.io.setting';
    public rancher_virtualizationManagement = '/c/local/harvesterManager/harvesterhci.io.management.cluster';
    public rancher_clusterManagmentPage = '/c/local/manager/provisioning.cattle.io.cluster';
    public rancher_cloudCredentialPage = '/c/local/manager/cloudCredential';
    public rancher_nodeTamplatePage = '/c/local/manager/pages/node-templates';
}

export const PageUrl = {
    setting:          '/harvester/c/local/harvesterhci.io.setting',
    virtualMachine:   '/harvester/c/local/kubevirt.io.virtualmachine',
    vmNetwork:        '/harvester/c/local/harvesterhci.io.networkattachmentdefinition',
    namespace:        '/harvester/c/local/namespace',
    volumeSnapshot:   '/harvester/c/local/harvesterhci.io.volumesnapshot'
}

export const MenuNav = {
    dashboard:      ['Dashboard', 'harvester/c/local/harvesterhci.io.dashboard', 'Harvester Cluster: local'],
    Host:           ['Hosts', 'harvester/c/local/harvesterhci.io.host', 'Hosts'],
    virtaulmachine: ['Virtual Machines', 'harvester/c/local/kubevirt.io.virtualmachine', 'Virtual Machines'],
    volume:         ['Volumes', 'harvester/c/local/harvesterhci.io.volume', 'Volumes'],
    Images:         ['Images', 'harvester/c/local/harvesterhci.io.virtualmachineimage', 'Images'],
    namespace:      ['Namespaces', 'harvester/c/local/namespace', 'Namespaces'],
    clusterNetwork: ['Cluster Networks/Configs', 'harvester/c/local/network.harvesterhci.io.clusternetwork', 'Cluster Networks/Configs', ['Networks']],
    vmNetwork:      ['VM Networks', 'harvester/c/local/harvesterhci.io.networkattachmentdefinition', 'VM Networks', ['Networks']],
    vmBackup:       ['VM Backups', 'harvester/c/local/harvesterhci.io.virtualmachinebackup', 'VM Backups', ['Backup & Snapshot']],
    vmSnapshot:     ['VM Snapshots', 'harvester/c/local/harvesterhci.io.vmsnapshot', 'VM Snapshots', ['Backup & Snapshot']],
    volumeSnapshot: ['Volume Snapshots', 'harvester/c/local/harvesterhci.io.volumesnapshot', 'Volume Snapshots', ['Backup & Snapshot']],
    alertmanagerConfig:      ['Alertmanager Configs', 'harvester/c/local/harvesterhci.io.monitoring.alertmanagerconfig', 'Alertmanager Configs', ['Monitoring & Logging', 'Monitoring']],
    clusterFlow:             ['Cluster Flow', 'harvester/c/local/harvesterhci.io.logging.clusterflow', 'Cluster Flows', ['Monitoring & Logging', 'Logging']],
    clusterOutput:           ['Cluster Output', 'harvester/c/local/harvesterhci.io.logging.clusteroutput', 'Cluster Outputs', ['Monitoring & Logging', 'Logging']],
    flow:                    ['Flow', 'harvester/c/local/harvesterhci.io.logging.flow', 'Flows', ['Monitoring & Logging', 'Logging']],
    Output:                  ['Output', 'harvester/c/local/harvesterhci.io.logging.output', 'Outputs', ['Monitoring & Logging', 'Logging']],
    Template:                ['Templates', 'harvester/c/local/harvesterhci.io.virtualmachinetemplateversion', 'Templates', ['Advanced']],
    sshKey:                  ['SSH Keys', 'harvester/c/local/harvesterhci.io.keypair', 'SSH Keys', ['Advanced']],
    cloudConfigTemplate:     ['Cloud Config Templates', 'harvester/c/local/harvesterhci.io.cloudtemplate', 'Cloud Config Templates', ['Advanced']],
    storageClass:            ['Storage Classes', 'harvester/c/local/harvesterhci.io.storage', 'Storage Classes', ['Advanced']],
    pciDevice:               ['PCI Devices', 'harvester/c/local/devices.harvesterhci.io.pcidevice', 'PCI Devices', ['Advanced']],
    addon:                   ['Addons', 'harvester/c/local/harvesterhci.io.addon', 'Addons', ['Advanced']],
    secrets:                 ['Secrets', 'harvester/c/local/harvesterhci.io.secret', 'Secrets', ['Advanced']],
    setting:                 ['Settings', 'harvester/c/local/harvesterhci.io.setting', 'Settings', ['Advanced']]
}