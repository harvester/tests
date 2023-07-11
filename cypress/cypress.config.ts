import { defineConfig } from 'cypress'

export default defineConfig({
  pageLoadTimeout: 120000,
  fixturesFolder: './fixtures',
  viewportWidth: 1920,
  viewportHeight: 1080,
  numTestsKeptInMemory: 1,
  defaultCommandTimeout: 240000,
  requestTimeout: 240000,
  responseTimeout: 240000,
  chromeWebSecurity: false,
  env: {
    NODE_ENV: 'production',
    username: 'admin',
    password: 'password1234',
    mockPassword: "mockPassword",
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
      name: 'openSUSE-Leap-15.3-3-NET-x86_64.qcow2',
      url: 'https://download.opensuse.org/pub/opensuse/distribution/leap/15.3/appliances/openSUSE-Leap-15.3-JeOS.x86_64-15.3-OpenStack-Cloud-Current.qcow2',
    },
    nfsEndPoint: 'nfs://ip',
    vlanIDs: [1, 2],
  },
  retries: {
    runMode: 0,
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
    specPattern: [
      './testcases/dashboard/*.spec.ts',
      './testcases/settings/*.spec.ts',
      './testcases/image/*.spec.ts',
      './testcases/networks/*.spec.ts',
      './testcases/**/*.spec.ts',
    ],
    supportFile: './support/index.js',
    baseUrl: 'https://192.168.0.131',
    experimentalSessionAndOrigin: true,
    video: false,
  },
})
