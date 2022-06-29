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

  public goToList() {
    cy.visit(constants.vmPage);

    cy.get(this.sideBar).find('li').contains('Virtual Machines').click();
    cy.get(this.pageHead).then($el => {
      cy.url().should('exist', constants.vmPage);
    })
  }

  public goToCreate() {
    this.goToList()
    cy.get(this.actionButton).find('a').contains(' Create ').click();
  }

  public setValue(value: ValueInterface) {
    this.namespace().select(value?.namespace)
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.cpu().input(value?.cpu)
    this.memory().input(value?.memory)
    cy.get('.tab#Volume').click()
    this.image().select(value?.image)
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
          this.network().select(n?.network, idx)
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

  goToYamlDetail(name: string) {
    this.goToList();
    cy.get('.search').type(name)
    const vm = cy.contains(name)
    expect(vm.should('be.visible'))
    vm.click()

    const config = cy.get('.masthead button').contains('YAML')
    expect(config.should('be.visible'));
    config.click()
    cy.url().should('contain', 'as=yaml')
  }

  public init() {
    image.goToList();
    cy.request({
      url: `v1/harvester/${HCI.IMAGE}s`,
      headers: {
        accept: 'application/json'
      }
    }).as('imageList')

    cy.get('@imageList').should((res: any) => {
      expect(res?.status, 'Check Image list').to.equal(200);
      const images = res?.body?.data || []

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

  usbTablet() {
    return new CheckboxPo('.checkbox-container', `:contains("Enable USB Tablet")`)
  }

  efiEnabled() {
    return new CheckboxPo('.checkbox-container', `:contains("Booting in EFI mode ")`)
  }

  deleteProgramlly(id:string) {
    cy.window().then((win:any) => {
      const vm = win.byId(HCI.VM, id, 'harvester')

      cy.intercept('DELETE', `/v1/harvester/${ HCI.VM }s/${ id }`).as('delete');
      vm.remove()
      cy.wait('@delete').then(res => {
        expect(res.response?.statusCode).to.equal(200);
      })
    })
  }
}
