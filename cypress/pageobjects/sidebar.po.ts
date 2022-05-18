import { HCI } from '@/constants/types'

import { Constants } from '@/constants/constants';
const constants = new Constants();

export default class SidebarPage {
    private advancedSettingsAccordion = '.accordion';
    private settings = 'Settings';

    /**
     * This navigates to the advanced settings page via the UI in the sidebar
     */
    public advancedSettings() {
        cy.get(this.advancedSettingsAccordion, {  timeout: constants.timeout.maxTimeout })
        .each(($elem, index) => {
          if (index === 1) {
            cy.wrap($elem).click();
          }
        });
        cy.contains(this.settings).click();
        cy.location().then((location) => {
          expect(location.pathname).to.eq(`${constants.settingsUrl}`)
        })
    }
}