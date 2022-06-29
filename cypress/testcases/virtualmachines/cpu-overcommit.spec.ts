import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";
import SidebarPage from "@/pageobjects/sidebar.po";
import SettingsPage from "@/pageobjects/settings.po";

import { generateName } from '@/utils/utils';

const vms = new VmsPage();
const login = new LoginPage();
const settings = new SettingsPage();
const sidebar = new SidebarPage();

/**
 * 1. Login
 * 2. Navigate to Advanced Settings
 * 3. Edit overcommit-config
 * 4. The field of CPU should be editable
 * 5. Created VM cpu reserved should be CPU / <overcommit-CPU> * 100m
*/
describe('Update Overcommit configuration', () => {
  beforeEach(() => {
    cy.login();
  });

  it('Edit overcommit-config cpu', () => {
    const VM_NAME = generateName('test-cpu-overcommit')
    const NAMESPACE = 'default'

    settings.goTo();
    settings.checkIsCurrentPage();
    settings.clickMenu('overcommit-config', 'Edit Setting', 'overcommit-config')

    settings.setOvercommit({
      cpu: '2000',
    })

    settings.update('overcommit-config');

    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: Cypress._.toLower(imageEnv.name),
      namespace: NAMESPACE,
    }

    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');

    vms.create(value);

    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode).to.equal(201);
      expect(res.response?.body?.spec?.template?.spec?.domain?.resources?.requests?.cpu).to.equal('100m');
    })

    vms.delete(NAMESPACE, VM_NAME)
  })
});
