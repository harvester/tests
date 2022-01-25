import { Constants } from '../constants/constants'
import { validateZip, deleteDownloadsFolder } from '../utils/utils'
const constants = new Constants();

export class SupportPage {
    private supportBundleButton = 'Generate Support Bundle';
    private supportBundleInput = 'textarea'
    private generateButton = '[type="submit"]';

    public visitSupportPage() {
        cy.visit(constants.supportPage).then(() => {
            cy.url().should('contain', constants.supportPage);
        });
        // this.validateSupportPage();
    }
    
    public generateSupportBundle(description: string) {
        // cy.task('deleteDownloadsFolder');
        this.visitSupportPage();
        cy.get('.btn').contains(this.supportBundleButton).click();
        cy.get(this.supportBundleInput).each(($elem, index) => {
            if(index == 1) {
                cy.wrap($elem).type(description)
            }
        });
        cy.intercept('file').as('supportBundle');
        cy.get(this.generateButton).click();
        cy.wait('@supportBundle', { timeout: 120000 }).then((res) => {
            // grab filename from 'content-disposition' header
            const filename = res.response.headers['content-disposition'].split('filename=')[1];
            cy.task('validateZip', filename);
        });

    }

    private checkSupportBundle() {
        this.visitSupportPage();

    }
    
    private validateSupportPage() {
        cy.url().should('contain', constants.supportPage);
    }

}