export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 60000, uploadTimeout: 300000, downloadTimeout: 120000,   };
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public setupUrl = '/auth/setup/';
    public loginUrl = '/auth/login/';
    public dashboardUrl = '/harvester/c/local/harvesterhci.io.dashboard';
    public settingsUrl = '/harvester/c/local/harvesterhci.io.setting';
    public uiSourceUrl = '/harvester/c/local/harvesterhci.io.setting/ui-source?mode=edit';
    public hostsPage = '/harvester/c/local/harvesterhci.io.host';
    public supportPage = '/harvester/c/local/support';
    public vmPage = '/harvester/c/local/kubevirt.io.virtualmachine';
    public settingUrl = '/harvester/c/local/harvesterhci.io.setting';
    public volumePage = '/harvester/c/local/harvesterhci.io.volume';
    public imagePage = '/harvester/c/local/harvesterhci.io.virtualmachineimage';
}

export const PageUrl = {
    setting:          '/harvester/c/local/harvesterhci.io.setting',
    virtualMachine:   '/harvester/c/local/kubevirt.io.virtualmachine',
    vmNetwork:        '/harvester/c/local/harvesterhci.io.networkattachmentdefinition'
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
    monitoringConfiguration: ['Configuration', 'harvester/c/local/harvesterhci.io.managedchart/fleet-local/rancher-monitoring?mode=edit', 'rancher-monitoring', ['Monitoring & Logging', 'Monitoring'], false],
    alertmanagerConfig:      ['Alertmanager Configs', 'harvester/c/local/harvesterhci.io.monitoring.alertmanagerconfig', 'Alertmanager Configs', ['Monitoring & Logging', 'Monitoring']],
    loggingConfiguration:    ['Configuration', 'harvester/c/local/harvesterhci.io.managedchart/fleet-local/rancher-logging?mode=edit', 'rancher-logging', ['Monitoring & Logging', 'Logging'], false],
    clusterFlow:             ['Cluster Flow', 'harvester/c/local/harvesterhci.io.logging.clusterflow', 'Cluster Flows', ['Monitoring & Logging', 'Logging']],
    clusterOutput:           ['Cluster Output', 'harvester/c/local/harvesterhci.io.logging.clusteroutput', 'Cluster Outputs', ['Monitoring & Logging', 'Logging']],
    flow:                    ['Flow', 'harvester/c/local/harvesterhci.io.logging.flow', 'Flows', ['Monitoring & Logging', 'Logging']],
    Output:                  ['Output', 'harvester/c/local/harvesterhci.io.logging.output', 'Outputs', ['Monitoring & Logging', 'Logging']],
    Template:                ['Templates', 'harvester/c/local/harvesterhci.io.virtualmachinetemplateversion', 'Templates', ['Advanced']],
    sshKey:                  ['SSH Keys', 'harvester/c/local/harvesterhci.io.keypair', 'SSH Keys', ['Advanced']],
    cloudConfigTemplate:     ['Cloud Config Templates', 'harvester/c/local/harvesterhci.io.cloudtemplate', 'Cloud Config Templates', ['Advanced']],
    storageClass:            ['Storage Classes', 'harvester/c/local/harvesterhci.io.storage', 'Storage Classes', ['Advanced']],
    pciDevice:               ['PCI Devices', 'harvester/c/local/devices.harvesterhci.io.pcidevice', 'PCI Devices (Experimental)', ['Advanced']],
    addon:                   ['Addons', 'harvester/c/local/harvesterhci.io.addon', 'Addons', ['Advanced']],
    setting:                 ['Settings', 'harvester/c/local/harvesterhci.io.setting', 'Settings', ['Advanced']]
}