import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { VolumePage } from "@/pageobjects/volume.po";
import NamespacePage from "@/pageobjects/namespace.po";
import { PageUrl } from "@/constants/constants";
import { generateName } from '@/utils/utils';
import { Constants } from "@/constants/constants";

const vms = new VmsPage();
const volumes = new VolumePage();
const constants = new Constants();
const namespaces = new NamespacePage();

describe('VM Form Validation', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  /**
   * 1. Login
   * 2. Navigate to the VM create page
   * 3. Input required values
   * 4. Validate the create request
   * 5. Validate the config and yaml should show
  */
  it('Create a vm with all the default values', () => {
    const VM_NAME = generateName('test-vm-create');
    const namespace = 'default'
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

    vms.goToYamlEdit(VM_NAME);

    vms.delete(namespace, VM_NAME)
  });


  /**
   * https://harvester.github.io/tests/manual/virtual-machines/1283-vm-creation-required-fields/
   */
   it('Check VM creation without required-fields', () => {
    vms.goToCreatePage();
    vms.clickFooterBtn();
    cy.get('#cru-errors').contains('"Name" is required').should('exist');
    cy.get('#cru-errors').contains('"Cpu" is required').should('exist');
    cy.get('#cru-errors').contains('"Memory" is required').should('exist');
    cy.get('#cru-errors').contains('"Image" is required').should('exist');
  })

  /**
   * 1. Create some image and volume
   * 2. Create virtual machine
   * 3. Fill out all mandatory field but leave memory blank.
   * 4. Click create
  */
  it('Create VM without memory provided', () => {
    const VM_NAME = 'test-memory-required';
    const namespace = 'default'
  
    const imageEnv = Cypress.env('image');
  
    const value = {
      name: VM_NAME,
      cpu: '2',
      image: Cypress._.toLower(imageEnv.name),
      namespace,
    }
  
    vms.goToCreate();
    vms.setValue(value);
  
    vms.clickFooterBtn();
  
    cy.contains('"Memory" is required').should('exist')
  });
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
describe("automatic assignment to different nodes when creating multiple vm's", () => {
  it("automatic assignment to different nodes when creating multiple vm's", () => {

  });
})

// TODO: Create volume require storage class
describe.skip('VM clone Validation', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  /**
   * https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-existing-volume/
   */
  it('Create VM with existing volume', () => {
    const namespace = 'default'
    const VM_NAME = 'use-existing-volume';

    const volumeValue = {
      name: 'existing-volume',
      size: "10",
      namespace
    };

    vms.deleteVMFromStore(`${namespace}/${VM_NAME}`);
    volumes.deleteFromStore(`${namespace}/${volumeValue.name}`); // Delete the previously created volume

    volumes.create(volumeValue); // create volume

    // create VM use existing volume
    vms.goToCreate();

    const imageEnv = Cypress.env('image');
    
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }, {
      buttonText: 'Add Volume',
      size: 12,
      create: true,
    }, {
      buttonText: 'Add Existing Volume',
      create: true,
      volume: 'existing-volume'
    }];

    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('2', '4');
    vms.setVolumes(volume);
    vms.save();

    volumes.goToList();
    volumes.checkVMAttached('default', 'existing-volume', 'use-existing-volume');
  })

  it('Clone VM from Virtual Machine list that was created from existing volume (Depends on the previous case)', () => {
    const VM_NAME = 'use-existing-volume';

    cy.login({url: PageUrl.virtualMachine});
    vms.goToList();

    vms.clickCloneAction(VM_NAME);

    vms.setNameNsDescription(`repeat-${VM_NAME}`, 'default');
    cy.get('.cru-resource-footer').contains('Create').click();
    cy.get('#cru-errors').contains('the volume existing-volume is already used by VM');
  });
})

describe('VM runStategy Validation (Halted)', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  const namespace = 'default'

  it('Craete VM use Halted (Run Strategy)', () => {
    vms.goToCreate();

    const imageEnv = Cypress.env('image');
    
    const VM_NAME = 'vm-halted';
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    const advancedOption = {
      runStrategy: 'Halted'
    };

    vms.deleteVMFromStore(`${namespace}/${VM_NAME}`)
    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('2', '4');
    vms.setVolumes(volume);
    vms.setAdvancedOption(advancedOption);
    vms.save();

    // TODO Verify VM is Off, Wait for other pr
  });
})

describe('All Namespace filtering in VM list', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.namespace});
  });

  // https://harvester.github.io/tests/manual/_incoming/2578-all-namespace-filtering/  
  // TODO: rancher cluster
  it.only('Test Namespace filter', () => {
    const namespace = 'test'

    // create a new namespace
    namespaces.deleteFromStore(namespace);
    namespaces.goToCreate();
    namespaces.setNameDescription(namespace);
    namespaces.save();

    // create vm in test namespace
    const imageEnv = Cypress.env('image');
    
    const VM_NAME = 'namespace-test';
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    vms.goToCreate();
    vms.deleteVMFromStore(`${namespace}/${VM_NAME}`);
    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('1', '4');
    vms.setVolumes(volume);
    vms.save();

    // Check whether the namespace is displayed
    VmsPage.header.findNamespace(namespace);
    vms.censorInColumn(VM_NAME, 3, namespace, 4, 'Running', 2, { timeout: constants.timeout.maxTimeout, nameSelector: '.name-console a' });
  })
})
