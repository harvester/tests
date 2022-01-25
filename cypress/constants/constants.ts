export class Constants {
    public timeout = { timeout: 10000 };
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public baseUrl = Cypress.env("baseUrl");
    public setupUrl = this.baseUrl + 'auth/setup/';
    public loginUrl = this.baseUrl + 'dashboard/auth/login/';
    public dashboardUrl = this.baseUrl + 'dashboard/c/local/harvester/harvesterhci.io.dashboard';
    public settingsUrl = this.baseUrl + 'dashboard/c/local/harvester/harvesterhci.io.setting';
    public uiSourceUrl = this.baseUrl + 'dashboard/c/local/harvester/harvesterhci.io.setting/ui-source?mode=edit'
    public hostsPage = this.baseUrl + 'dashboard/c/local/harvester/harvesterhci.io.host';
    public supportPage = this.baseUrl + 'dashboard/c/local/harvester/support'
}