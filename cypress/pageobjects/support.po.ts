import type { CypressChainable } from '@/utils/po.types'
import { Constants } from '@/constants/constants'
import { validateZip, deleteDownloadsFolder } from '@/utils/utils'
import Dashboard from "@/pageobjects/dashboard.po";

const constants = new Constants();

export class SupportPage {
    private supportBundleButton = 'Generate Support Bundle';
    private supportBundleInput = 'textarea'
    private generateButton = '[type="submit"]';

    public get docsBtn(): CypressChainable {
        return cy.get("main .community .support-link a").contains("Docs")
    }

    public get forumsBtn(): CypressChainable {
        return cy.get("main .community .support-link a").contains("Forums")
    }

    public get slackBtn(): CypressChainable {
        return cy.get("main .community .support-link a").contains("Slack")
    }

    public get fileAnIssueBtn(): CypressChainable {
        return cy.get("main .community .support-link a").contains("File an Issue")
    }

    public get downloadKubeConfigBtn(): CypressChainable {
        return cy.get("main button").contains("Download KubeConfig")
    }

    public visit() {
        cy.url().then(url => {
            if(!url.includes(constants.dashboardUrl)) {
                cy.login();
            }
            Dashboard.nav.SupportLink.click()
            cy.get("main h1").should("contain","Harvester Support")
            cy.url().should("contain", constants.supportPage)
        })
    }

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
        // cy.wait('@supportBundle', { timeout: 120000 }).then((res) => {
        //     // grab filename from 'content-disposition' header
        //     const filename = res.response.headers['content-disposition'].split('filename=')[1];
        //     cy.task('validateZip', filename);
        // });

    }

    private checkSupportBundle() {
        this.visitSupportPage();

    }
    
    private validateSupportPage() {
        cy.url().should('contain', constants.supportPage);
    }

}