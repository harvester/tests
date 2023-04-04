import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { generateName } from '@/utils/utils';

const constants = new Constants();
const vms = new VmsPage();

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
    this.clickTab('Basics');
    vms.cpu().input(cpu)
    vms.memory().input(memory)
  }

  public save({type = this.type, namespace = 'default'}: {type?:string, namespace:string}): Promise<string> {
    return new Cypress.Promise((resolve, reject) => {
      const interceptName = generateName('create');

      cy.intercept('POST', `/v1/harvester/${type}s/${namespace}`).as(interceptName);
      this.clickFooterBtn()
      cy.wait(`@${interceptName}`).then(res => {
        expect(res.response?.statusCode, `Create ${this.type} success`).to.equal(201);
        console.log(res.response?.body?.metadata?.name);
        resolve(res.response?.body?.metadata?.name || '');
      })
      .end();
    });
  }
}
