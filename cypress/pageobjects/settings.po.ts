import { Constants } from '@/constants/constants'
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import RadioButtonPo from '@/utils/components/radio-button.po'
import CruResource from '@/utils/components/cru-resource.po';
import { HCI } from '@/constants/types'
const constants = new Constants();

interface OvercommitInterface {
  cpu?: string,
  memory?: string,
  storage?: string,
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
}
