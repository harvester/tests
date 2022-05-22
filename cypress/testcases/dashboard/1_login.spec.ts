import { LoginPage } from "@/pageobjects/login.po";
/**
 * This is the login spec
 * 1. Login for first time
 * 2. Login with already set password
 */
describe('login page for harvester', () => {
    it('should login successfully', () => {
        const login = new LoginPage();
        login.login();
    });
});
