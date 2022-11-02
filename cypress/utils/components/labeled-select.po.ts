import ComponentPo from './component.po';

interface SelectArg {
  option: string | undefined,
  index?: number,
  selector?: string,
}
export default class LabeledSelectPo extends ComponentPo {
  select(args: SelectArg):any {
    if (args.option) {
      if (args.index !== undefined) {
        this.self().eq(args.index).click()
      } else {
        this.self().click()
      }
      
      if (args.selector) {
        cy.get(args.selector).contains(args.option).click()
      } else {
        cy.contains(args.option).click()
      }
    }

    return
  }

  text() {
    return this.self().find('.vs__selected').invoke('text')
  }
}
