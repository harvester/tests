import type { CypressChainable } from '@/utils/po.types'
import ComponentPo from './component.po';

export class Navbar {
  public static get DashboardBtn(): CypressChainable {
    return cy.get("nav a").contains("Dashboard")
  }

  public static get HostsBtn(): CypressChainable {
    return cy.get("nav a").contains(/^Hosts$/)
  }

  public static get VirtualMachinesBtn(): CypressChainable {
    return cy.get("nav a").contains("Virtual Machines")
  }

  public static get VolumesBtn(): CypressChainable {
    return cy.get("nav a").contains("Volumes")
  }

  public static get ImagesBtn(): CypressChainable {
    return cy.get("nav a").contains("Images")
  }

  public static get NamespacesBtn(): CypressChainable {
    return cy.get("nav a").contains("Namespaces")
  }

  public static get AdvancedToggle(): CypressChainable {
    return cy.get("nav .header").contains("Advanced").siblings("i.toggle")
  }

  public static get TemplatesBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("Templates")
  }

  public static get BackupsBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("Backups")
  }

  public static get NetworksBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("Networks")
  }

  public static get SSHKeysBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("SSH Keys")
  }

  public static get CloudConfigTemplateBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("Cloud Config Template")
  }

  public static get SettingsBtn(): CypressChainable {
    return Navbar.AdvancedToggle.click().get("nav a").contains("Settings")
  }

  public static get SupportLink(): CypressChainable {
    return cy.get("nav> .footer a").contains("Support")
  }

  public static get versionText(): CypressChainable {
    return cy.get("nav> .footer .version")
  }

  public static get LangBtn(): CypressChainable {
    return cy.get("nav> .footer .trigger")
  }

  /**
   * 
   * @param navName Menu name
   * @param matchUrl The url that is expected to match
   * @param listPageHeaderText The title of the page
   * @param parentNavs Menu Path
   * @param exact Exact match of text
   */
  clickMenuNav(navName: string, matchUrl: string, listPageHeaderText: string, parentNavs: Array<string> = [], exact: boolean = true) {
    function recursionClickNav(parentNav: string, idx: number) {
      return cy.contains(new RegExp("^" + parentNav + "$")).click().parentsUntil('.has-children').next().within(($el) => {
        if (parentNavs.length === idx + 1) {
          cy.get('li a').contains(new RegExp("^" + navName + "$")).click();

          cy.location().should(loc => {
            const deleteHash = loc.href.replace(loc.hash, '');
            expect(deleteHash).to.eq(`${new Navbar().basePath()}/${matchUrl}`)
          })

          cy.wait(2000); // need to wait here, because when you click on the secondary menu, it will automatically jump to the first position in the secondary menu
          cy.get('a').parentsUntil('body').find('main .outlet header h1').should('be.visible').invoke('text').then((_text) => {
            if (exact) {
              expect(_text.trim()).eq(listPageHeaderText);
            } else {
              expect(_text.trim()).include(listPageHeaderText);
            }
            cy.log(`${navName} Nav go to the correct page and display it`);
          });
        } else {
          cy.get('div h6').contains(new RegExp("^" + parentNavs[idx + 1] + "$")).click();
        }
      })
    }

    if (parentNavs.length === 0) {
      cy.get("nav a").contains(new RegExp("^" + navName + "$")).click();
      cy.location().should(loc => {
        const deleteHash = loc.href.replace(loc.hash, '');
        expect(deleteHash).to.eq(`${this.basePath()}/${matchUrl}`)
      })

      cy.wait(2000);
      cy.get('a').parentsUntil('body').find('main .outlet header h1').should('be.visible').invoke('text').then((_text) => {
        expect(_text.trim()).eq(listPageHeaderText)
        cy.log(`${navName} Nav go to the correct page and display it`)
      });
    } else {
      cy.get("nav .accordion.has-children").within(($el) => {
        parentNavs.map((parentNav, idx) => {
          recursionClickNav(parentNav, idx);
        })
      })
    }
  }

  basePath() {
    return Cypress.env('NODE_ENV') === 'dev' ? Cypress.env('baseUrl') : `${Cypress.env('baseUrl')}/dashboard`;
  }
}

class Header {
  public static get userBtn(): CypressChainable {
    return cy.get("header .user-menu")
  }

  public static get nameSpaceBtn(): CypressChainable {
    return cy.get("header .ns-dropdown")
  }

  public static logout() {
    Header.userBtn.click().get(".user-menu-item").contains("Log Out").click()
  }
}

export default class PagePo extends ComponentPo {
  public static nav = Navbar;
  public static header = Header;

  constructor(private path: string, selector: string = '.dashboard-root') {
    super(selector);
  }

  static goTo(path: string): Cypress.Chainable<Cypress.AUTWindow> {
    return cy.visit(path);
  }

  goTo(): Cypress.Chainable<Cypress.AUTWindow> {
    return PagePo.goTo(this.path);
  }

  isCurrentPage(): Cypress.Chainable<boolean> {
    return cy.url().then(url => url === Cypress.env('baseUrl') + this.wrapPath(this.path));
  }

  checkIsCurrentPage() {
    return this.isCurrentPage().should('eq', true);
  }

  wrapPath(path: string) {
    const isDev = Cypress.env('NODE_ENV') === 'dev';
    let url = path;
    if (!isDev) {
      url = `/dashboard${path}`;
    }

    return url
  }

  basePath() {
    return Cypress.env('NODE_ENV') === 'dev' ? Cypress.env('baseUrl') : `${Cypress.env('baseUrl')}/dashboard`;
  }
}
