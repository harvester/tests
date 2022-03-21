import { Constants } from "@/constants/constants";
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

export class ImagePage {
  name() {
    return new LabeledInputPo('.namespace-select > .labeled-input', `:contains("Name")`)
  }

  url() {
    return new LabeledInputPo('.labeled-input', `:contains("URL")`);
  }

  description() {
    return new LabeledInputPo('.labeled-input', `:contains("Description")`)
  }

  public goToList() {
    // cy.get('.nav').contains('Images').click();
    cy.visit(constants.imagePage);
    cy.intercept('GET', '/v1/harvester/harvesterhci.io.virtualmachineimages').as('goToImageList');
    cy.wait('@goToImageList');
    cy.url().should('eq', constants.imagePage);
  }

  public goToCreate() {
    this.goToList();
    cy.contains('Create').click();
  }

  public goToEdit(name: string) {
    this.goToList();
    cy.get('.search').type(name);
    const image = cy.contains(name);

    image.should('be.visible')
    image.parentsUntil('tbody', 'tr').find('.icon-actions').click();
    cy.get('.list-unstyled.menu').contains('Edit Config').click();
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
      cy.get('.kv-item.key input').eq(index).type(key);
      cy.get('.kv-item.value textarea').eq(index).type(value.labels[key]);
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
    cy.get('.radio-group').contains('File').click();
    cy.get('#file').selectFile(value.path, { force: true });
    this.addLabels(value);
    this.save({ upload: true });
  }

  public exportImage(vmName: string, imageName: string) {
    volumes.goToList();
    cy.get('.search').type(vmName);

    const volume = cy.contains(vmName);

    volume.should('be.visible')

    volume.parentsUntil('tbody', 'tr').find('td').eq(2).invoke('text').then((volumeName) => {
      volumes.exportImage(volumeName.trim(), imageName);
    });
  }

  public checkState(value: ValueInterface, valid: boolean = true) {
    cy.get('.search').type(value.name);
    cy.contains(value.name).parentsUntil('tbody', 'tr').find('td.col-image-percentage-bar').contains(valid ? 'Completed' : '0%', { timeout: 300000 }).should('be.visible');
    cy.contains(value.name).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Failed', { timeout: 300000 }).should('be.visible');

    if (valid) {
      cy.contains(value.size || 'Size need to be string').should('be.visible');
    }
  }

  // public checkImageInLH(imageName: string) {
  //   let imageId: any = null;

  //   cy.intercept('GET', '/v1/harvester/harvesterhci.io.virtualmachineimages').as('getImageList');
  //   this.goToList();

  //   cy.wait('@getImageList').then(res => {
  //     expect(res.response?.statusCode).to.equal(200);

  //     const images = res.response?.body?.data || [];

  //     imageId = images.find((image: any) => image.spec.displayName === imageName)?.id;
  //     expect(!!imageId).to.be.true;
  //   });

  //   cy.request({ method: 'GET', url: 'v1/longhorn.io.backingimages', headers: {
  //     'Content-Type': 'application/json; charset=utf-8',
  //     'accept': 'json'
  //   }}).as('getBackingImageList');

  //   cy.get('@getBackingImageList').should((response) => {
  //     const found = response.body.data.find((image: any) => imageId.replace('/', '-') === image.metadata.name);

  //     expect(found?.metadata?.state?.error).to.be.false;
  //     expect(found?.metadata?.state?.name).to.equal('active');
  //   });
  // }

  public save( { upload, edit }: { upload?: boolean; edit?: boolean } = {} ) {
    cy.intercept(edit? 'PUT' : 'POST', `/v1/harvester/harvesterhci.io.virtualmachineimages${ upload ? '/*' : edit ? '/*/*' : '' }`).as('createImage');
    cy.get('.cru-resource-footer').contains(!edit ? 'Create' : 'Save').click();
    cy.wait('@createImage').then(res => {
      expect(res.response?.statusCode).to.equal( edit ? 200 : 201 );
    });
  }

  public setValue(value: ValueInterface) {
    this.name().input(value?.name);
    this.url().input(value?.url);
    this.description().input(value?.description);
  }

  public delete(name: string) {
    this.goToList();
    cy.get('.search').type(name);
    const image = cy.contains(name);

    image.should('be.visible')
    image.parentsUntil('tbody', 'tr').click();
    cy.contains('Delete').click();

    cy.intercept('DELETE', '/v1/harvester/harvesterhci.io.virtualmachineimages/*/*').as('delete');
    cy.get('.card-container.prompt-remove').contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode).to.equal(200);
    });
  }

  
}
