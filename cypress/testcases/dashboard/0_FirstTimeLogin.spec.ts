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
      const page = new LoginPage();
      page.visit();

      page.checkEula(true);
      expect(page.submitBtn.should('be.enabled'));

      page.checkEula(false);
      expect(page.submitBtn.should("be.disabled"));

    });

    it("is optional to accept collection of anonymous statstics", () => {
      onlyOn(isFirstTimeLogin);
      const page = new LoginPage();
      page.visit();

      page.checkTelemetry(true);
      expect(page.submitBtn.should("be.disabled"));

      page.checkTelemetry(false);
      expect(page.submitBtn.should("be.disabled"));

    });
  });

  context("Set Password", () => {
    specify("Password inconsistant", () => {
      onlyOn(isFirstTimeLogin);
      const page = new LoginPage();
      page.visit();
      page.selectSpecificPassword();
      page.checkEula(true);

      page.inputPassword("abcd1234");
      expect(page.submitBtn.should("be.disabled"));

      page.inputPassword(page.password, "abcd1234");
      expect(page.submitBtn.should("be.disabled"));

    });

    specify("Password consistant", () => {
      onlyOn(isFirstTimeLogin);
      const page = new LoginPage();
      page.visit();
      page.selectSpecificPassword();
      page.checkEula(true);

      page.inputPassword(page.password, page.password);
      expect(page.submitBtn.should("be.enabled"));
    });
  });

  after(() => {
    // side-effect of login
    if (isFirstTimeLogin) {
      const page = new LoginPage();
      page.visit()
          .selectSpecificPassword()
          .checkTelemetry(false)
          .checkEula(true)
          .inputPassword()
          .submitBtn.click();

      page.validateLogin();
    }
  })
});