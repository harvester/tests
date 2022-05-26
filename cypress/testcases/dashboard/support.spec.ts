import { SupportPage } from "@/pageobjects/support.po";

describe("Support Page", () => {
  const page = new SupportPage();
  beforeEach(() => {
    page.visit();
  })

  context("Links in Community Support Section", () => {
    it("Should Link to Harvester Document", () => {
      page.docsBtn.invoke("attr", "href")
          .should("eq", "https://docs.harvesterhci.io/latest/")
    })

    it("Should Link to Rancher Forum", () => {
      page.forumsBtn.invoke("attr", "href")
          .should("eq", "https://forums.rancher.com/c/harvester/")
    })

    it("Should Link to Rancher Slack", () => {
      page.slackBtn.invoke("attr", "href")
          .should("eq", "https://slack.rancher.io")
    })

    it("Should Link to Harvester Github Isuse", () => {
      page.fileAnIssueBtn.invoke("attr", "href")
          .should("eq", "https://github.com/harvester/harvester/issues/new/choose")
    })
  })

  context("Download KubeConfig File", () => {
    it("Should be Downloaded", async () => {
      const kubeconfig = `${Cypress.config("downloadsFolder")}/local.yaml`
      page.downloadKubeConfigBtn.click()

      cy.readFile(kubeconfig)
        .should("exist")

      cy.task("readYaml", kubeconfig)
        .should(val => expect(val).to.not.be.a('string'))

    })
  })


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
  context('Generate Support Bundle', () => {
    it('Generate Support Bundle', () => {
      cy.login();
      support.generateSupportBundle('this ia a test description');
    });
  });
})
