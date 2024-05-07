import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { VolumePage } from "@/pageobjects/volume.po";
import NamespacePage from "@/pageobjects/namespace.po";
import { PageUrl } from "@/constants/constants";
import { ImagePage } from "@/pageobjects/image.po";
import { generateName } from '@/utils/utils';
import { Constants } from "@/constants/constants";

const vms = new VmsPage();
const volumePO = new VolumePage();
const constants = new Constants();
const namespaces = new NamespacePage();
const imagePO = new ImagePage();

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
      cpu: '1',
      memory: '1',
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

describe('VM clone Validation', () => {
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
    volumePO.deleteFromStore(`${namespace}/${volumeValue.name}`); // Delete the previously created volume

    volumePO.create(volumeValue); // create volume

    // create VM use existing volume
    vms.goToCreate();

    const imageEnv = Cypress.env('image');
    
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
      size: 4
    }, {
      buttonText: 'Add Volume',
      size: 5,
      create: true,
    }, {
      buttonText: 'Add Existing Volume',
      create: true,
      volume: 'existing-volume'
    }];

    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('1', '1');
    vms.setVolumes(volume);
    vms.save();

    volumePO.goToList();
    volumePO.checkVMAttached('default', 'existing-volume', 'use-existing-volume');

    vms.deleteVMFromStore(`${namespace}/${VM_NAME}`);
    volumePO.deleteFromStore(`${namespace}/${volumeValue.name}`);
  })
})


describe('VM runStategy Validation (Halted)', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  const namespace = 'default'

  it('Create VM use Halted (Run Strategy)', () => {
    vms.goToCreate();

    const imageEnv = Cypress.env('image');
    
    const VM_NAME = 'vm-halted';
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
      size: 4
    }];

    const advancedOption = {
      runStrategy: 'Halted'
    };

    vms.deleteVMFromStore(`${namespace}/${VM_NAME}`)
    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('1', '1');
    vms.setVolumes(volume);
    vms.setAdvancedOption(advancedOption);
    vms.save();
    vms.checkVMState(VM_NAME, 'Off');
    vms.deleteVMFromUI(namespace, VM_NAME)
  });
})

/**
 * 1. Create vm “vm-1”
 * 2. Create a image “img-1” by export the volume used by vm “vm-1”
 * 3. Delete vm “vm-1”
 * 4. Delete image “img-1”
 * Expected Results
 * 1. Image “img-1” will be deleted
 */
export function DeleteVMWithImage() {}
describe("Delete VM with exported image", () => {
  it("Delete VM with exported image", () => {
    const VM_NAME = generateName('vm-1');
    const namespace = 'default'
  
    cy.login();
  
    const imageEnv = Cypress.env('image');
  
    const value = {
      name: VM_NAME,
      cpu: '1',
      memory: '1',
      image: Cypress._.toLower(imageEnv.name),
      namespace,
    }
  
    vms.goToCreate();
    vms.setValue(value);
  
    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');
    cy.get('.cru-resource-footer').contains('Create').click()
    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode, 'Check create VM').to.equal(201);
      const body = res.response?.body
      const volumeClaimTemplates = body?.metadata?.annotations?.['harvesterhci.io/volumeClaimTemplates']
      const volumes = JSON.parse(volumeClaimTemplates || '{}')

      const imageName = generateName('img-1'); 
      
      volumePO.goToList()
      volumePO.exportImage(volumes[0].metadata.name, imageName)
      cy.intercept('DELETE', `/v1/harvester/kubevirt.io.virtualmachines/${namespace}/${VM_NAME}*`).as('deleteVM');
      vms.delete(namespace, VM_NAME)
      cy.wait('@deleteVM').then(res => {
        expect(res.response?.statusCode, 'Delete VM').to.be.oneOf([200, 204]);
        
        imagePO.goToList()

        cy.intercept('DELETE', `/v1/harvester/harvesterhci.io.virtualmachineimages/${namespace}/*`).as('deleteImage');
        imagePO.clickAction(imageName, 'Delete')
        cy.get('[data-testid="prompt-remove-confirm-button"]').click()
        cy.wait('@deleteImage').then(res => {
          expect(res.response?.statusCode, 'Delete Image').to.be.oneOf([200, 204]); 
        })
      })
    })
  });
})

/**
 * 1. Create VM and add SSH Key
 * 2. Save VM
 * Expected Results
 * 1. You should be able to ssh in with correct SSH private key
 */
// TODO: require docker image or CI machine ssh key
describe('Edit vm and insert ssh and check the ssh key is accepted for the login', () => {
  it.skip('Edit vm and insert ssh and check the ssh key is accepted for the login', () => {
    cy.login();

    const VM_NAME = generateName('test-vm-ssh');
    const namespace = 'default'
    const imageEnv = Cypress.env('image');
    const NETWORK_1 = 'vlan1'

    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
      size: 4
    }];

    vms.goToCreate();

    vms.setNameNsDescription(VM_NAME, namespace);
    vms.setBasics('1', '1', {
      id: 'default/preset-ssh'
    });
    vms.setVolumes(volume);
    vms.networks([{
      network: NETWORK_1,
    }])

    vms.save(); 

    vms.censorInColumn(VM_NAME, 3, namespace, 4, 'Running', 2, { timeout: constants.timeout.maxTimeout, nameSelector: '.name-console a' });
    // Wait for IP address show in table
    vms.censorInColumn(VM_NAME, 3, namespace, 4, '.', 7, { timeout: constants.timeout.maxTimeout, nameSelector: '.name-console a' });

    cy.contains('tr', VM_NAME)
      .wait(10000) // Wait for system ssh port ready
      .find('[data-title="IP Address"] > div > span > .has-tooltip')
      .then($els => {
        const address = $els[0]?.innerText

        cy.task('ssh', {
          username: 'opensuse',
          host: address,
          remoteCommand: 'ls',
        })
        .then(result => {
          vms.delete(namespace, VM_NAME)
        })
      })
  })
})

describe('All Namespace filtering in VM list', () => {
  beforeEach(() => {
    cy.login({url: PageUrl.namespace});
  });

  // https://harvester.github.io/tests/manual/_incoming/2578-all-namespace-filtering/  
  // TODO: go to rancher cluster
  it('Test Namespace filter', () => {
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
      size: 4
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
