import { onlyOn } from "@cypress/skip-test";
import { LoginPage } from "@/pageobjects/login.po";


describe("First Time Login Page", () => {
  let isFirstTimeLogin: boolean = false;
  before(async () => {
    isFirstTimeLogin = await LoginPage.isFirstTimeLogin();
  })

  context("Check Options", () => {
    it("is required to accept term", () => {
      onlyOn(isFirstTimeLogin);
    });

    it("is optional to accept collection of anonymous statstics", () => {
      onlyOn(isFirstTimeLogin);
    });
  });

  context("Set Password", () => {
    specify("Password inconsistant", () => {
      onlyOn(isFirstTimeLogin);
    });

    specify("Password consistant", () => {
      onlyOn(isFirstTimeLogin);
    });
  });
});


/**
 * This is the login spec
 * 1. Login for first time
 * 2. Login with already set password
 */
describe('login page for harvester', () => {
    it('should login the first time', () => {
        const login = new LoginPage();
        login.firstLogin();
    });
    
    it('should login successfully', () => {
        const login = new LoginPage();
        login.login();
    });
});
