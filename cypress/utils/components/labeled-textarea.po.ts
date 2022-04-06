import ComponentPo from './component.po';

export default class LabeledTextAreaPo extends ComponentPo {
  input(string: string | undefined, options?: any) {
    if (string) {
      this.self().find('textarea').clear()
      this.self().type(string, options)
    }

    return
  }
}
