import { Constants } from '../../constants/constants'
const constants = new Constants();

export class SidebarPage {
    private advancedSettingsAccordion = '.accordion';
    private settings = 'Settings';


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