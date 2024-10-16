import TablePo from "@/utils/components/table.po";
import NetworkPage from "@/pageobjects/network.po";
import { generateName } from '@/utils/utils';

const network = new NetworkPage();
const table = new TablePo();

interface Vlan {
  name: string,
  namespace: string,
  vlan: number,
  clusterNetwork: string,
}

/**
 * 1. Login
 * 2. Navigate to the network create page
 * 3. click Create button
 * Expected Results
 * 1. create/delete network success
*/
export function CheckCreateNetwork() { }
describe('Check create/delete network', () => {
  it('Check create/delete network', () => {
    cy.login();

    const name = generateName('test-network-create');

    network.create({
      name,
      namespace: 'default',
      vlan: '233',
      clusterNetwork: 'mgmt'
    })

    network.delete('default', name)
  });
});

/**
 * 1. Login
 * 2. Navigate to the network create page
 * 3. Input DHCP server IP
 * 4. click Create button
 * Expected Results
 * 1. Create network with DHCP server IP success
*/
export function CheckDHCP() { }
describe('Check network with DHCP', () => {
  it('Check network with DHCP', () => {
    cy.login();

    cy.intercept('POST', `/v1/harvester/k8s.cni.cncf.io.network-attachment-definitions`).as('create');

    const name = generateName('test-network-create');
    const dhcp = '172.0.0.1'
    const namespace = 'default'

    network.create({
      name,
      namespace,
      vlan: '234',
      clusterNetwork: 'mgmt',
      mode: 'Auto (DHCP)',
      dhcp,
    })

    cy.wait('@create').then(res => {
      expect(res.response?.statusCode).to.equal(201);
      const route = res.response?.body?.metadata?.annotations['network.harvesterhci.io/route']

      if (route) {
        const json = JSON.parse(route)
        expect(json.serverIPAddr, 'Check Server IP Address').to.equal(dhcp);
      }
    })

    network.deleteFromStore(`${namespace}/${name}`)
  });
});

/**
 * 1. Login
 * 2. Navigate to the network create page
 * 3. Select manual mode
 * 4. Input Cidr and gateway
 * 5. click Create button
 * Expected Results
 * 1. Create network with manual mode success
*/
export function CheckManualMode() { }
describe('Check network with Manual Mode', () => {
  it('Check network with Manual Mode', () => {
    cy.login();

    cy.intercept('POST', `/v1/harvester/k8s.cni.cncf.io.network-attachment-definitions`).as('create');

    const name = generateName('test-network-create');
    const cidr = '172.0.0.1/24'
    const gateway = '172.0.0.1'
    const namespace = 'default'

    network.create({
      name,
      namespace,
      vlan: '235',
      mode: 'Manual',
      clusterNetwork: 'mgmt',
      cidr,
      gateway,
    })

    cy.wait('@create').then(res => {
      expect(res.response?.statusCode, 'Check create network').to.equal(201);
      const route = res.response?.body?.metadata?.annotations['network.harvesterhci.io/route']
      if (route) {
        const json = JSON.parse(route)
        expect(json.cidr, 'Check CIDR').to.equal(cidr);
        expect(json.gateway, 'Check gateway').to.equal(gateway);
      }
    })

    network.deleteFromStore(`${namespace}/${name}`)
  });
});


export function CreateVlan1() { }
describe('Preset Vlans', () => {
  function createVlan(vlan: Vlan) {
    cy.intercept('POST', `/v1/harvester/k8s.cni.cncf.io.network-attachment-definitions`).as('create');

    const name = vlan.name;
    const namespace = vlan.namespace;
    network.deleteFromStore(`${namespace}/${name}`, network.storeType);
    network.create({
      name,
      namespace,
      vlan: vlan.vlan,
      clusterNetwork: vlan.clusterNetwork,
    })

    table.clickFlatListBtn();

    cy.wait(2000)
    cy.wrap('async').then(() => {
      table.find(name, 2, namespace, 3).then((index) => {
        if (typeof index === 'number') {
          cy.get(`[data-testid="sortable-table-${index}-row"]`).find('td').eq(6).should('contain', 'Active')
        }
      })
    })
  }

  it('Create Vlan1', () => {
    const vlans = Cypress.env('vlans') || [];
    const vlan = vlans[0].vlan

    cy.login();

    createVlan({
      name: `vlan${vlan}`,
      namespace: 'default',
      vlan,
      clusterNetwork: 'mgmt',
    })
  });

  it('Create Vlan2', () => {
    const vlans = Cypress.env('vlans') || [];
    const vlan = vlans[1].vlan

    cy.login();

    createVlan({
      name: `vlan${vlan}`,
      namespace: 'default',
      vlan,
      clusterNetwork: 'mgmt',
    })
  });
});
