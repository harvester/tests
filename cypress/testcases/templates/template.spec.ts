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
    const value = {
      name: NAME,
      cpu: '2',
      memory: '4',
      namespace,
    }

    templates.create(value, true);

    templates.delete(namespace, NAME)
  });
});
