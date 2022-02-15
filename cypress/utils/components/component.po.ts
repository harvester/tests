import { CypressChainable } from '@/utils/po.types';

export default class ComponentPo {
  public self: () => CypressChainable

  constructor(self: CypressChainable);
  constructor(selector: string, parent?: CypressChainable);// selector should be jquery.Selector
  constructor(selector: string, filter?: string, parent?: CypressChainable);
  constructor(...args: Array<any>) {
    if (typeof args[0] === 'string' && typeof args[1] === 'string') {
      const [selector, filter, parent] = args as [string, string, CypressChainable];

      this.self = () => (parent || cy).get(selector).filter(filter);
    } else if (typeof args[0] === 'string' && typeof args[0] !== 'string') {
      const [selector, parent] = args as [string, CypressChainable];

      this.self = () => (parent || cy).get(selector);
    } else {
      // Note - if the element is removed from screen and shown again this will fail
      const [self] = args as [CypressChainable];

      this.self = () => self;
    }
  }

  isDisabled(): Cypress.Chainable<boolean> {
    return this.self().invoke('attr', 'disabled').then((disabled: string) => disabled === 'disabled');
  }

  checkVisible(): Cypress.Chainable<boolean> {
    return this.self().should('be.visible');
  }
}
