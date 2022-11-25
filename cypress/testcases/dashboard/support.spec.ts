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
          .should("eq", "https://docs.harvesterhci.io")

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

      cy.readFile(kubeconfig)
        .should("exist")

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
    })

    it('is should download', () => {
      let filename: string | undefined = undefined
      page.generateSupportBundleBtn.click()
      page.inputSupportBundle('this is a test bundle')
          .get("@generateBtn").click()
          .intercept("/v1/harvester/*supportbundles/**/bundle*", req => 
            req.continue(res => {
              cy.log(res.body.status)
              filename = res.body.status?.filename || undefined
            })
          )

      cy.window().then(win => {
        let timeout = {timeout: constants.timeout.downloadTimeout}
        return cy.get("@generateView").then(timeout, $el => {
          return new Promise((resolve, reject) => {
            // delay 3s to refresh page, this will fix page reload bug
            // `DOMNodeRemoved` is deprecated, we probably need to use `MutationObserver`
            // in the future
            $el.one("DOMNodeRemoved", () => setTimeout(() => resolve(win.history.go(0)), 3000))
          })
        })
      })
      .then(() => { // the scope will execute after page reloaded
        new Promise((resolve, reject) => {
          if (filename !== undefined) {
            cy.task("findFiles", {path: Cypress.config("downloadsFolder"), fileName: "supportbundle"})
              .then((files: any) => files.length == 1 ? resolve(files[0]) : reject(files))
          }
          resolve(filename)
        })
        .then(filename => {
          cy.log("Downloaded SupportBundle: ", filename)
          let zipfilename = `${Cypress.config("downloadsFolder")}/${filename}`
          return new Promise((resolve, reject) => {
            cy.task("readZipFile", zipfilename)
              .then(entries => resolve(entries))
          })
        })
        .then((items: any) => {
          cy.log(`ZipFile entries: ${items.length}`)
          let {dirs, files} = items.reduce((groups: any, e: any) => {
            e.isDirectory ? groups.dirs.push(e) : groups.files.push(e)
            return groups
          }, {dirs:[], files:[]})

          cy.log("Total Dirs:", dirs)
          cy.log("Total Files:", files)
          return {dirs, files}
        })
        // .then(({dirs, files}) => {}) // new verfiers here

      })
    })

  })
})
