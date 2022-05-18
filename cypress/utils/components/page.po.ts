import ComponentPo from './component.po';

export default class PagePo extends ComponentPo {
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
