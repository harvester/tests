const isDev = Cypress.env('NODE_ENV') === 'dev';
export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 60000, uploadTimeout: 300000 };
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public setupUrl = '/auth/setup/';
    public loginUrl = '/auth/login/';
    public dashboardUrl = '/c/local/harvester/harvesterhci.io.dashboard';
    public settingsUrl = '/c/local/harvester/harvesterhci.io.setting';
    public uiSourceUrl = '/c/local/harvester/harvesterhci.io.setting/ui-source?mode=edit';
    public hostsPage = '/c/local/harvester/harvesterhci.io.host';
    public supportPage = '/c/local/harvester/support';
    public vmPage = '/c/local/harvester/kubevirt.io.virtualmachine';
    public settingBaseUrl = '/c/local/harvester/harvesterhci.io.setting';
    public volumePage = '/c/local/harvester/harvesterhci.io.volume';
    public imagePage = '/c/local/harvester/harvesterhci.io.virtualmachineimage';
}
