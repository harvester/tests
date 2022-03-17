export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 30000 };
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public baseUrl = Cypress.env("baseUrl");
    public setupUrl = this.baseUrl + 'auth/setup/';
    public loginUrl = this.baseUrl + '/auth/login/';
    public dashboardUrl = this.baseUrl + '/c/local/harvester/harvesterhci.io.dashboard';
    public settingsUrl = this.baseUrl + '/c/local/harvester/harvesterhci.io.setting';
    public uiSourceUrl = this.baseUrl + '/c/local/harvester/harvesterhci.io.setting/ui-source?mode=edit'
    public hostsPage = this.baseUrl + '/c/local/harvester/harvesterhci.io.host';
    public supportPage = this.baseUrl + '/c/local/harvester/support'
    public vmPage = this.baseUrl + '/c/local/harvester/kubevirt.io.virtualmachine'
    public settingBaseUrl = this.baseUrl + '/c/local/harvester/harvesterhci.io.setting'
}
