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
  let interceptionCount = 0;

  beforeEach(() => {
    cy.login();
  });

  it('Create a vm template with the required values', () => {
    cy.intercept('POST', `v1/harvester/${HCI.VM_VERSION}s/default`).as('create');

    templates.goToList();
    templates.goToCreate();
    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('2', '4');
    templates.save({namespace});

    cy.wait('@create').should((res: any) => {
      expect(res.response?.statusCode, 'Create VM Template').to.equal(201);
      const version = res?.response?.body || {}
      const versionName = version?.metadata?.name || '';

      templates.hasAction({
        name: versionName,
        ns: namespace,
        action: 'Delete',
        expect: false,
      })

      templates.clickAction(versionName, 'Modify template (Create new version)');
    });
    
    
    cy.intercept('POST', `v1/harvester/${HCI.VM_VERSION}s/default`).as('create');
    
    templates.setBasics('1', '2');
    templates.save({namespace});

    cy.wait('@create').should((res: any) => {
      expect(res.response?.statusCode, 'Create VM Template').to.equal(201);
      const version = res?.response?.body || {}
      const versionName = version?.metadata?.name || '';

      templates.hasAction({
        name: versionName,
        ns: namespace,
        action: 'Delete',
      })
    });

    templates.delete(namespace, NAME);
  });
});
