import { SupportPage } from "@/pageobjects/support.po";
import { Constants } from "@/constants/constants";
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

    it('should download successfully', () => {
      let filename: string | undefined = undefined
      page.generateSupportBundleBtn.click()

      page.inputSupportBundle('this is a test bundle')
          .get("@generateBtn").click()
          .intercept("/v1/harvester/*supportbundles/**/bundle*", req => 
            req.continue(res => {
              filename = res.body?.metadata?.name
            })
          )
 
      cy.window().then(win => {
        const timeout = {timeout: constants.timeout.downloadTimeout}
        cy.log(`Wait for ${timeout.timeout} ms to generate and download support bundle`)
        return cy.get("@generateView").then(timeout, ($el) => {
          return new Promise((resolve, reject) => {
            const modalObserver = new MutationObserver((mutationList) => {
              if(mutationList.length && mutationList[0]?.type === "childList") {
                  // page needs to reload after downloaded support bundle, delay 3s to refresh page
                  setTimeout(() => resolve(win.history.go(0)), 3000)
              }else{
                reject('Error: monitoring generate modal closed, no childList mutation found');
              }
            });
            modalObserver.observe($el[0], { childList: true, characterData: true });
          })
        })
      })
      .then(() => { // the scope will execute after page reloaded
        new Promise((resolve, reject) => {
          if(filename === undefined) {
            reject('filename is undefined')
          }
          const supportBundle = {path: Cypress.config("downloadsFolder"), fileName: "supportbundle"}
          // resolve real bundle filename
          cy.task("findFiles", supportBundle)
            .then((files: any) => files.length === 1 ? resolve(files[0]) : reject(files))
        })
        .then(filename => {
          cy.log("Downloaded SupportBundle: ", filename)
          const zipFileName = `${Cypress.config("downloadsFolder")}/${filename}`
          // resolve file entries in zip
          return new Promise((resolve) => {
            cy.task("readZipFile", zipFileName).then(entries => resolve(entries))
          })
        })
        .then((items: any) => {
          cy.log(`Total file entries in zip : ${items.length}`)

          const {dirs, files} = items.reduce((groups: any, e: any) => {
            e.isDirectory ? groups.dirs.push(e) : groups.files.push(e)
            return groups
          }, {dirs:[], files:[]})

          cy.log("Total Dirs count :", dirs.length)
          cy.log("Total Files count:", files.length)
          expect(dirs.length).to.greaterThan(0)  
          expect(files.length).to.greaterThan(0)  
        })
      })
    })
  })
})
