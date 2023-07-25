import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { generateName } from '@/utils/utils';
import templatePage from "@/pageobjects/template.po";

const vmPO = new VmsPage();
const templates = new templatePage();

/**
 * 1. Go to Template, create a VM template with Boot in EFI mode selected.
 * 2. Go to Virtual Machines, click Create, select Multiple instance, type in a random name prefix, and select the VM template we just created.
 * 3. Create a VM with template
 * Expected Results
 * 1. Check VM setting, the booting in EFI mode is checked
*/
describe("template with EFI", () => {
  it('template with EFI', () => {
    cy.login();

    const NAME = generateName('test-efi-template')
    const namespace = 'default'
  
    templates.goToCreate()

    const imageEnv = Cypress.env('image');
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    templates.setNameNsDescription(NAME, namespace);
    templates.setBasics('1', '1')
    templates.setVolumes(volume)
    templates.setAdvancedOption({
      efiEnabled: true
    })

    templates.save({namespace})

    vmPO.goToCreate()

    vmPO.selectTemplateAndVersion({id: `${namespace}/${NAME}`, version: '1'})

    const namePrefix = 'test-multiple-efi'

    vmPO.setMultipleInstance({
      namePrefix,
      count: '3',
    })
    vmPO.setNameNsDescription(namePrefix, namespace);

    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');
    cy.intercept('POST', '/v1/harvester/secrets/*').as('createSecret');

    vmPO.save();

    for( let i=0; i<3; i++) {
      cy.wait('@createVM').then(res => {
        expect(res.response?.statusCode, 'Check create VM').to.equal(201);
        expect(res.response?.body?.spec?.template?.spec?.domain?.firmware?.bootloader?.efi?.secureBoot, 'Check efi.secureBoot').to.equal(false);
      })
      cy.wait('@createSecret').then(res => {
        expect(res.response?.statusCode, 'Check create VM secret').to.equal(201);
      })
    }

    vmPO.goToList()

    cy.get('.search').type(namePrefix)
    cy.get('tr.main-row').should($els => {
      expect($els).to.have.length(3)
    })
    cy.get('tr.main-row').each(row => {
      cy.wrap(row).find('td').eq(0).click()
      cy.get('button#promptRemove').click()
      cy.get('[data-testid="prompt-remove-confirm-button"]').click()
    })
  })
})
