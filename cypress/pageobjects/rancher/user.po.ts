import CruResourcePo from '@/utils/components/cru-resource.po';
import { MANAGEMENT } from '@/constants/types'
import LabeledInputPo from '@/utils/components/labeled-input.po';
import CheckboxPo from '@/utils/components/checkbox.po';

export default class UserPo extends CruResourcePo {
  constructor() {
    super({
      type: MANAGEMENT.USER
    });
  }

  public username() {
    return new LabeledInputPo('.labeled-input', `:contains("Username")`)
  }

  public newPassword() {
    return new LabeledInputPo('.labeled-input', `:contains("New Password")`)
  }

  public confirmPassword() {
    return new LabeledInputPo('.labeled-input', `:contains("Confirm Password")`)
  }

  public globalPermissions(string) {
    return cy.find('.card-body').contains(string).click()
  }

  administrator() {
    return new CheckboxPo(':nth-child(1) > [data-testid="card"] > .card-wrap > [data-testid="card-body-slot"] > .checkbox-section > :nth-child(1) > .checkbox-outer-container > .checkbox-container', `:contains("Administrator")`)
  }

  public setValue(value: any) {
    this.username().input(value?.username)
    this.newPassword().input(value?.newPassword)
    this.confirmPassword().input(value?.confirmPassword)

    // TODO: Can not get the value of globalPermissions
    if (value?.administrator) {
      this.administrator().click()
    }
  }

  public create(value: any, urlWithNamespace?: boolean) {
    cy.visit(`/c/local/auth/${this.type}/create`)

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
    cy.intercept('POST', `/v3/users`).as('create');
    
    this.clickFooterBtn(buttonText)
    cy.wait('@create').then(res => {
      expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
    })
  }
}