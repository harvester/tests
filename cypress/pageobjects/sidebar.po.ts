import { Constants } from '../constants/constants'
const constants = new Constants();

export class SidebarPage {
    private advancedSettingsAccordion = '.accordion';
    private settings = 'Settings';

    /**
     * This navigates to the advanced settings page via the UI in the sidebar
     */
    public advancedSettings() {
        cy.get(this.advancedSettingsAccordion)
        .each(($elem, index) => {
          if (index === 1) {
            cy.wrap($elem).click();
          }
        });
        cy.contains(this.settings).click();
        expect(cy.url().should('eq', constants.settingsUrl));
    }

}