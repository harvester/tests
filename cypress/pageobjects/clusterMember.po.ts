import CruResourcePo from '@/utils/components/cru-resource.po';
import { MANAGEMENT } from '@/constants/types'
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import RadioButtonPo from '@/utils/components/radio-button.po';

export default class UserPo extends CruResourcePo {
  constructor() {
    super({
      type: MANAGEMENT.CLUSTER_ROLE_TEMPLATE_BINDING
    });
  }

  public selectMember() {
    return new LabeledSelectPo('.labeled-select.hoverable', `:contains("Select Member")`)
  }

  public clusterPermissions() {
    return new RadioButtonPo('.radio-group')
  }

  public setValue(value: any) {
    this.selectMember().search(value?.selectMember)
    this.selectMember().select({ option: value?.selectMember })

    this.clusterPermissions().input(value?.clusterPermissions)
  }

  public create(value: any, urlWithNamespace?: boolean) {
    cy.visit(`/harvester/c/${Cypress.config('clusterId')}/${this.type}/create`)

    this.setValue(value)

    this.save()
  }

  public save({
    buttonText = 'save',
    edit,
  } : {
    buttonText?:string,
    edit?: boolean;
  } = {}) {
    cy.intercept('POST', `/v3/clusterroletemplatebindings`).as('createClusterMember');
    
    this.clickFooterBtn(buttonText)
    cy.wait('@createClusterMember').then(res => {
      expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
    })
  }
}
