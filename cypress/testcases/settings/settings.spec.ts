import { PageUrl } from "@/constants/constants";
import SettingsPagePo from "@/pageobjects/settings.po";

const settings = new SettingsPagePo();

describe('Setting Page', () => {
    beforeEach(() => {
       cy.login({url: PageUrl.setting});
       settings.checkIsCurrentPage();
    })

    /**
     * https://harvester.github.io/tests/manual/advanced/chage-api-ui-source-bundled/
     * 1. Navigate to the Advanced Settings Page via URL
     * 2. Edit UI Source via UI
     * 3. Change the UISource Type
     * 4. Validate that the URL changed
     */
    it.skip('change UI source type to Bundled, Check whether the configuration takes effect', () => {
        const address = `${Cypress.env('baseUrl')}/dashboard/_nuxt/**`;
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source')
        settings.checkUiSource('Bundled', address);
    });

    
    it.skip('change UI source type to external, Check whether the configuration takes effect', () => {
        const address = 'https://releases.rancher.com/harvester-ui/dashboard/latest/**';
        settings.clickMenu('ui-source', 'Edit Setting', 'ui-source')
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

/**
 * https://harvester.github.io/tests/manual/advanced/set-s3-backup-target/
 */
describe('Set backup target S3', () => {
    it.skip('Set backup target S3', () => {
        cy.login();
        settings.goToList();
        settings.clickMenu('backup-target', 'Edit Setting', 'backup-target');
        settings.setS3BackupTarget({
            type: 'S3', 
            endpoint: 'https://minio-service.default:9000', 
            bucketName: 'backupbucket',
            bucketRegion: 'us-east-1',
            accessKeyId: 'longhorn-test-access-key',
            secretAccessKey: 'longhorn-test-secret-key'
        })
        settings.update('backup-target');
    });
})
