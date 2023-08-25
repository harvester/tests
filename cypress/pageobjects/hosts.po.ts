import { Constants } from "../constants/constants";
const constants = new Constants();
import CruResourcePo from '@/utils/components/cru-resource.po';
import { HCI } from '@/constants/types'
import LabeledInputPo from '@/utils/components/labeled-input.po';

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  customName?: string,
  consoleUrl?: string,
}

export class HostsPage extends CruResourcePo {
  private hostList = '.host-list';
  private actionsDropdown = '.role-multi-action';
  private editButton = '.icon-edit';
  private editYamlButton = '.icon-file';

  constructor() {
    super({
      type: HCI.HOST,
      realType: 'node',
    });
  }

  public navigateHostsPage() {
    cy.visit(constants.hostsPage);
  }

  public editHosts() {
    this.navigateHostsPage();
    cy.get(this.actionsDropdown).first().click();
    cy.get(this.editButton).click();
  }

  public editHostsYaml() {
    this.navigateHostsPage();
    cy.get(this.actionsDropdown).first().click();
    cy.get(this.editYamlButton).click();
  }

  customName() {
    return new LabeledInputPo('.labeled-input', `:contains("Custom Name")`)
  }

  consoleUrl() {
    return new LabeledInputPo('.labeled-input', `:contains("Console URL")`)
  }

  setValue(value:ValueInterface) {
    this.customName().input(value.customName)
    this.consoleUrl().input(value.consoleUrl)
  }

  checkBasicValue(name: string, options: {
    customName?: string,
    consoleUrl?: string,
  }) {
    this.goToEdit(name);

    if (options?.customName) {
      cy.get('.labeled-input').contains('Custom Name').next().should('have.value', options.customName);
    }

    if (options?.consoleUrl) {
      cy.get('.labeled-input').contains('Console URL').next().should('have.value', options.consoleUrl);
    }
  }

  enableMaintenance(name:string) {
    cy.intercept('POST', `/v1/harvester/${this.realType}s/${name}?action=enableMaintenanceMode`).as('enable');
    this.clickAction(name, 'Enable Maintenance Mode');
    // Maintenance
    cy.get('.card-container').contains('Apply').click();
    cy.wait('@enable').then(res => {
      expect(res.response?.statusCode, `Enable maintenance ${name}`).to.equal(204);
    })
  }

  public update(id:string) {
    const saveButtons = '.buttons > .right'
    
    cy.intercept('PUT', `/v1/harvester/${this.realType}s/${id}`).as('update');
    cy.get(saveButtons).contains('Save').click()
    cy.wait('@update').then(res => {
      expect(res.response?.statusCode, `Check edit ${id}`).to.equal(200);
    })
  }
}
