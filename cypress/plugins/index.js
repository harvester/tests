/// <reference types="cypress" />
const dotenvPlugin = require('cypress-dotenv');
const fs = require("fs");
const yaml = require('js-yaml');
// ***********************************************************
// This example plugins/index.js can be used to load plugins
//
// You can change the location of this file or turn off loading
// the plugins file with the 'pluginsFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/plugins-guide
// ***********************************************************

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)

/**
 * @type {Cypress.PluginConfig}
 */
// eslint-disable-next-line no-unused-vars
module.exports = (on, config) => {
  config = dotenvPlugin(config)

  // `on` is used to hook into various events Cypress emits
  // `config` is the resolved Cypress config
  config.baseUrl = config.env.baseUrl;

  on("task", {
    readYaml(filename) {
      return new Promise((res, rej) => {
        try {
          res(yaml.load(fs.readFileSync(filename)))
        } catch (e) {
          res(e.message)
        }
      })
    }
  })

  return config;
}
