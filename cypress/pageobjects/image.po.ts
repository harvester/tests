import PagePo from '@/utils/components/page.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  url: string,
}

export default class ImagePage extends PagePo {
  static url: string = `${Cypress.env('baseUrl')}dashboard/c/local/harvester/harvesterhci.io.virtualmachineimage`

  constructor() {
    super(ImagePage.url);
  }

  public goToList() {
    cy.visit(ImagePage.url);
    cy.intercept('GET', '/v1/harvester/harvesterhci.io.virtualmachineimages').as('goToImageList');
    cy.wait('@goToImageList')
    expect(cy.url().should('eq', ImagePage.url));
  }

  public goToCreate() {
    this.goToList()
    cy.contains('Create').click()
  }

  public save() {
    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachineimage/*').as('createImage');
    cy.get('.cru-resource-footer').contains('Create').click()
    cy.wait('@createImage').then(res => {
      expect(res.response?.statusCode).to.equal(201);
    })
  }

  public setValue(value: ValueInterface) {
    this.url().input(value?.name)
  }

  url() {
    return new LabeledInputPo('.labeled-input', `:contains("URL")`)
  }
}
