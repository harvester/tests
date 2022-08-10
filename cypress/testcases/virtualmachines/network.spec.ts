import NetworkPage from '@/pageobjects/network.po';
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";
import { generateName } from '@/utils/utils';

const network = new NetworkPage()
const vms = new VmsPage();
const login = new LoginPage();

describe('Add a network to an existing VM with only 1 network', () => {
  const VM_NAME = generateName('test-network');
  const vlanEnv = Cypress.env('vlans');
  const NETWORK_1 = vlanEnv[0]
  const NETWORK_2 = vlanEnv[1]
  const NAMESPACE = 'default'

  beforeEach(() => {
    cy.login();
  });

  it('VM should start successfully', () => {
    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: Cypress._.toLower(imageEnv.name),
      networks: [{
        network: NETWORK_1,
      }],
      namespace: NAMESPACE,
    }
    vms.create(value);
    vms.goToConfigDetail(VM_NAME);
    cy.url().should('contain', VM_NAME)

    const editValue = {
      networks: [{
        network: NETWORK_1,
      }, {
        network: NETWORK_2,
      }]
    }
    vms.edit(VM_NAME, editValue);

    vms.delete(NAMESPACE, VM_NAME)
  })
})