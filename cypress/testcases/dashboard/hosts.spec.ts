import { HostsPage } from "@/pageobjects/hosts.po";
import { EditYamlPage } from "@/pageobjects/editYaml.po";
import { HCI } from '@/constants/types'

const hosts = new HostsPage();
const editYaml = new EditYamlPage();

/**
 * TODO:
 * This will insert custom YAML into the hosts page while editing
 */
describe('should insert custom name into YAML', () => {
  it.skip('should insert custom name into YAML', () => {
    cy.login();
    hosts.navigateHostsPage();
    hosts.editHostsYaml();
    editYaml.insertCustomName('This is a custom name');
  });
});

describe('Check edit host', () => {
  it('Check edit host', () => {
    cy.login();
    
    const host = Cypress.env('host')[0];

    const customName = 'test-custom-name'
    const consoleUrl = 'test-console-url'

    hosts.goToEdit(host.name);
    hosts.setValue({
      customName,
      consoleUrl,
    })

    // TODO: The footer position is inconsistent on the host edit page.
    hosts.update(host.name)

    hosts.goToEdit(customName);
    hosts.checkBasicValue(customName, {
      customName,
      consoleUrl
    })
  })
})

describe('Check Add disk', () => {
  it.skip('Check Add disk', () => {
    cy.login();
    
    const host = Cypress.env('host')[0];
    const disk = host.disks[0]
    
    cy.visit(`/harvester/c/local/${HCI.HOST}/${host.name}?mode=edit`)

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

    cy.visit(`/harvester/c/local/${HCI.HOST}/${host.name}?mode=edit`)

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
