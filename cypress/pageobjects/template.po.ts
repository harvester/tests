import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';
import { VmsPage } from "@/pageobjects/virtualmachine.po";

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
    vms.cpu().input(cpu)
    vms.memory().input(memory)
  }
}
