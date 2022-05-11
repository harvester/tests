import YAML from 'js-yaml'

import networkPage from "@/pageobjects/network.po";
import { LoginPage } from "@/pageobjects/login.po";
import {generateName} from '@/utils/utils';


const network = new networkPage();
const login = new LoginPage();

/**
 * 1. Login
 * 2. Navigate to the network create page
 * 3. click Create button
 * Expected Results
 * 1. Create network success
*/
export function CheckCreateNetwork() {}
describe('Check create/delete network', () => {
  it('Check create/delete network', () => {
    cy.login();

    const name = generateName('test-network-create');

    network.create({
      name,
      namespace: 'default',
      vlan: '233',
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
export function CheckDHCP() {}
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
      mode: 'Auto(DHCP)',
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

    network.deleteProgramlly(`${namespace}/${name}`)
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
export function CheckManualMode() {}
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

    network.deleteProgramlly(`${namespace}/${name}`)
  });
});
