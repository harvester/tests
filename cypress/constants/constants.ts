export class Constants {
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public baseUrl = Cypress.env("baseUrl");
    public setupUrl = this.baseUrl + 'auth/setup/';
    public loginUrl = this.baseUrl + 'dashboard/auth/login/';
    public dashboardUrl = this.baseUrl + 'c/local/harvester/harvesterhci.io.dashboard#vm';
    public settingsUrl = this.baseUrl + 'c/local/harvester/harvesterhci.io.setting';
    public uiSourceUrl = this.baseUrl + 'c/local/harvester/harvesterhci.io.setting/ui-source?mode=edit'
}