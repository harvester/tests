import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';

const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  image?: string,
  size?: string,
}

export class VolumePage {
  private search: string = '.search';
  private actionMenu: string = '.list-unstyled.menu';
  private exportImageActions: string = '.card-actions';
  private deleteButton: string = '.card-container.prompt-remove';

  name() {
    return new LabeledInputPo('.namespace-select > .labeled-input', `:contains("Name")`)
  }

  description() {
    return new LabeledInputPo('.labeled-input', `:contains("Description")`)
  }

  exportImageName() {
    return new LabeledInputPo('.card-container .labeled-input', `:contains("Name")`)
  }

  source() {
    return new LabeledSelectPo('.labeled-select', `:contains("Source")`)
  }

  size() {
    return new LabeledInputPo('.labeled-input', `:contains("Size")`)
  }

  image() {
    return new LabeledSelectPo('.labeled-select', `:contains("Image"):last`)
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

  public create(value: ValueInterface) {
    this.goToCreate();
    this.setValue(value);
    this.save();
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

  public checkState(value: ValueInterface) {
    // state indicator for status of volume status e.g. Ready
    cy.contains(value.name || '').parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter .bg-success').contains('Ready').should('be.visible');
  }

  public setValue(value: ValueInterface) {
    if (!!value.image) {
      this.source().select('VM Image');
      this.image().select(value?.image);
    }

    this.name().input(value?.name);
    this.size().input(value?.size);
  }

  public save( { edit }: { edit?: boolean } = {} ) {
    cy.intercept(edit? 'PUT' : 'POST', `/v1/harvester/persistentvolumeclaims${ edit ? '/*/*' : '' }`).as('createVolume');
    cy.get('.cru-resource-footer').contains(!edit ? 'Create' : 'Save').click();
    cy.wait('@createVolume').then(res => {
      expect(res.response?.statusCode).to.equal( edit ? 200 : 201 );
    });
  }

  public delete(name: string) {
    this.goToList();
    cy.get(this.search).type(name);
    const volume = cy.contains(name);

    volume.should('be.visible')
    volume.parentsUntil('tbody', 'tr').click();
    cy.contains('Delete').click();

    cy.intercept('DELETE', '/v1/harvester/persistentvolumeclaims/*/*').as('delete');
    cy.get(this.deleteButton).contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode).to.equal(200);
    });
  }

  public checkStateByVM(vmName: string) {
    this.goToList();
    cy.get(this.search).type(vmName);

    const volume = cy.contains(vmName);

    volume.should('be.visible');

    // Get volume name from attahched VM in name field of Volume page
    volume.parentsUntil('tbody', 'tr').find('td').eq(2).invoke('text').then((volumeName) => {
      this.checkState({name: volumeName.trim()});
    });
  }

  public deleteVolumeByVM(vmName: string) {
    this.goToList();
    cy.get(this.search).type(vmName);

    const volume = cy.contains(vmName);

    volume.should('be.visible');

    // Get volume name from attahched VM in name field of Volume page
    volume.parentsUntil('tbody', 'tr').find('td').eq(2).invoke('text').then((volumeName) => {
      this.delete(volumeName.trim());
    });
  }

}
