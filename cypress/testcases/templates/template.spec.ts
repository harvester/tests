import { HCI } from '@/constants/types';
import { generateName } from '@/utils/utils';
import templatePage from "@/pageobjects/template.po";
import { VmsPage } from "@/pageobjects/virtualmachine.po";

const templates = new templatePage();
const vmPO = new VmsPage();

/**
 * 1. Login
 * 2. Navigate to the VM template create page
 * 3. Input required values
 * 4. Validate the create request
*/
describe('Create a vm template with all the required values', () => {
  const NAME = generateName('test-template')
  const namespace = 'default'

  beforeEach(() => {
    cy.login();
  });

  it('Create a vm template with the required values', () => {
    templates.goToCreate()
    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('1', '1')
    templates.save({namespace})

    templates.delete(namespace, NAME)
  });
});

/**
 * https://harvester.github.io/tests/manual/_incoming/2376-2379-delete-vm-template-default-version/
*/
describe('Delete VM template default version', () => {
  const NAME = generateName('test-template');
  const namespace = 'default';
  let DEFAULT_VERSION_NAME = '', NEW_VERSION_NAME = '';

  beforeEach(() => {
    cy.login();
  });

  it('Create a vm template with the required values', () => {
    cy.intercept('POST', `v1/harvester/${HCI.VM_VERSION}s/default`).as('create');

    templates.goToList();
    templates.goToCreate();
    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('1', '1');
    cy.wrap(templates.save({namespace})).then((versionName) => {
      DEFAULT_VERSION_NAME = versionName as string;

      templates.hasAction({
        name: DEFAULT_VERSION_NAME,
        ns: namespace,
        action: 'Delete',
        expect: false,
      })
  
      templates.clickAction(DEFAULT_VERSION_NAME, 'Modify template (Create new version)');
    })

    templates.setBasics('1', '2');

    cy.wrap(templates.save({namespace})).then((versionName) => {
      NEW_VERSION_NAME = versionName as string;

      templates.hasAction({
        name: NEW_VERSION_NAME,
        ns: namespace,
        action: 'Delete',
      })
    })

    templates.delete(namespace, NAME);
  });
})

/**
 * 1. Create a new VM with a template of non-default version
 * Expected Results
 * 1. After selecting appropriate template and/or version it should populate other fields
 * 2. CPU, Memory, Image, and SSH key should match saved template info
*/
describe('Create vm using a template of non-default version', () => {
  // TODO: Dependency on preset ssh key "default/preset-ssh"
  it.skip('Create vm using a template of non-default version', () => {
    cy.login();

    const NAME = generateName('test-template')
    const namespace = 'default'

    const value = {
      name: NAME,
      cpu: '1',
      memory: '1',
      namespace,
    }

    const imageEnv = Cypress.env('image');
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    templates.goToCreate()
    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('1', '1', {
      id: 'default/preset-ssh'
    })
    templates.setVolumes(volume)
    templates.save({namespace})

    vmPO.goToCreate()

    vmPO.selectTemplateAndVersion({id: `${namespace}/${NAME}`, version: '1'})

    const vmName = generateName('test-vm')

    vmPO.setNameNsDescription(vmName, namespace);

    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');
    vmPO.save();
    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode).to.equal(201);

      expect(res.response?.body?.spec?.template?.spec?.domain?.resources?.limits?.cpu, 'Check CPU').to.equal('1')
      expect(res.response?.body?.spec?.template?.spec?.domain?.resources?.limits?.memory, 'Check memory').to.equal('1Gi')
      expect(res.response?.body?.spec?.template?.metadata?.annotations?.['harvesterhci.io/sshNames'], 'Check ssh key').to.equal('["default/preset-ssh"]')

      vmPO.deleteVMFromStore(res.response?.body?.id)
      templates.deleteFromStore(`${namespace}/${NAME}`)
    })
  });
});
