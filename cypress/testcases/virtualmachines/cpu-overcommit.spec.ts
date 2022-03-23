import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";
import { SidebarPage } from "@/pageobjects/sidebar.po";
import { SettingsPage } from "@/pageobjects/settings.po";

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

  it('Step1: Edit overcommit-config cpu', () => {
    const VM_NAME = 'test-cpu-overcommit'

    settings.goToEditSetting('overcommit-config')

    settings.setOvercommit({
      cpu: '2000',
    })

    settings.save()

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
    }

    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');

    vms.create(value);

    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode).to.equal(201);
      expect(res.response?.body?.spec?.template?.spec?.domain?.resources?.requests?.cpu).to.equal('100m');
    })

    vms.delete(VM_NAME)
  })
});
