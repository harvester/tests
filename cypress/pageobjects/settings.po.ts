import { Constants } from '@/constants/constants'
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import CruResource from '@/utils/components/cru-resource.po';
import { HCI } from '@/constants/types'
const constants = new Constants();

interface OvercommitInterface {
  cpu?: string,
  memory?: string,
  storage?: string,
}

interface BackupTargetInterface {
    type?: string, 
    endpoint: string, 
    bucketName: string,
    bucketRegion: string,
    accessKeyId: string,
    secretAccessKey: string
}

export default class SettingsPagePo extends CruResource {
    private detailPageHead = 'main .outlet header h1 a';

    constructor() {
       super({ type: HCI.SETTING })
    }

    /**
     * Go to the setting edit page. Then it checks the URL
     */
    clickMenu(name: string, actionText: string, urlSuffix: string, type?: string) {
        const editPageUrl = type ? `/harvester/c/local/${type}` : constants.settingsUrl;

        cy.get(`.advanced-setting #${name} button`).click()
  
        cy.get('span').contains(actionText).click();
        
        cy.get(this.detailPageHead).then(() => {
            cy.url().should('eq', `${this.basePath()}${editPageUrl}/${urlSuffix}?mode=edit`)
        })
    }

    changeLogLevel(id: string, value: string) {
        new LabeledSelectPo('.labeled-select', `:contains("Value")`).select({option: value})

        this.update(id);
    }

    checkSettingValue(title: string, value: string) {
        const select = new LabeledSelectPo('.labeled-select', `:contains(${title})`)
        cy.wrap(select).then(() => {
            select.text().should(($text) => {
                expect($text.trim()).to.equal(value)
            })
        })
    }

    checkUiSource(type: string, address: string) {
        new LabeledSelectPo('section .labeled-select.hoverable', `:contains("Value")`).select({option: type})
        this.update('ui-source');
        this.checkIsCurrentPage();
        cy.reload();

        cy.intercept('GET', address).as('fetch');
        cy.wait('@fetch', { timeout: constants.timeout.maxTimeout}).then(res => {
            cy.log(`Check Passed ui-source (${type})`)
        });
    }

    setOvercommit(value: OvercommitInterface) {
      const cpu = new LabeledInputPo('.labeled-input', `:contains("CPU")`)

      cpu.input(value.cpu)
    }

    setNFSBackupTarget(type: string, endpoint: string) {
        const select = new LabeledSelectPo("section .labeled-select.hoverable", `:contains("Type")`);
        select.select({option: type, selector: '.vs__dropdown-menu'});
        new LabeledInputPo('.labeled-input', `:contains("Endpoint")`).input(endpoint);
    }

    setS3BackupTarget(value: BackupTargetInterface) {
        const type = new LabeledSelectPo(".labeled-select.hoverable", `:contains("Type")`);
        const endpoint = new LabeledInputPo('.labeled-input', `:contains("Endpoint")`);
        const bucketName = new LabeledInputPo('.labeled-input', `:contains("Bucket Name")`);
        const bucketRegion = new LabeledInputPo('.labeled-input', `:contains("Bucket Region")`);
        const accessKeyId = new LabeledInputPo('.labeled-input', `:contains("Access Key ID")`);
        const secretAccessKey = new LabeledInputPo('.labeled-input', `:contains("Secret Access Key")`);

        type.select(value.type || 'S3');
        endpoint.input(value.endpoint);
        bucketName.input(value.bucketName);
        bucketRegion.input(value.bucketRegion);
        accessKeyId.input(value.accessKeyId);
        secretAccessKey.input(value.secretAccessKey);
    }
}
