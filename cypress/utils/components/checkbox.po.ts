import ComponentPo from '@/utils/components/component.po';

export default class CheckboxPo extends ComponentPo {
  check(newValue: boolean | undefined) {
    if (typeof newValue === 'undefined') {
      return
    }

    const value = this.value()

    if (newValue !== value) {
      this.self().click()
    }

    return
  }

  value() {
    return Boolean(this.self().find('input').invoke('attr', 'value'))
  }
}
