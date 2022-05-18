import { LoginPage } from "@/pageobjects/login.po";
import { SupportPage } from "@/pageobjects/support.po";
const login = new LoginPage();
const support = new SupportPage();

/**
 * 1. Login
 * 2. Navigate to the support page
 * 3. Validate the URL
 */
export function checkSupportPage() {}
describe('Support Page', () => {
    it('Check suport page', () => {
        cy.login();
        support.visitSupportPage();
    });
});

/**
 * 1. Login
 * 2. Navigate to the support page
 * 3. Click Generate Support Bundle
 * 4. Input Description
 * 5. Click Generate
 * 6. Wait for download
 * 7. Verify Downlaod
 * @notImplementedFully
 */
export function generateSupportBundle() {}
describe('Generate Support Bundle', () => {
    it('Generate Support Bundle', () => {
        cy.login();
        support.generateSupportBundle('this ia a test description');
    });
});
