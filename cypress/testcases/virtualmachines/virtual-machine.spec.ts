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
  const VM_NAME = 'test-vm-name-automation'

  beforeEach(() => {
    login.login();
  });

  it('Step 1: Create a vm with all the default values', () => {
    vms.goToCreate();

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
    }
    vms.setValue(value);

    vms.save();
  });

  it('Step 2: Config and YAML should show', () => {
    vms.goToConfigDetail(VM_NAME);

    vms.goToYamlDetail(VM_NAME);
  })
});

/**
 * 1. Login
 * 2. Navigate to the VM create page
 * 3. Input required values
 * 4. Check "Start VM on Creation"
 * 4. Validate the create request
 * 5. Validate the config
 * 6. Validate the yaml
*/
describe('Create a VM with Start VM on Creation checked', () => {
  const VM_NAME = 'test-vm-running-checked-automation'

  beforeEach(() => {
    login.login();
  });
  
  it('Step 1: Create VM', () => {
    vms.goToCreate();

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      createRunning: true,
    }
    vms.setValue(value);

    vms.save();
  });

  it('Step 2: Check config', () => {
    vms.goToConfigDetail(VM_NAME);
    
    cy.wrap(vms.createRunning().value()).should('eq', true)
  });

  it('Step 3: Check yaml', () => {
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
 * 5. Validate the config
 * 6. Validate the yaml
*/
describe('Create a VM with Start VM on Creation unchecked', () => {
  const VM_NAME = 'test-vm-running-unchecked-automation'

  beforeEach(() => {
    login.login();
  });
  
  it('Step 1: Create VM', () => {
    vms.goToCreate();

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      createRunning: false,
    }
    vms.setValue(value);

    vms.save();
  });

  it('Step 2: Check config', () => {
    vms.goToConfigDetail(VM_NAME);
    
    cy.wrap(vms.createRunning().value()).should('eq', false)
  });

  it('Step 3: Check yaml', () => {
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
