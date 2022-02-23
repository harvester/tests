import ComponentPo from './component.po';

export default class LabeledSelectPo extends ComponentPo {
  select(option: string | undefined):any;
  select(option: string | undefined, index: number):any;
  select(...args: Array<any>) {
    if (args[0]) {
      if (args[1] !== undefined) {
        this.self().eq(args[1]).click()
      } else {
        this.self().click()
      }
     
      cy.contains(args[0]).click()
    }

    return
  }

  text() {
    return this.self().find('.vs__selected').invoke('text')
  }
}
