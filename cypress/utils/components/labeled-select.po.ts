import ComponentPo from './component.po';

export default class LabeledSelectPo extends ComponentPo {
  select(option: string | undefined) {
    if (option) {
      this.self().click()
      cy.contains(option).click()
    }

    return
  }

  text() {
    return this.self().find('.vs__selected').invoke('text')
  }
}
