import ComponentPo from '@/pageobjects/components/component.po';

export default class LabeledSelectPo extends ComponentPo {
  select(option: string) {
    this.self().click()
    cy.contains(option).click()

    return
  }
}
