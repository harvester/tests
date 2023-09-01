import ComponentPo from '@/utils/components/component.po';

export default class CheckboxPo extends ComponentPo {
  check(newValue: boolean | undefined) {
    if (typeof newValue === 'undefined') {
      return
    }

    this.self().find('[role="checkbox"]').invoke('attr', 'aria-checked').then(isChecked => {
      if ((newValue && !Boolean(isChecked)) || (!newValue && Boolean(isChecked))) {
        this.self().click()
      }
    })

    return
  }

  value() {
    return Boolean(this.self().find('[role="checkbox"]').invoke('attr', 'aria-checked'))
  }
  
  expectChecked() {
    return this.self().find('[role="checkbox"]').invoke('attr', 'aria-checked').should('eq', 'true')
  }

  expectUnchecked() {
    return this.self().find('[role="checkbox"]').invoke('attr', 'aria-checked').should('eq', undefined)
  }

  click() {
    return this.self().click()
  }
}
