import { HCI } from '@/constants/types';
import { generateName } from '@/utils/utils';
import templatePage from "@/pageobjects/template.po";

const templates = new templatePage();

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
    templates.goToList();
    templates.goToCreate();
    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('2', '4');
    templates.save({namespace});
    templates.delete(namespace, NAME);
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
    templates.setBasics('2', '4');
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
});
