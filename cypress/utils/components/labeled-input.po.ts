import ComponentPo from './component.po';

export default class LabeledSelectPo extends ComponentPo {
  input(string: string | undefined) {
    if (string) {
      this.self().find('input').clear()
      this.self().type(string)
    }

    return
  }
}
