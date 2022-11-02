import SettingsPagePo from "@/pageobjects/settings.po";
import SidebarPage from "@/pageobjects/sidebar.po";

const settings = new SettingsPagePo();
const sidebar = new SidebarPage();

describe('Setting Page', () => {
    beforeEach(() => {
       cy.login();
       settings.goTo();
    })

    /**
     * https://harvester.github.io/tests/manual/advanced/chage-api-ui-source-bundled/
     * 1. Navigate to the Advanced Settings Page via URL
     * 2. Edit UI Source via UI
     * 3. Change the UISource Type
     * 4. Validate that the URL changed
     */
    it('change UI source type to Bundled, Check whether the configuration takes effect', () => {
        const address = `${Cypress.env('baseUrl')}/dashboard/_nuxt/**`;
        settings.checkIsCurrentPage();
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source')
        settings.checkUiSource('Bundled', address);
    });

    
    it('change UI source type to external, Check whether the configuration takes effect', () => {
        const address = 'https://releases.rancher.com/harvester-ui/dashboard/latest/**';
        settings.checkIsCurrentPage();
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source')
        settings.checkUiSource('External', address);
    });

    /**
     * https://harvester.github.io/tests/manual/advanced/change-log-level-debug/
     */
    it('change log level (Info)', () => {
        settings.checkIsCurrentPage();
        // setting value
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.changeLogLevel('log-level', 'Info');

        // Check whether the configuration is successful 
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.checkSettingValue('Value', 'Info');
    })

    it('change log level (Trace)', () => {
        settings.checkIsCurrentPage();
        // setting value
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.changeLogLevel('log-level', 'Trace');

        // Check whether the configuration is successful 
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.checkSettingValue('Value', 'Trace');
    })

    /**
     * backup target
     */
    it('Configure backup target (NFS)', () => {
        settings.checkIsCurrentPage();
        settings.clickMenu('backup-target', 'Edit Setting', 'backup-target');
        settings.setNFSBackupTarget('NFS', Cypress.env('nfsEndPoint'));
        settings.checkSettingValue('Type', 'NFS');
        settings.update('backup-target');
    })
})
