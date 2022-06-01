import { SupportPage } from "@/pageobjects/support.po";
import {Constants} from "../../constants/constants";
const constants = new Constants;

describe("Support Page", () => {
  const page = new SupportPage();
  before(() => cy.task("deleteFolder", Cypress.config("downloadsFolder")))

  beforeEach(() => {
    page.visit();
  })

  context("Links in Community Support Section", () => {
    it("Should Link to correct URLs", () => {
      page.docsBtn.invoke("attr", "href")
          .should("eq", "https://docs.harvesterhci.io/latest/")

      page.forumsBtn.invoke("attr", "href")
          .should("eq", "https://forums.rancher.com/c/harvester/")

      page.slackBtn.invoke("attr", "href")
          .should("eq", "https://slack.rancher.io")

      page.fileAnIssueBtn.invoke("attr", "href")
          .should("eq", "https://github.com/harvester/harvester/issues/new/choose")
    })
  })

  context("Download KubeConfig File", () => {
    it("Should be Downloaded", () => {
      const kubeconfig = `${Cypress.config("downloadsFolder")}/local.yaml`
      page.downloadKubeConfigBtn.click()

      // cy.readFile(kubeconfig)
      //   .should("exist")
      cy.verifyDownload('local.yaml', {timeout: constants.timeout.downloadTimeout});

      cy.task("readYaml", kubeconfig)
        .should(val => expect(val).to.not.be.a('string'))

    })
  })

  context('Generate Support Bundle', () => {
    it('is required to input Description', () => {
      page.generateSupportBundleBtn.click()

      page.inputSupportBundle()
          .get("@generateBtn").click()

      // to verify the button renamed with `Error`
      cy.get("@generateBtn")
        .should("be.not.disabled")
        .should("contain", "Error")

      // to verify the error message displayed
      cy.get("@generateView")
        .get(".banner.error")
        .should("be.visible")

      // to verify the view disappeared.
      cy.get("@closeBtn").click()
      cy.get("@generateView")
        .children()
        .should($el => expect($el).to.have.length(0))
    }),
    // This will download the support bundle and check if it 
    it('is should download', () => {
      page.generateSupportBundleBtn.click()
      // This creates an event listener that adds a timeout on the reload account. If the download exceeds
      // the downloadTimeout, or the pageLoadTimeout in cypress.json then it will not pass correctly
      cy.window().document().then(function (doc) {
        doc.addEventListener('click', () => {
          setTimeout(function () { doc.location.reload() }, constants.timeout.downloadTimeout)
        })

          page.inputSupportBundle('this is a test bundle')
            .get("@generateBtn").click()
            // Verify that the download has completed
            .verifyDownload('supportbundle', {timeout: constants.timeout.downloadTimeout, contains: true})
            .intercept('/v1/harvester/supportbundles*/download', (req) => {
              req.reply((res) => {
                expect(res.statusCode).to.equal(200);
                });
              })

            })
            // This verified the file after the event listenter in case the
            // reload timeout triggered before the other timeouts. Then it will give a false success. This should catch that use case
            cy.verifyDownload('supportbundle', {timeout: constants.timeout.downloadTimeout, contains: true});

          })
  });
})
