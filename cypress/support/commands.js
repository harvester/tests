import cookie from 'cookie';

import { Constants } from '../constants/constants'
const constants = new Constants();
// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })
Cypress.Commands.add('login', (username = Cypress.env('username'), password = Cypress.env('password')) => {
    const isDev = Cypress.env('NODE_ENV') === 'dev';
    const baseUrl = isDev ? Cypress.config('baseUrl') : `${Cypress.config('baseUrl')}/dashboard`;
    cy.visit(`${baseUrl}/auth/login`);
    cy.intercept('GET', '/v3-public/authProviders').as('authProviders');
    cy.wait('@authProviders').then(res => {
      const { CSRF } = cookie.parse(document.cookie);
      cy.request({
        method: 'POST',
        url: '/v3-public/localProviders/local?action=login',
        body: {
          "description":"UI session",
          "responseType":"cookie",
          "username":"admin",
          "password":"password1234"
        },
        headers: {
          'Content-Type': 'application/json;charset=UTF-8',
          'x-api-csrf': CSRF
        }
      });
    })
});