import YAML from 'js-yaml'

import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";

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
  // randomstring.generate(7)
  const VM_NAME = 'test-vm-automation'

  beforeEach(() => {
    cy.login();
  });

  it('Step 1: Create a vm with all the default values', () => {
    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
    }
    vms.create(value);
  });

  it('Step 2: Config and YAML should show', () => {
    vms.goToConfigDetail(VM_NAME);

    vms.goToYamlDetail(VM_NAME);
  })

  it('Step 3: Delete VM', () => {
    vms.delete(VM_NAME)
  })
});

/**
 * 1. Login
 * 2. Navigate to the VM create page
 * 3. Input required values
 * 4. Check "Start VM on Creation"
 * 4. Validate the create request
 * 5. Validate the yaml
*/
describe('Create a VM with Start VM on Creation checked', () => {
  const VM_NAME = 'test-vm-running-checked-automation'

  beforeEach(() => {
    cy.login();
  });
  
  it('Step 1: Create VM', () => {
    vms.goToCreate();
    const imageEnv = Cypress.env('image');
    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
      createRunning: true,
    }
    vms.setValue(value);

    vms.save();
  });

  it('Step 2: Check yaml', () => {
    cy.intercept('GET', `/apis/kubevirt.io/v1/namespaces/*/virtualmachines/${VM_NAME}`).as('vmDetail');

    vms.goToYamlDetail(VM_NAME);
    
    cy.wait('@vmDetail').then(res => {
      expect(res.response?.statusCode).to.equal(200);
      const yaml = res.response?.body

      const value:any = YAML.load(yaml)
      expect(value?.spec?.running).to.equal(true);
    })
  });
})

/**
 * 1. Login
 * 2. Navigate to the VM create page
 * 3. Input required values
 * 4. uncheck "Start VM on Creation"
 * 4. Validate the create request
 * 5. Validate the yaml
*/
describe('Create a VM with Start VM on Creation unchecked', () => {
  const VM_NAME = 'test-vm-running-unchecked-automation'

  beforeEach(() => {
    cy.login();
  });
  
  it('Step 1: Create VM', () => {
    vms.goToCreate();
    const imageEnv = Cypress.env('image');
    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
      createRunning: false,
    }
    vms.setValue(value);

    vms.save();
  });

  it('Step 2: Check yaml', () => {
    cy.intercept('GET', `/apis/kubevirt.io/v1/namespaces/*/virtualmachines/${VM_NAME}`).as('vmDetail');

    vms.goToYamlDetail(VM_NAME);
    
    cy.wait('@vmDetail').then(res => {
      expect(res.response?.statusCode).to.equal(200);
      const yaml = res.response?.body

      const value:any = YAML.load(yaml)
      expect(value?.spec?.running).to.equal(false);
    })
  });
})

/**
 * 1. Create some image and volume
 * 2. Create virtual machine
 * 3. Fill out all mandatory field but leave memory blank.
 * 4. Click create
*/
export function CheckMemoryRequired() {}
it('Create VM without memory provided', () => {
  const VM_NAME = 'test-memory-required'
  const NAMESPACE = 'default'

  cy.login();

  const imageEnv = Cypress.env('image');

  const value = {
    name: VM_NAME,
    cpu: '2',
    image: imageEnv.name,
    createRunning: false,
  }

  vms.goToCreate();
  vms.setValue(value);

  cy.get('.cru-resource-footer').contains('Create').click()

  cy.contains('"Memory" is required').should('exist')
});



/**
 * 1. Login
 * 2. Navigate to the vm page
 * 3. click Create button, choose create "Multiple Instance"
 * Expected Results
 * 1. vm assignment to different nodes
 * @notImplemented
 */
export function CheckMultiVMScheduler() {}
it("automatic assignment to different nodes when creating multiple vm's", () => {

});
