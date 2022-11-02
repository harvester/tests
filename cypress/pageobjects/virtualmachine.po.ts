import cookie from 'cookie';

import { Constants } from "@/constants/constants";
import { HCI } from '@/constants/types';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import CheckboxPo from '@/utils/components/checkbox.po';
import { ImagePage } from "@/pageobjects/image.po";
import { find } from "cypress/types/lodash";
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

export class VmsPage extends CruResourcePo {
  private actionButton = '.outlet .actions-container';
  private pageHead = 'main .outlet header h1';
  private sideBar = 'nav.side-nav .list-unstyled';

  constructor() {
    super({
      type: HCI.VM
    });
  }


  public goToCreate() {
    this.goToList()
    cy.get(this.actionButton).find('a').contains(' Create ').click();
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
    this.createRunning().check(value?.createRunning)
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

  network() {
    return new LabeledSelectPo('section .labeled-select.hoverable', `:contains("Network")`)
  }

  rootDisk() {
    return new CheckboxPo('.checkbox-container', `:contains("disk-0")`)
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

  createRunning() {
    return new CheckboxPo('.checkbox-container', `:contains("Start virtual machine on creation")`)
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
        this.rootDisk().check(false);
      }
    })

    cy.intercept('DELETE', `/v1/harvester/${this.realType}s/${namespace}/${name}*`).as('delete');
    cy.get(this.confirmRemove).contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode, `Delete ${this.type}`).to.be.oneOf([200, 204]);
    })
  }

  usbTablet() {
    return new CheckboxPo('.checkbox-container', `:contains("Enable USB Tablet")`)
  }

  efiEnabled() {
    return new CheckboxPo('.checkbox-container', `:contains("Booting in EFI mode ")`)
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
