type login = {
  username?: string, 
  password?: string,
  url?: string
}

declare namespace Cypress {
  interface Chainable {
    login(login?: login): Chainable<Element>;
  }
}
