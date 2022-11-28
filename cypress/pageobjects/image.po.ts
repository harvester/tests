import { Constants } from "@/constants/constants";
import { HCI, PVC } from '@/constants/types'
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

  setBasics({url, path} : { url?: string, path?: string }) {
    this.clickTab('basic');

    if (path) {
      cy.get(this.downloadOrUploadRadios).contains('File').click();
      cy.get(this.fileButton).selectFile(path || '', { force: true });

      return;
    }

    if (url) {
      this.url().input(url);
    }
  }

  setLabels({labels = {}} : {labels?: any}) {
    const keys = Object.keys(labels);
    
    this.clickTab('labels');
    keys.forEach((key, index) => {
      cy.contains('Add Label').click();
      cy.get('.kv-item.key input').eq(-1).type(key);
      cy.get('.kv-item.value input').eq(-1).type(labels[key]);
    });
  }

  public exportImage(vmName: string, imageName: string, namespace: string) {
    volumes.goToList();
    this.search(vmName);
    cy.wait(2000);
    cy.wrap('async').then(() => {
      this.table.find(vmName, 6, namespace, 4).then((index: any) => {
        if (typeof index === 'number') {
          cy.get(`[data-testid="sortable-table-${index}-row"]`).find('td').eq(2).invoke('text').then((volumeName) => {
            volumes.exportImage(volumeName.trim(), imageName);
          });
        }
      })
    })
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
}
