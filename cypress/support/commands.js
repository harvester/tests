import cookie from 'cookie';

import { Constants } from '../constants/constants'
const constants = new Constants();

require('cy-verify-downloads').addCustomCommand();
Cypress.Commands.add('login', (username = Cypress.env('username'), password = Cypress.env('password')) => {
    const isDev = Cypress.env('NODE_ENV') === 'dev';
    const baseUrl = isDev ? Cypress.config('baseUrl') : `${Cypress.config('baseUrl')}/dashboard`;
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
        cy.visit('/'); // Login successfully to the dashboard page
        cy.get('.initial-load-spinner', { timeout: constants.timeout.maxTimeout })
        cy.get("main h1 span").contains("Harvester")
      });
    })
});

Cypress.Commands.add('stopOnFailed', () => {
  Cypress.on('fail', (e, test) => {
    Cypress.runner.stop();
    throw new Error(e.message);
  })
})

Cypress.Commands.overwrite('visit', (originalFn, url = '', options) => {
  const isDev = Cypress.env('NODE_ENV') === 'dev';

  if (!isDev) {
    url = `/dashboard${url}`;
  }

  return originalFn(url, options)
})
