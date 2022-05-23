import { LoginPage } from "@/pageobjects/login.po";
import Dashboard from "@/pageobjects/dashboard.po";
/**
 * This is the login spec
 * 1. Login for first time
 * 2. Login with already set password
 */
describe('login page for harvester', () => {
    it("Invalid Login", () => {
        const page = new LoginPage();

        page.visit();
        page.inputUsername("admin");
        page.inputPassword("the Invalid Password");

        page.submitBtn.click();
        page.Message({iserror:true}).should("be.visible")

    })

    it('should login successfully', () => {
        const login = new LoginPage();
        login.login();
    });

    it("Log out from valid login", () => {
        const page = new LoginPage();
        page.visit()
        page.inputUsername()
        page.inputPassword()

        page.submitBtn.click()
        page.validateLogin();

        Dashboard.header.logout();
        page.Message({iserror:false}).should("be.visible")
    })
});
