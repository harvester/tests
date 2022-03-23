import NetworkPage from '@/pageobjects/network.po';
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";

const network = new NetworkPage()
const vms = new VmsPage();
const login = new LoginPage();

describe('Add a network to an existing VM with only 1 network', () => {
  const VM_NAME = 'test-network'
  const NETWORK_1 = 'vlan178'
  const NETWORK_2 = 'vlan188'

  beforeEach(() => {
    cy.login();
  });

  it('Step 1: VM should start successfully', () => {
    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      networks: [{
        network: 'vlan178',
      }]
    }
    vms.create(value);
    vms.goToConfigDetail(VM_NAME);
    cy.url().should('contain', VM_NAME)
  })

  it('Step 2: The already existing network connectivity should still work', () => {
    network.goToList()

    cy.get('.search').type(NETWORK_1)
    const col = cy.contains(NETWORK_1)
    expect(col.should('be.visible'))
    expect(col.parentsUntil('tbody', 'tr').contains('Active').should('be.visible'))
  })

  it('Step 2: Add a network to the VM', () => {
    const value = {
      networks: [{
        network: 'vlan178',
      }, {
        network: 'vlan188',
      }]
    }
    vms.edit(VM_NAME, value);
  })

  it('Step 4: The new connectivity should also work', () => {
    network.goToList()

    cy.get('.search').type(NETWORK_2)
    const col = cy.contains(NETWORK_2)
    expect(col.should('be.visible'))
    expect(col.parentsUntil('tbody', 'tr').contains('Active').should('be.visible'))
  })

  it('Step 3: Delete VM', () => {
    vms.delete(VM_NAME)
  })
})