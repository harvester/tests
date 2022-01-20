import { Constants } from '../../constants/constants'
const constants = new Constants();

export class LoginPage {
    private usernameInput = '#username';
    private passwordInput = '#password';
    private submitButton = '#submit';
    private checkboxEula = '#checkbox-eula'
    private checkboxTelemetry = '#checkbox-telemetry';
    private allRadios = 'input[type="radio"]';
 
    public login() {
        cy.visit(constants.loginUrl);
        cy.get(this.usernameInput).type(constants.username);
        cy.get(this.passwordInput).type(constants.password)
        cy.get(this.submitButton).click();
    }

    public validateLogin() {
        /**
        // Parameters may be declared in a variety of syntactic forms
         */
        expect(cy.url().should('eq', constants.dashboardUrl) );
    }
    public firstLogin() {
        cy.visit(constants.baseUrl).visit(constants.setupUrl);
        cy.location('pathname', {timeout: 20000}).should('include', constants.baseUrl);        expect(cy.url().should('eq', constants.loginUrl));
        this.checkTerms(false);
        cy.get(this.checkboxEula).check();
        cy.get(this.checkboxTelemetry);
        cy.get(this.allRadios)
        .each(($elem, index) => {
          if (index === 1) {
            cy.wrap($elem).click();
          }
        });
        // This enters the password into both of the password fields
        cy.get('[type=Password]')
        .each(($elem, index) => {
            cy.wrap($elem).type(constants.password);
        });
        cy.get(this.submitButton).click();
    }
    private checkTerms(eula: boolean) {
        /**
         * @param eula Boolean for whether or not eula is checked
         */
        cy.visit(constants.loginUrl);
        if (eula == false) {
            expect(cy.get('#submit').should('be.disabled'));
        }
        if (eula == true) {
            expect(cy.get('#submit').should('be.enabled'));
        }
        
    }
}
