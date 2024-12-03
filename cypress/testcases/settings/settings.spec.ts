import { PageUrl } from "@/constants/constants";
import SettingsPagePo from "@/pageobjects/settings.po";

const settings = new SettingsPagePo();

describe('Setting Page', () => {
    beforeEach(() => {
        cy.login({ url: PageUrl.setting });
        settings.checkIsCurrentPage();
    })

    /**
     * https://harvester.github.io/tests/manual/advanced/chage-api-ui-source-bundled/
     * 1. Navigate to the Advanced Settings Page via URL
     * 2. Edit UI Source via UI
     * 3. Change the UISource Type
     * 4. Validate that the URL changed
     */
    it('change UI source type to Bundled, Check whether the configuration takes effect', () => {
        const address = `${Cypress.env('baseUrl')}/dashboard/js/**`;
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source', undefined, 'UI')
        settings.checkUiSource('Bundled', address);
    });


    it('change UI source type to external, Check whether the configuration takes effect', () => {
        const address = 'https://releases.rancher.com/harvester-ui/dashboard/**';
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source', undefined, 'UI')
        settings.checkUiSource('External', address);
    });

    /**
     * https://harvester.github.io/tests/manual/advanced/change-log-level-debug/
     */
    it('change log level (Info)', () => {
        // setting value
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.changeLogLevel('log-level', 'Info');

        // Check whether the configuration is successful 
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.checkSettingValue('Value', 'Info');
    })

    it('change log level (Trace)', () => {
        // setting value
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.changeLogLevel('log-level', 'Trace');

        // Check whether the configuration is successful 
        settings.clickMenu('log-level', 'Edit Setting', 'log-level')
        settings.checkSettingValue('Value', 'Trace');
    })
})

/**
 * https://harvester.github.io/tests/manual/advanced/set-s3-backup-target/
 */
describe('Set backup target S3', () => {
    beforeEach(() => {
        cy.login({ url: PageUrl.setting });
        settings.checkIsCurrentPage(false);
    })

    it('Set backup target S3', () => {
        settings.clickMenu('backup-target', 'Edit Setting', 'backup-target');

        const backupTarget = Cypress.env('backupTarget');
        settings.setS3BackupTarget({
            type: 'S3',
            endpoint: backupTarget.endpoint,
            bucketName: backupTarget.bucketName,
            bucketRegion: backupTarget.bucketRegion,
            accessKeyId: backupTarget.accessKey,
            secretAccessKey: backupTarget.secretKey,
        })

        settings.update('backup-target');
    });

    /**
     * backup target
     */
    it.skip('Configure backup target (NFS)', () => {
        settings.clickMenu('backup-target', 'Edit Setting', 'backup-target');
        settings.setNFSBackupTarget('NFS', Cypress.env('nfsEndPoint'));
        settings.checkSettingValue('Type', 'NFS');
        settings.update('backup-target');
    })
})
