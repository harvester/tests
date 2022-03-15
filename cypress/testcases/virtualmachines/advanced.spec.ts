import YAML from 'js-yaml'

import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";


const vms = new VmsPage();
const login = new LoginPage();

describe('Create a new VM and add Enable USB tablet option', () => { 
  beforeEach(() => {
    login.login();
  });

  it('Create a new VM with USB tablet checked', () => {
    const VM_NAME = 'test-usb-tablet'

    vms.goToCreate();

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      usbTablet: true,
    }
    vms.setValue(value);

    vms.save();

    vms.goToConfigDetail(VM_NAME);

    cy.get('.tab#advanced').click()
    vms.usbTablet().expectChecked()

    cy.intercept('GET', `/apis/kubevirt.io/v1/namespaces/*/virtualmachines/${VM_NAME}`).as('vmDetail');

    vms.goToYamlDetail(VM_NAME);
    
    cy.wait('@vmDetail').then(res => {
      expect(res.response?.statusCode).to.equal(200);
      const yaml = res.response?.body

      const value:any = YAML.load(yaml)
      const inputs = value?.spec?.template?.spec?.domain?.devices?.inputs || []
      const foundTablet = !!inputs.find((i:any) => i.name === 'tablet')

      expect(foundTablet).to.equal(true);
    })

    vms.delete(VM_NAME)
  })
})

describe("Create a new VM and add Install guest agent option", () => {
  beforeEach(() => {
    login.login();
  });

  it('Create a new VM with Install guest agent checked', () => {
    const VM_NAME = 'test-guest-agent'

    vms.goToCreate();

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      guestAgent: true,
    }
    vms.setValue(value);

    vms.save();

    vms.goToConfigDetail(VM_NAME);

    cy.get('.tab#advanced').click()
    vms.usbTablet().expectChecked()

    vms.delete(VM_NAME)
  })
})
