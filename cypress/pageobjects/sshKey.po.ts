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
  sshKey?: string,
}
export default class SshPage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.SSH
    });
  }

  sshKey() {
    return new LabeledTextAreaPo('.labeled-input', `:contains("SSH Key")`)
  }

  public setValue(value: ValueInterface) {
    this.namespace().select({option: value?.namespace})
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.sshKey().input(value?.sshKey, {
      delay: 0,
    })
  }
}
