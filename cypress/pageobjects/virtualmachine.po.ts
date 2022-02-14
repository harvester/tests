import { Constants } from "../constants/constants";
import LabeledSelectPo from './components/labeled-select.po';
import LabeledInputPo from './components/labeled-input.po';
const constants = new Constants();

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

  public setDefaultValue() {
    this.namespace().select('default')
    this.name().input('test-vm-name-automation')
    this.description().input('test-vm-description-automation')
    this.cpu().input('2')
    this.memory().input('4')
    cy.get('.tab#Volume').click()
    this.image().select('ubuntu-18.04-server-cloudimg-amd64.img')
    cy.get('.tab#Network').click()
    this.network().select('vlan1')
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
