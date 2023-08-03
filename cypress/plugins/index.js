/// <reference types="cypress" />
const dotenvPlugin = require('cypress-dotenv');
const fs = require("fs");
const yaml = require('js-yaml');
const { isFileExist, findFiles } = require('cy-verify-downloads');
const AdmZip = require("adm-zip");

let globalVar = {};
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
    isFileExist,
    findFiles,
    readYaml(filename) {
      return new Promise((res, rej) => {
        try {
          res(yaml.load(fs.readFileSync(filename)))
        } catch (e) {
          res(e.message)
        }
      })
    },
    deleteFolder(folderName) {
      return new Promise((resolve, reject) => {
        fs.rmdir(folderName, { maxRetries: 5, recursive: true }, err => {
          if (err && err.code !== "ENOENT") {
            console.error(err)
            reject(err.message)
          }
          resolve(true)
        })
      })
    },
    deleteFile(fileName) {
      return new Promise((resolve, reject) => {
        fs.rm(fileName, { maxRetries: 5, force: true }, err => {
          if (err && err.code !== "ENOENT") {
            console.error(err)
            reject(err.message)
          }
          resolve(true)
        })
      })
    },
    readZipFile(fileName) {
      return new Promise((resolve, reject) => {
        try {
          resolve(new AdmZip(fileName).getEntries())
        } catch (e) {
          console.error(e)
          resolve(e.message)
        }
      })
    },

    setGlobalVariable: (val) => {
      return (globalVar = val);
    },

    getGlobalVariable: () => {
      return globalVar;
    },

  })

  // https://github.com/cypress-io/cypress/issues/349
  // add --disable-dev-shm-usage chrome flag
  on('before:browser:launch', (browser, launchOptions) => {
    if (browser.family === 'chromium') {
      console.log('Adding Chrome flag: --disable-dev-shm-usage');
      launchOptions.args.push('--disable-dev-shm-usage');
    }
    return launchOptions;
  });

  return config;
}
