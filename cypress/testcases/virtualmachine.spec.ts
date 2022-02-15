import { VmsPage } from "../pageobjects/virtualmachine.po";
import { LoginPage } from "../pageobjects/login.po";

const vms = new VmsPage();
const login = new LoginPage();
const VM_NAME = 'test-vm-name-automation'

describe('VM Page', () => {
  beforeEach(() => {
    login.login();
  });

  it('Create a vm with all the default values', () => {
    vms.goToCreate();

    const defaultValue = {
      namespace: 'default',
      name: VM_NAME,
      description: 'test-vm-description-automation',
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      network: 'vlan1',
    }
    vms.setValue(defaultValue);

    vms.save();
  });

  it('Config and YAML should show', () => {
    vms.goToList();
    cy.get('.search').type(VM_NAME)
    cy.contains(VM_NAME).click()

    const config = cy.get('.masthead button').contains('Config')
    expect(config.should('be.visible'));
    config.click()
    cy.url().should('contain', 'config')

    const yaml = cy.get('.masthead button').contains('YAML')
    expect(yaml.should('be.visible'));
    yaml.click()
    cy.url().should('contain', 'yaml')
  })
});
