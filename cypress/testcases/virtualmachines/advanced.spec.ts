import YAML from 'js-yaml'

import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { LoginPage } from "@/pageobjects/login.po";
import { generateName } from '@/utils/utils';


const vms = new VmsPage();
const login = new LoginPage();

describe('Create a new VM and add Enable USB tablet option', () => { 
  beforeEach(() => {
    cy.login();
  });

  it('Create a new VM with USB tablet checked', () => {
    const VM_NAME = generateName('test-usb-tablet')
    const NAMESPACE = 'default'

    vms.goToCreate();
    
    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
      usbTablet: true,
      namespace: NAMESPACE,
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

    vms.deleteProgramlly(`${NAMESPACE}/${VM_NAME}`)
  })
})

describe("Create a new VM and add Install guest agent option", () => {
  beforeEach(() => {
    cy.login();
  });

  it('Create a new VM with Install guest agent checked', () => {
    const VM_NAME = generateName('test-guest-agent')
    const NAMESPACE = 'default'

    vms.goToCreate();

    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
      guestAgent: true,
      namespace: NAMESPACE,
    }
    vms.setValue(value);

    vms.save();

    vms.goToConfigDetail(VM_NAME);

    cy.get('.tab#advanced').click()
    vms.usbTablet().expectChecked()

    vms.deleteProgramlly(`${NAMESPACE}/${VM_NAME}`)
  })
})

describe("Verify Booting in EFI mode checkbox", () => {
  beforeEach(() => {
    cy.login();
  });

  it('Create a new VM with Booting in EFI mode checked', () => {
    const VM_NAME = generateName('test-efi')
    const NAMESPACE = 'default'

    const imageEnv = Cypress.env('image');

    const value = {
      name: VM_NAME,
      cpu: '2',
      memory: '4',
      image: imageEnv.name,
      efiEnabled: true,
      namespace: NAMESPACE,
    }

    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');

    vms.create(value);

    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode, 'Check create VM').to.equal(201);
      expect(res.response?.body?.spec?.template?.spec?.domain?.features?.smm?.enabled, 'Check smm.enabled').to.equal(false);
      expect(res.response?.body?.spec?.template?.spec?.domain?.firmware?.bootloader?.efi?.secureBoot, 'Check efi.secureBoot').to.equal(false);
    })

    vms.goToConfigDetail(VM_NAME);

    cy.get('.tab#advanced').click()
    vms.efiEnabled().expectChecked()

    vms.deleteProgramlly(`${NAMESPACE}/${VM_NAME}`)
  })
}) 
