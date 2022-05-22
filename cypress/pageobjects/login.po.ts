import { Constants } from '../constants/constants'
const constants = new Constants();

export class LoginPage {
    private usernameInput = '#username';
    private passwordInput = '#password';
    private submitButton = '#submit';
    private checkboxEula = '#checkbox-eula'
    private checkboxTelemetry = '#checkbox-telemetry';
    private allRadios = '.radio-container';
    private checkbox = '.checkbox-custom';
    private mainPageHeader = 'main .outlet header h1 span'

    public username: string;
    public password: string;

    /**
    * To check whether the Harvester is first time to login.
    * @returns the boolean value to identify is first time login or not.
    */
    public static isFirstTimeLogin(): Promise<boolean> {
        return new Promise((resolve, reject) => {
            cy.intercept('GET', '/v1/management.cattle.io.setting').as('getFirstLogin')
              .visit("/")
              .wait('@getFirstLogin').then(login => {
                const data: any[] = login.response?.body.data;
                const firstLogin = data.find(v => v?.id === "first-login");
                resolve(firstLogin.value === 'true');
               })
              .end();
        });
    }

    constructor(username:string = constants.username, passwd: string = constants.password) {
        this.username = username;
        this.password = passwd;
    }

    public get submitBtn():CypressChainable {
        return cy.get(`${this.submitButton} >button`)
    }

    /**
     * This visits the login page and logs in
     */
    public login() {
        cy.visit(constants.loginUrl);
        cy.get(this.usernameInput).type(this.username);
        cy.get(this.passwordInput).type(this.password)
        cy.get(this.submitButton).click()
        
        cy.get(this.mainPageHeader, { timeout: constants.timeout.maxTimeout }).then($el => {
            this.validateLogin()
        })
    }
    /**
    * Parameters may be declared in a variety of syntactic forms
    */
    private validateLogin() {
        cy.url().should('contain', constants.dashboardUrl);
    }

    public visit() {
        cy.visit("/");
        return this
    }

    public selectRandomPassword() {
        cy.get(`form ${this.allRadios}`).eq(0).click();
        return this
    }

    public selectSpecificPassword() {
        cy.get(`form ${this.allRadios}`).eq(1).click();
        return this
    }

    public checkEula(checked:boolean = true) {
        cy.get(`${this.checkboxEula} ${this.checkbox}`).then($el => {
            if(!!$el.attr("aria-checked") === checked) {
                cy.get(this.checkboxEula)
            } else {
                cy.get(this.checkboxEula).click("left")
            }
        })
        return this
    }

    public checkTelemetry(checked:boolean = true) {
        cy.get(`${this.checkboxTelemetry} ${this.checkbox}`).then($el => {
            if (!!$el.attr("aria-checked") === checked) {
                cy.get(this.checkboxTelemetry)
            } else {
                cy.get(this.checkboxTelemetry).click("left")
            }
        })
        return this
    }

    public inputPassword(first:string = this.password, second:string = this.password) {
        const passwds = [first, second];
        cy.get("[type=Password]").each(($el, idx) => cy.wrap($el).type(passwds[idx]))
        return this
    }

    /**
     * Method for logging in first time. Sets password to not be random, accepts terms, 
     * and disables telemetry
     */
    public firstLogin() {
        // cy.url().should('include', constants.baseUrl);
        // expect(cy.url().should('eq', constants.loginUrl));
        // this.checkTerms(false);
        cy.intercept('GET', '/v1/management.cattle.io.setting').as('getFirstLogin');
        cy.visit('/');

        cy.wait('@getFirstLogin').then((login) => {
            const data: any[] = login.response?.body.data;
            const firstLogin = data.find(value => value?.id === 'first-login');
            if (firstLogin.value === 'true') {
                cy.get(this.checkboxEula).click('left')
                cy.get(this.checkboxTelemetry).click('left');
                cy.get(this.allRadios)
                .each(($elem, index) => {
                    if (index === 1) {
                        cy.wrap($elem).click('left');
                    }
                });
                // This enters the password into both of the password fields
                cy.get('[type=Password]')
                .each(($elem) => {
                    cy.wrap($elem).type(constants.password);
                });
                cy.get(this.submitButton).click();
                cy.get(this.mainPageHeader, { timeout: constants.timeout.maxTimeout }).then($el => {
                    this.validateLogin()
                })
            } else {
                cy.log('Not the first time login');
            }
        });
    }
    /**
     * Checks whether or not eula is checked and the submit button
     * @param eula Boolean for whether or not eula is checked
     */
    private checkTerms(eula: boolean) {
        cy.visit(constants.loginUrl);
        if (eula == false) {
            expect(cy.get('#submit').should('be.disabled'));
        }
        if (eula == true) {
            expect(cy.get('#submit').should('be.enabled'));
        }
    }
}
