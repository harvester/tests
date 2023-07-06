import { Constants } from "@/constants/constants";
import { HCI, PVC } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import { VolumePage } from "@/pageobjects/volume.po";
import { generateName } from '@/utils/utils';

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

  filterByLabels(labels: any = {}) {
    const keys = Object.keys(labels);

    cy.get('body').click(0,0);
    cy.get('.fixed-header-actions').contains('Filter Labels').click();
    cy.get('.filter-popup').contains('Clear All').click();
    keys.forEach((key, index) => {
      cy.get('.filter-popup').contains('Add').click();
      cy.get('.filter-popup .box').eq(index + 1).within(() => {
        const keyInput = new LabeledSelectPo('.key .unlabeled-select');
        
        keyInput.select({option: key});
        
        const valueInput = new LabeledSelectPo('.value .unlabeled-select');
        
        if (labels[key]) {
          valueInput.select({option: labels[key]});
        }
      })
    });
    
  }

  checkState({ name = '', namespace = 'default', state = 'Active', progress = 'Completed', size = '16 MB' }: {name?:string, namespace?:string, state?:string, progress?:string,size?:string} = {}) {
    this.censorInColumn(name, 3, namespace, 4, state, 2, { timeout: constants.timeout.uploadTimeout });
    this.censorInColumn(name, 3, namespace, 4, progress, 5, { timeout: constants.timeout.uploadTimeout });
    this.censorInColumn(name, 3, namespace, 4, size, 6, { timeout: constants.timeout.uploadTimeout });
  }

  public exportImage(vmName: string, imageName: string, namespace: string) {
    volumes.goToList();
    this.search(vmName);
    cy.wait(2000);
    cy.wrap('async').then(() => {
      this.table.find(vmName, 7, namespace, 4).then((index: any) => {
        if (typeof index === 'number') {
          cy.get(`[data-testid="sortable-table-${index}-row"]`).find('td').eq(2).invoke('text').then((volumeName) => {
            volumes.exportImage(volumeName.trim(), imageName);
          });
        }
      })
    })
  }

  public save( { upload, edit, depth }: { namespace?:string, buttonText?: string, upload?: boolean; edit?: boolean; depth?: number; } = {} ): Promise<string> {
    return new Promise((resolve, reject) => {
      const interceptName = generateName('create');

      cy.intercept(edit? 'PUT' : 'POST', `/v1/harvester/harvesterhci.io.virtualmachineimages${ upload ? '/*' : edit ? '/*/*' : '' }`).as(interceptName);
      cy.get('.cru-resource-footer').contains(!edit ? 'Create' : 'Save').click();
      cy.wait(`@${interceptName}`).then(async (res) => {
        if (edit && res.response?.statusCode === 409 && depth === 0) {
          await this.save({ upload, edit, depth: depth + 1})
        } else {
          expect(res.response?.statusCode, `Check save success`).to.equal( edit ? 200 : 201 );
          resolve(res.response?.body?.metadata?.name || '');
        }
      })
      .end();
    });
  }
}
