import { HostsPage } from "../pageobjects/hosts.po";
import { EditYamlPage } from "../pageobjects/editYaml.po";
import { LoginPage } from "../pageobjects/login.po";
import { HCI } from '@/constants/types'

const hosts = new HostsPage();
const editYaml = new EditYamlPage();
const login = new LoginPage();

/**
 * This will insert custom YAML into the hosts page while editing
 */
export function insertCustomYAML() {}
describe('should insert custom name into YAML', () => {
  it('should insert custom name into YAML', () => {
    cy.login();
    hosts.navigateHostsPage();
    hosts.editHostsYaml();
    editYaml.insertCustomName('This is a custom name');
  });
});

export function CheckEdit() {}
describe('Check edit host', () => {
  it('Check edit host', () => {
    cy.login();
    
    const host = Cypress.env('host');
    
    cy.visit(`/c/local/harvester/${HCI.HOST}/${host.name}?mode=edit`)

    const customName = 'test-custom-name'
    const consoleUrl = 'test-console-url'

    hosts.setValue({
      customName,
      consoleUrl,
    })

    cy.intercept('PUT', `/v1/harvester/nodes/*`).as('update');

    hosts.update(host.name)

    cy.wait('@update').then(res => {
      const annotations = res.response?.body?.metadata?.annotations || {}
      expect(annotations['harvesterhci.io/host-custom-name'], 'Check custom name').to.equal(customName);
      expect(annotations['harvesterhci.io/host-console-url'], 'Check console url').to.equal(consoleUrl);
    })
  })
})

export function CheckAddDisk() {}
describe('Check Add disk', () => {
  it('Check Add disk', () => {
    cy.login();
    
    const host = Cypress.env('host');
    const disk = host.disks[0]
    
    cy.visit(`/c/local/harvester/${HCI.HOST}/${host.name}?mode=edit`)

    const diskTab = '#disk > a'
    const addDiskButton = '.button-dropdown'
    const diskOption = '.vs__dropdown-option'
    const removeIcon = '.btn > .icon'

    cy.get(diskTab).click()

    cy.contains(addDiskButton, 'Add Disk').click()
    cy.contains(diskOption, `${disk.devPath}`).click()

    cy.intercept('PUT', `/v1/harvester/${HCI.BLOCK_DEVICE}s/longhorn-system/${disk.name}`).as('updateBD');

    hosts.update(host.name)

    cy.wait('@updateBD').then(res => {
      const spec = res.response?.body?.spec || {}
      expect(spec?.fileSystem?.provisioned, 'Check provisioned').to.equal(true);
    })

    cy.visit(`/c/local/harvester/${HCI.HOST}/${host.name}?mode=edit`)

    cy.get(diskTab).click()
    cy.get(removeIcon).click()

    cy.intercept('PUT', `/v1/harvester/${HCI.BLOCK_DEVICE}s/longhorn-system/${disk.name}`).as('updateBD');

    hosts.update(host.name)

    cy.wait('@updateBD').then(res => {
      const spec = res.response?.body?.spec || {}
      expect(spec?.fileSystem?.provisioned, 'Check provisioned').to.equal(false);
    })
  })
})
