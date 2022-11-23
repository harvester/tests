import cookie from 'cookie';

import { Constants } from "@/constants/constants";
import { HCI } from '@/constants/types';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import CheckboxPo from '@/utils/components/checkbox.po';
import { ImagePage } from "@/pageobjects/image.po";
import CruResourcePo from '@/utils/components/cru-resource.po';

const constants = new Constants();
const image = new ImagePage();

interface Network {
  network?: string,
}

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  cpu?: string,
  memory?: string,
  image?: string,
  networks?: Array<Network>,
  createRunning?: boolean,
  usbTablet?: boolean,
  efiEnabled?: boolean,
}

interface Volume {
  buttonText: string,
  create?: boolean,
  [index: string]: any
}

export class VmsPage extends CruResourcePo {
  private actionButton = '.outlet .actions-container';

  constructor() {
    super({
      type: HCI.VM
    });
  }

  public goToCreate() {
    this.goToList()
    cy.get(this.actionButton).find('a').contains(' Create ').click();
  }

  setBasics(cpu?: string, memery?: string, ssh?: {id?: string, createNew?: boolean, value?: string}) {
    this.clickTab('basics');
    this.cpu().input(cpu);
    this.memory().input(memery);

    if (ssh && ssh.id) {
      new LabeledSelectPo('.labeled-select', `:contains("SSHKey")`).select({option: ssh.id});
    } else if (ssh && ssh.createNew) {
      new LabeledSelectPo('.labeled-select', `:contains("SSHKey")`).select({option: 'Create a New...'});
      new LabeledTextAreaPo('.v--modal-box .card-container .labeled-input', `:contains("SSH-Key")`).input(ssh.value, {
        delay: 0,
      });

      cy.get('.v--modal-box .card-container').contains('Create').click();
    }
  }

  setVolumes(volumes: Array<Volume>) {
    this.clickTab('Volume');
    cy.wrap('async').then(() => {
      volumes.map((volume) => {
        if (volume.create) {
          cy.get('.tab-container button').contains(volume.buttonText).click()
        }
      });

      volumes.map((volume, index) => {
        let imageEl: any;
        let volumeEl: any;
        cy.get('.info-box').eq(index).within(() => {
            if (volume.image) {
              imageEl = new LabeledSelectPo('.labeled-select', `:contains("Image")`);
            }

            if (volume.size) {
              new LabeledInputPo('.labeled-input', `:contains("Size")`).input(volume.size);
            }

            if (volume.volume) {
              volumeEl = new LabeledSelectPo('.labeled-select', `:contains("Volume")`);
            }
        }).then(() => {
          if (imageEl) {
            imageEl.select({option: volume.image});
          }

          if (volumeEl) {
            volumeEl.select({option: volume.volume});
          }
        })
      })
    })
  }

  setAdvancedOption(option: {[index: string]: any}) {
    this.clickTab('advanced');

    if (option.runStrategy) {
      new LabeledSelectPo('.labeled-select', `:contains("Run Strategy")`).select({option: option.runStrategy});
    }
  }

  clickCloneAction(name: string) {
    this.clickAction(name, 'Clone');
    new CheckboxPo('.v--modal-box .checkbox-container', `:contains("clone volume data")`).check(false);
    cy.get('.v--modal-box button').contains('Clone').click();
  }

  public setValue(value: ValueInterface) {
    this.namespace().select({option: value?.namespace})
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.cpu().input(value?.cpu)
    this.memory().input(value?.memory)
    cy.get('.tab#Volume').click()
    this.image().select({option: value?.image})
    this.networks(value?.networks)
    cy.get('.tab#advanced').click()
    this.usbTablet().check(value?.usbTablet)
    this.efiEnabled().check(value?.efiEnabled)
  }

  public save() {
    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');
    cy.get('.cru-resource-footer').contains('Create').click()
    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode).to.equal(201);
    })
  }

  cpu() {
    return new LabeledInputPo('.labeled-input', `:contains("CPU")`)
  }

  memory() {
    return new LabeledInputPo('.labeled-input', `:contains("Memory")`)
  }

  image() {
    return new LabeledSelectPo('.labeled-select', `:contains("Image")`)
  }

  deleteVMFromStore(id: string) {
    this.deleteFromStore(id); // Delete the previously created vm
    this.deleteFromStore(id, HCI.VMI); // You need to wait for the vmi to be deleted as well, because it will not be deleted until the vm is deleted
  }

  network() {
    return new LabeledSelectPo('section .labeled-select.hoverable', `:contains("Network")`)
  }

  rootDisk() {
    return cy.get(this.confirmRemove).find('.checkbox-container span[role="checkbox"].checkbox-custom');
  }

  plugVolumeCustomName() {
    return new LabeledInputPo('.labeled-input', `:contains("Name")`);
  }

  plugVolumeName() {
    return new LabeledSelectPo('.labeled-select', `:contains("Volume")`);
  }

  networks(networks: Array<Network> = []) {
    if (networks.length === 0){
      return
    } else {
      cy.get('.tab#Network').click()

      cy.get('.info-box.infoBox').then(elms => {
        if (elms?.length < networks?.length) {
          for(let i=0; i<networks?.length - elms?.length; i++) {
            cy.contains('Add Network').click()
          }
        }

        networks.map((n, idx) => {
          this.network().select({option: n?.network, index: idx})
        })
      })
    }
  }

  goToConfigDetail(name: string) {
    this.goToList();
    cy.get('.search').type(name)
    const vm = cy.contains(name)
    expect(vm.should('be.visible'))
    vm.click()

    const config = cy.get('.masthead button').contains('Config')
    expect(config.should('be.visible'));
    config.click()
    cy.url().should('contain', 'as=config')
  }

  goToYamlEdit(name: string) {
    this.goToList();

    this.clickAction(name, 'Edit YAML')
  }

  public init() {
    cy.intercept('GET', `v1/harvester/${HCI.IMAGE}s`).as('imageList');
    image.goToList();

    cy.wait('@imageList').should((res: any) => {
      expect(res.response?.statusCode, 'Check Image list').to.equal(200);
      const images = res?.response?.body?.data || []

      const imageEnv = Cypress.env('image');

      const name = Cypress._.toLower(imageEnv.name)
      const url = imageEnv.url
      const imageFound = images.find((i:any) => i?.spec?.displayName === name)

      if (imageFound) {
        return
      } else {
        image.goToCreate();
        image.setValue({
          name,
          url,
        })
        image.save()
        image.checkState({ name, size: '16 MB' });
      }
    })
  }

  public goToEdit(name: string) {
    this.goToList()
    cy.get('.search').type(name)
    const vm = cy.contains(name)
    expect(vm.should('be.visible'))
    vm.parentsUntil('tbody', 'tr').find('.icon-actions').click()

    cy.intercept('GET', `/v1/harvester/configmaps`).as('loadEdit');
    cy.get('.list-unstyled.menu').contains('Edit Config').click()
    cy.wait('@loadEdit').then(res => {
      expect(res.response?.statusCode).to.equal(200);
    })
  }

  public edit(name: string, value: ValueInterface) {
    this.init()
    this.goToEdit(name);
    this.setValue(value);
    cy.get('.cru-resource-footer').contains('Save').click()
  }

  public delete(namespace:string, name: string, { removeRootDisk }: { removeRootDisk?: boolean } = { removeRootDisk: true }) {
    cy.visit(`/harvester/c/local/${this.type}`)

    this.clickAction(name, 'Delete').then((_) => {
      if (!removeRootDisk) {
        this.rootDisk().click();
      }
    })

    cy.intercept('DELETE', `/v1/harvester/${this.realType}s/${namespace}/${name}*`).as('delete');
    cy.get(this.confirmRemove).contains('Delete').click();
    cy.wait('@delete').then(res => {
      cy.window().then((win) => {
        const id = `${namespace}/${name}`;
        super.checkDelete(this.type, id)
        expect(res.response?.statusCode, `Delete ${this.type}`).to.be.oneOf([200, 204]);
      })
    })
  }

  public plugVolume(vmName: string, volumeNames: Array<string>, namespace: string) {
    this.goToList();

    cy.wrap(volumeNames).each((V: string) => {
      this.clickAction(vmName, 'Add Volume').then((_) => {
        this.plugVolumeCustomName().input(V);
        this.plugVolumeName().select({option: V});
      })

      cy.intercept('POST', `/v1/harvester/${this.realType}s/${namespace}/${vmName}*`).as('plug');
      cy.get('.card-container').contains('Apply').click();
      cy.wait('@plug').then(res => {
        expect(res.response?.statusCode, `${this.type} plug Volume`).to.be.oneOf([200, 204]);
        cy.get('.search-box').clear();
      })
    })
  }

  public unplugVolume(vmName: string, volumeNames: any, namespace: string) {
    this.goToConfigDetail(vmName);
    cy.get('.tabs.vertical').contains('Volumes').click();

    cy.wrap(volumeNames).each((V: string, index) => {
      cy.contains('.info-box.box', V).contains('Detach Volume').click();
      cy.intercept('POST', `/v1/harvester/${this.realType}s/${namespace}/${vmName}*`).as('unplug');
      cy.get('.card-container').contains('Detach').click();
      cy.wait('@unplug').then(res => {
        expect(res.response?.statusCode, `${this.type} unplug Volume`).to.be.oneOf([200, 204]);
      })
    })
  }

  usbTablet() {
    return new CheckboxPo('.checkbox-container', `:contains("Enable USB Tablet")`)
  }

  efiEnabled() {
    return new CheckboxPo('.checkbox-container', `:contains("Booting in EFI mode")`)
  }

  deleteProgramlly(id:string) {
    const { CSRF } = cookie.parse(document.cookie);

    cy.request({
      url: `/v1/harvester/${HCI.VM}s/${ id }`,
      headers: {
        accept: 'application/json',
        'x-api-csrf': CSRF,
      },
      method: 'DELETE',
    }).then(res => {
      expect(res.status).to.equal(200);
    })
  }
}
