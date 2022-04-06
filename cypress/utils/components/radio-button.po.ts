import ComponentPo from './component.po';

export default class RadioButtonPo extends ComponentPo {
  input(string: string | undefined) {
    if (string) {
      this.self().parent().find('.radio-container').contains(string).click()
    }

    return
  }
}
