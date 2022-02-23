import { Constants } from "@/constants/constants";
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledInputPo from '@/utils/components/labeled-input.po';
import CheckboxPo from '@/utils/components/checkbox.po';
import ImagePage from "@/pageobjects/image.po";
import { find } from "cypress/types/lodash";

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
}

export class VmsPage {
  public goToList() {
    cy.visit(constants.vmPage);
    cy.intercept('GET', '/v1/harvester/kubevirt.io.virtualmachines').as('loadVM');
    cy.wait('@loadVM')
    expect(cy.url().should('eq', constants.vmPage));
  }

  public goToCreate() {
    this.goToList()
    cy.intercept('GET', '/v1/harvester/configmaps').as('loadVMCreate');
    cy.contains('Create').click()
    cy.wait('@loadVMCreate')
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
  }

  public save() {
    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/*').as('createVM');
    cy.get('.cru-resource-footer').contains('Create').click()
    cy.wait('@createVM').then(res => {
      expect(res.response?.statusCode).to.equal(201);
    })
  }

  namespace() {
    return new LabeledSelectPo('.labeled-select', `:contains("Namespace")`)
  }

  name() {
    return new LabeledInputPo('.namespace-select > .labeled-input', `:contains("Name")`)
  }

  description() {
    return new LabeledInputPo('.labeled-input', `:contains("Description")`)
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
    cy.intercept('GET', `/v1/harvester/harvesterhci.io.virtualmachineimages`).as('getImages');

    image.goToList();
    
    cy.wait('@getImages').then(res => {
      expect(res.response?.statusCode).to.equal(200);
      const images = res.response?.body?.data || []
      const name = 'ubuntu-18.04-server-cloudimg-amd64.img'
      const url = 'https://cloud-images.ubuntu.com/releases/bionic/release/ubuntu-18.04-server-cloudimg-amd64.img'
      const imageFound = images.find((i:any) => i?.spec?.displayName === 'ubuntu-18.04-server-cloudimg-amd64.img')

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

  public create(value: ValueInterface) {
    this.init()
    this.goToCreate();
    this.setValue(value);
    this.save();
  }

  public delete(name: string) {
    this.goToList()
    cy.get('.search').type(name)
    const vm = cy.contains(name)
    expect(vm.should('be.visible'))
    vm.parentsUntil('tbody', 'tr').click()
    cy.contains('Delete').click()

    cy.intercept('DELETE', `/v1/harvester/kubevirt.io.virtualmachines/*/${name}?*`).as('delete');
    cy.get('.card-container.prompt-remove').contains('Delete').click();
    cy.wait('@delete').then(res => {
      expect(res.response?.statusCode).to.equal(200);
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
}
