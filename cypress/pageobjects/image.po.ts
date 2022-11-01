import { Constants } from "@/constants/constants";
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import { VolumePage } from "@/pageobjects/volume.po";

const constants = new Constants();
const volumes = new VolumePage();

interface ValueInterface {
  namespace?: string,
  name: string,
  description?: string,
  url?: string,
  size?: string,
  path?: string,
  labels?: any,
}

export class ImagePage extends CruResourcePo {
  private downloadOrUploadRadios: string = '.radio-group';
  private fileButton: string = '#file';
  private deleteButton: string = '.card-container.prompt-remove';

  constructor() {
    super({
      type: HCI.IMAGE
    });
  }

  url() {
    return new LabeledInputPo('.labeled-input', `:contains("URL")`);
  }

  public goToCreate() {
    this.goToList();
    cy.contains('Create').click();
  }

  public goToEdit(name: string) {
    this.goToList();
    cy.get(this.searchInput).type(name);
    const image = cy.contains(name);

    image.should('be.visible')
    image.parentsUntil('tbody', 'tr').find('.icon-actions').click();
    cy.get(this.actionMenu).contains('Edit Config').click();
  }

  goToDetail(name: string) {
    const image = cy.contains(name);
    image.should('be.visible');
    image.click();
  }

  public addLabels(value: ValueInterface) {
    if (!value.labels) {
      return;
    }

    const keys = Object.keys(value.labels);

    cy.get('.tab#labels').click();
    keys.forEach((key, index) => {
      cy.contains('Add Label').click();
      cy.get('.kv-item.key input').eq(-1).type(key);
      cy.get('.kv-item.value input').eq(-1).type(value.labels[key]);
    });
  }

  public create(value: ValueInterface) {
    this.setValue(value);
    if (value?.labels) {
      this.addLabels(value);
    }
    this.save();
  }

  public edit(value: ValueInterface, upload: boolean = false) {
    if (!upload) {
      this.url().self().find('input').should('be.disabled')
    }

    this.description().input(value?.description);
    this.addLabels(value);
    this.save({ edit: true });
  }

  public createFromUpload(value: ValueInterface) {
    this.setValue(value);
    cy.get(this.downloadOrUploadRadios).contains('File').click();
    cy.get(this.fileButton).selectFile(value.path || '', { force: true });
    this.addLabels(value);
    this.save({ upload: true });
  }

  public exportImage(vmName: string, imageName: string) {
    volumes.goToList();
    cy.get(this.searchInput).type(vmName);

    const volume = cy.contains(vmName);

    volume.should('be.visible')

    // Get volume name from attahched VM in name field of Volume page
    volume.parentsUntil('tbody', 'tr').find('td').eq(2).invoke('text').then((volumeName) => {
      volumes.exportImage(volumeName.trim(), imageName);
    });
  }

  public checkState(value: ValueInterface, valid: boolean = true) {
    cy.get(this.searchInput).type(value.name);

    // state indicator for image upload progress percentage bar
    cy.contains(value.name).parentsUntil('tbody', 'tr').find('td.col-image-percentage-bar').contains(valid ? 'Completed' : '0%', { timeout: constants.timeout.uploadTimeout }).should('be.visible');
    // state indicator for status of image upload status e.g. active or uploading
    cy.contains(value.name).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Failed', { timeout: constants.timeout.uploadTimeout }).should('be.visible');
  }

  public save( { upload, edit, depth }: { upload?: boolean; edit?: boolean; depth?: number; } = {} ) {
    cy.intercept(edit? 'PUT' : 'POST', `/v1/harvester/harvesterhci.io.virtualmachineimages${ upload ? '/*' : edit ? '/*/*' : '' }`).as('createImage');
    cy.get('.cru-resource-footer').contains(!edit ? 'Create' : 'Save').click();
    cy.wait('@createImage').then(res => {
      if (edit && res.response?.statusCode === 409 && depth === 0) {
        this.save({ upload, edit, depth: depth + 1})
      } else {
        expect(res.response?.statusCode, `Check save success`).to.equal( edit ? 200 : 201 );
      }
    });
  }

  public setValue(value: ValueInterface) {
    this.name().input(value?.name);
    this.url().input(value?.url);
    this.description().input(value?.description);
  }

  public delete(name: string) {
    this.goToList();
    this.clickAction(name, 'Delete')

    cy.intercept('DELETE', '/v1/harvester/harvesterhci.io.virtualmachineimages/*/*').as('delete');
    cy.get(this.confirmRemove).contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode, `Delete ${this.type}`).to.be.oneOf([200, 204]);
    })
  }
}
