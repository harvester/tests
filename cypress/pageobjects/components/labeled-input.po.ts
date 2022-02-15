import ComponentPo from '@/pageobjects/components/component.po';

export default class LabeledSelectPo extends ComponentPo {
  input(string: string | undefined) {
    if (string) {
      this.self().type(string)
    }

    return
  }
}
