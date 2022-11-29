import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  cpu?: string,
  memory?: string,
}

export default class TemplatePage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.VM_VERSION,
      realType: HCI.VM_TEMPLATE,
    });
  }

  public setBasics(cpu?: string, memory?: string) {
    this.cpu().input(cpu)
    this.memory().input(memory)
  }

  cpu() {
    return new LabeledInputPo('.labeled-input', `:contains("CPU")`)
  }

  memory() {
    return new LabeledInputPo('.labeled-input', `:contains("Memory")`)
  }

  save(namespace:string, createButton?: string = 'Create') {
    cy.intercept('POST', `/v1/harvester/${this.realType}s/${namespace}`).as('create');
    cy.get(this.footerButtons).contains(createButton).click()
    cy.wait('@create').then(res => {
      expect(res.response?.statusCode, `Create ${this.type} success`).to.be.oneOf([200, 201]);
    })
  }
}
