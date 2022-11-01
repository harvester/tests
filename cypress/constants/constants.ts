const isDev = Cypress.env('NODE_ENV') === 'dev';
export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 60000, uploadTimeout: 300000, downloadTimeout: 120000  };
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
    public settingBaseUrl = '/harvester/c/local/harvesterhci.io.setting';
    public volumePage = '/harvester/c/local/harvesterhci.io.volume';
    public imagePage = '/harvester/c/local/harvesterhci.io.virtualmachineimage';
}
