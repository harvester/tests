import cookie from 'cookie';

import { Constants } from '../constants/constants'
const constants = new Constants();

require('cy-verify-downloads').addCustomCommand();

Cypress.Commands.add('login', (params = {}) => {
    const url = params.url || constants.dashboardUrl;
    const username = params.username ||   Cypress.env('username');
    const password = params.password || Cypress.env('password');

    cy.visit(`/auth/login`);
    cy.intercept('GET', '/v3-public/authProviders').as('authProviders');
    cy.wait('@authProviders').then(res => {
      const { CSRF } = cookie.parse(document.cookie);
      cy.request({
        method: 'POST',
        url: '/v3-public/localProviders/local?action=login',
        body: {
          description:"UI session",
          responseType:"cookie",
          username,
          password
        },
        headers: {
          'x-api-csrf': CSRF
        }
      }).then(() => {
        cy.visit(url); // After successful login, you can switch to the specified page, which is the home page by default
        cy.get('.initial-load-spinner', { timeout: constants.timeout.maxTimeout })
        cy.get(".dashboard-content .product-name").contains("Harvester")
      });
    })
});

Cypress.Commands.add('stopOnFailed', () => {
  Cypress.on('fail', (e, test) => {
    Cypress.runner.stop();
    throw new Error(e.message);
  })
})

Cypress.Commands.overwrite('visit', (originalFn, url, options) => {
  url = Cypress.env('urlPath')
  return originalFn(url, options)
})

Cypress.on('uncaught:exception', (err, runable) => {
  return false;
})
