import { Constants } from '../../constants/constants'
const constants = new Constants();

export class SettingsPage {
    private uiSourceButton = '#ui-source';
    private editSettingsButton = '.icon-edit';
    private settingsDropdown = '#vs4-combobox';
    private uiSourceAuto = '#vs4__option-0';
    private uiSourceExternal = '#vs4__option-1';
    private uiSourceBundled = '#vs4__option-2';

    /**
     * Visits the Advanced Settings page and checks URL
     */
    public visitSettings() {
        cy.visit(constants.settingsUrl).then(() => {
            expect(cy.url().should('eq', constants.settingsUrl));
        });
    }
    
    /**
     * visits advanced settings page and opens the edit ui source page. Then it checks the URL
     */
    public editUiSource() {
        cy.visit(constants.settingsUrl);
        expect(cy.url().should('eq', constants.settingsUrl) );
        cy.get(this.uiSourceButton).click();
        cy.get(this.editSettingsButton).click();;
        expect(cy.url().should('eq', constants.uiSourceUrl) );
    }
    /**
         * @param type this is the type of ui source type
         * @value 0 This is Auto
         * @value 1 This is External
         * @value 2 This is Bundled
     */
    public changeUiSourceType(type: number) {
        this.editUiSource();
        cy.get(this.settingsDropdown).scrollTo('center').click();
         try {
             if (type > 2 || type < 0) throw 'uiSource type is not valid';
             switch (type) {
                 case 0:
                     cy.get(this.uiSourceAuto).click();
                     break;
                 case 1:
                     cy.get(this.uiSourceExternal).click();
                     break;
                 case 0:
                     cy.get(this.uiSourceBundled).click();
                     break;
      
                 default:
                     break;
             }    
         } catch (error) {
             console.error(error);
         }
    }

}