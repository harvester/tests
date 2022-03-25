import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';

const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  source?: string,
  image?: string,
  size?: string,
}

export class VolumePage {
  private search: string = '.search';
  private actionMenu: string = '.list-unstyled.menu';
  private exportImageActions: string = '.card-actions';

  name() {
    return new LabeledInputPo('.namespace-select > .labeled-input', `:contains("Name")`)
  }

  description() {
    return new LabeledInputPo('.labeled-input', `:contains("Description")`)
  }

  exportImageName() {
    return new LabeledInputPo('.card-container .labeled-input', `:contains("Name")`)
  }

  public goToList() {
    // cy.get('.nav').contains('Volumes').click();
    cy.visit(constants.volumePage)
    cy.intercept('GET', '/v1/harvester/persistentvolumeclaims').as('goToVolumeList');
    cy.wait('@goToVolumeList');
    cy.url().should('eq', constants.volumePage)
  }

  public goToCreate() {
    this.goToList();
    cy.contains('Create').click();
  }

  public goToEdit(name: string) {
    this.goToList();
    cy.get(this.search).type(name);
    const volume = cy.contains(name);

    volume.should('be.visible')
    volume.parentsUntil('tbody', 'tr').find('.icon-actions').click();
    cy.get(this.actionMenu).contains('Edit Config').click();
  }

  goToDetail(name: string) {
    const volume = cy.contains(name)

    volume.should('be.visible')
    volume.click()
  }

  public exportImage(volumeName: string, imageName: string) {
    cy.contains(volumeName).parentsUntil('tbody', 'tr').find('.icon-actions').click();
    cy.get(this.actionMenu).contains('Export Image').click();
    this.exportImageName().input(imageName);

    cy.intercept('POST', `v1/harvester/persistentvolumeclaims/*/${ volumeName }?action=export`).as('exportImage');
    cy.get(this.exportImageActions).contains('Create').click();
    cy.wait('@exportImage').then(res => {
      expect(res.response?.statusCode).to.equal(200);
      expect(cy.contains('Succeed'));
    });
  }

}
