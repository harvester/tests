import { Constants } from "../constants/constants";
import LabeledSelectPo from '../utils/components/labeled-select.po';
import LabeledInputPo from '../utils/components/labeled-input.po';
const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  cpu?: string,
  memory?: string,
  image?: string,
  network?: string,
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
    cy.contains('Create').click()
    cy.intercept('GET', '/v1/harvester/harvesterhci.io.virtualmachineimages').as('loadVMCreate');
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
    cy.get('.tab#Network').click()
    this.network().select(value?.network)
  }

  public save() {
    cy.intercept('POST', '/v1/harvester/kubevirt.io.virtualmachines/default').as('createVM');
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
    return new LabeledSelectPo('section .labeled-select.create', `:contains("Network")`)
  }
}
