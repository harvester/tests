import { Constants } from '@/constants/constants'
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import CruResource from '@/utils/components/cru-resource.po';
import { HCI } from '@/constants/types'
const constants = new Constants();

export default class SettingsPagePo extends CruResource {
    private detailPageHead = 'main .outlet header h1 a';

    constructor() {
       super({ type: HCI.CLUSTER_NETWORK })
    }

    /**
     * Go to the setting edit page. Then it checks the URL
     */
    public clickMenu(name: string, actionText: string, urlSuffix: string, type: string) {
        const editPageUrl = type || constants.settingsUrl;
        cy.get(`.advanced-setting #${name} button`).click()
  
        cy.get('span').contains(actionText).click();
        
        cy.get(this.detailPageHead).then(() => {
            cy.url().should('eq', `${this.basePath()}${editPageUrl}/${urlSuffix}?mode=edit`)
        })
    }
}
