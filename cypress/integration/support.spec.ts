import { LoginPage } from "../pageobjects/login.po";
import { SupportPage } from "../pageobjects/support.po";
const login = new LoginPage();
const support = new SupportPage();


describe('Support Page', () => {
    // it('Check suport page', () => {
    //     login.login();
    //     support.visitSupportPage();
    // });
    
    it('Generate Support Bundle', () => {
        login.login();
        support.generateSupportBundle('this ia a test description');
    });
});
