const isDev = Cypress.env('NODE_ENV') === 'dev';
export class Constants {
    public timeout = { timeout: 10000, maxTimeout: 30000, uploadTimeout: 300000 };
    public username = Cypress.env("username");
    public password = Cypress.env("password");
    public setupUrl = addUrlPrefix('/auth/setup/');
    public loginUrl = addUrlPrefix('/auth/login/');
    public dashboardUrl = addUrlPrefix('/c/local/harvester/harvesterhci.io.dashboard');
    public settingsUrl = addUrlPrefix('/c/local/harvester/harvesterhci.io.setting');
    public uiSourceUrl = addUrlPrefix('/c/local/harvester/harvesterhci.io.setting/ui-source?mode=edit');
    public hostsPage = addUrlPrefix('/c/local/harvester/harvesterhci.io.host');
    public supportPage = addUrlPrefix('/c/local/harvester/support');
    public vmPage = addUrlPrefix('/c/local/harvester/kubevirt.io.virtualmachine');
    public settingBaseUrl = addUrlPrefix('/c/local/harvester/harvesterhci.io.setting');
    public volumePage = addUrlPrefix('/c/local/harvester/harvesterhci.io.volume');
    public imagePage = addUrlPrefix('/c/local/harvester/harvesterhci.io.virtualmachineimage');
}

function addUrlPrefix(url: string) {
    return isDev ? url : `/dashboard${url}`;
}
