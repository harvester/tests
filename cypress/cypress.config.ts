import { defineConfig } from 'cypress'

export default defineConfig({
  // https://docs.cypress.io/guides/references/configuration#Folders-Files
  defaultCommandTimeout: 240000,
  pageLoadTimeout: 120000,
  responseTimeout: 240000,
  requestTimeout: 240000,
  viewportWidth: 1920,
  viewportHeight: 1080,

  fixturesFolder: './fixtures',
  numTestsKeptInMemory: 1,
  chromeWebSecurity: false,
  screenshotsFolder: 'cypress/results/mochawesome-report/assets',
  downloadsFolder: 'cypress/downloads',
  env: {
    NODE_ENV: 'production',
    username: 'admin',
    password: 'password1234',
    mockPassword: "mockPassword",
    baseUrl: 'https://online-server',
    host: {
      name: 'harvester-node-1',
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
    vlans: [
      {
        nic: 'ens7',
        vlan: 100,
      },
      {
        nic: 'ens8',
        vlan: 104
      }
    ],
    sshKey: 'Your ssh public key, use for validate connect VM. e.g. ssh-rsa xxx',
    privateKeyPath: 'Your ssh private Key Path'
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
