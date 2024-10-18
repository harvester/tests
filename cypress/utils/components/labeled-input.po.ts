import ComponentPo from './component.po';

export default class LabeledInputPo extends ComponentPo {
  input(string: string | undefined) {
    if (string) {
      this.self().find('input').clear({ force: true })
      this.self().first().type(string)
    }

    return
  }
}
