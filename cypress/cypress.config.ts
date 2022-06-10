import { defineConfig } from 'cypress'

export default defineConfig({
  pageLoadTimeout: 120000,
  fixturesFolder: './fixtures',
  viewportWidth: 1920,
  viewportHeight: 1080,
  numTestsKeptInMemory: 5,
  defaultCommandTimeout: 30000,
  requestTimeout: 20000,
  responseTimeout: 20000,
  env: {
    NODE_ENV: 'production',
    username: 'admin',
    password: 'admin',
    baseUrl: 'https://online-server',
    host: {
      name: '',
      disks: [
        {
          name: '',
          devPath: '',
        },
      ],
    },
    image: {
      name: 'openSUSE-Leap-15.3-3-DVD-x86_64-Build38.1-Media.iso',
      url: 'https://mirrors.bfsu.edu.cn/opensuse/distribution/leap/15.3/iso/openSUSE-Leap-15.3-3-DVD-x86_64-Build38.1-Media.iso',
    },
    nfsEndPoint: 'nfs://ip',
  },
  retries: {
    runMode: 1,
    openMode: 0,
  },
  reporter: 'mochawesome',
  reporterOptions: {
    reportDir: 'cypress/results',
    overwrite: false,
    html: false,
    json: true,
  },
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      return require('./plugins/index.js')(on, config)
    },
    specPattern:
      './testcases/**/*.spec.ts',
    supportFile: './support/index.js',
    baseUrl: 'https://online-server',
    experimentalSessionAndOrigin: true,
  },
})
