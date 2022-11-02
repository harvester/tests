import PagePo from '@/utils/components/page.po';
import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import RadioButtonPo from '@/utils/components/radio-button.po';
import YamlEditorPo from '@/utils/components/yaml-editor.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

const constants = new Constants();

interface ValueInterface {
  namespace?: string,
  name?: string,
  description?: string,
  templateType?: string,
  data?: string,
}

export default class extends CruResourcePo {
  constructor() {
    super({
      type: HCI.CLOUD_TEMPLATE,
      realType: 'configmap',
    });
  }

  templateType() {
    return new LabeledSelectPo('section .labeled-select.hoverable', `:contains("Template")`)
  }

  data() {
    return new YamlEditorPo('.CodeMirror')
  }

  public setValue(value: ValueInterface) {
    this.namespace().select({option: value?.namespace})
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.templateType().select({option: value?.templateType})
    this.data().input(value.data)
  }
}
