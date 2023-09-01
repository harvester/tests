import CruResourcePo from '@/utils/components/cru-resource.po';
import { MANAGEMENT } from '@/constants/types'
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import RadioButtonPo from '@/utils/components/radio-button.po';

export default class ProjectPo extends CruResourcePo {
  constructor() {
    super({
      type: MANAGEMENT.PROJECT
    });
  }

  public setValue(value: any) {
    this.name().input(value?.name)
  }

  public create(value: any, urlWithNamespace?: boolean) {
    cy.visit(`/harvester/c/${Cypress.config('clusterId')}/${this.type}/create`)

    this.setValue(value)
    this.addMember(value?.members)

    this.save()
  }

  public selectMember() {
    return new LabeledSelectPo('.labeled-select.hoverable', `:contains("Select Member")`)
  }

  public clusterPermissions() {
    return new RadioButtonPo('.radio-group')
  }

  public addMember(members: object[] = []) {
    members.map(member => {
      cy.contains('Add').click()

      this.selectMember().search(member.name)
      this.selectMember().select({ option: member.name })

      this.clusterPermissions().input(member?.permissions)

      cy.get('[data-testid="card-actions-slot"]').contains('Add').click()
    })
  }

  public save({
    buttonText = 'save',
    edit,
  } : {
    buttonText?:string,
    edit?: boolean;
  } = {}) {
    cy.intercept('POST', `/v3/projects`).as('createProject');
    
    this.clickFooterBtn(buttonText)
    cy.wait('@createProject').then(res => {
      expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
    })
  }
}
