import YAML from 'js-yaml'

import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";
import { generateName } from '@/utils/utils';

const vms = new VmsPage();
const login = new LoginPage();

/**
 * 1. Login
 * 2. Navigate to the VM create page
 * 3. Input required values
 * 4. Validate the create request
 * 5. Validate the config and yaml should show
*/
describe('Create a vm with all the default values', () => {
  const VM_NAME = generateName('test-vm-create');
  const namespace = 'default'

  beforeEach(() => {
    cy.login();
  });

  it('Create a vm with all the default values', () => {
    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: Cypress._.toLower(imageEnv.name),
      namespace,
    }

    vms.create(value)

    vms.goToConfigDetail(VM_NAME);

    vms.goToYamlDetail(VM_NAME);

    vms.delete(namespace, VM_NAME)
  });
});

/**
 * 1. Create some image and volume
 * 2. Create virtual machine
 * 3. Fill out all mandatory field but leave memory blank.
 * 4. Click create
*/
export function CheckMemoryRequired() {}
describe('Create VM without memory provided', () => {
  it('Create VM without memory provided', () => {
    const VM_NAME = generateName('test-memory-required');
    const namespace = 'default'
  
    cy.login();
  
    const imageEnv = Cypress.env('image');
  
    const value = {
      name: VM_NAME,
      cpu: '2',
      image: Cypress._.toLower(imageEnv.name),
      namespace,
    }
  
    vms.goToCreate();
    vms.setValue(value);
  
    cy.get('.cru-resource-footer').contains('Create').click()
  
    cy.contains('"Memory" is required').should('exist')
  });
})

/**
 * 1. Login
 * 2. Navigate to the vm page
 * 3. click Create button, choose create "Multiple Instance"
 * Expected Results
 * 1. vm assignment to different nodes
 * @notImplemented
 */
export function CheckMultiVMScheduler() {}
describe("automatic assignment to different nodes when creating multiple vm's", () => {
  it("automatic assignment to different nodes when creating multiple vm's", () => {

  });
})
