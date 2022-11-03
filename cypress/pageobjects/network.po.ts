import PagePo from '@/utils/components/page.po';
import { Constants } from "@/constants/constants";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import LabeledTextAreaPo from '@/utils/components/labeled-textarea.po';
import RadioButtonPo from '@/utils/components/radio-button.po';
import { HCI, NETWORK_ATTACHMENT } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

const constants = new Constants();

interface ValueInterface {
  namespace: string,
  name: string,
  description: string,
  vlan?: string,
  dhcp?: string,
  gateway?: string,
  cidr?: string,
  mode?: string,
  clusterNetwork?: string
}

export default class NetworkPage extends CruResourcePo {
  private networkTab = '.tab#layer3Network';

  constructor() {
    super({
      type: HCI.NETWORK_ATTACHMENT,
      realType: 'k8s.cni.cncf.io.network-attachment-definition',
      storeType: NETWORK_ATTACHMENT
    });
  }

  public setValue(value: ValueInterface) {
    this.namespace().select({option: value?.namespace})
    this.name().input(value?.name)
    this.description().input(value?.description)
    this.vlan().input(value?.vlan)
    this.clusterNetwork().select({option: value?.clusterNetwork})
    cy.get(this.networkTab).click()
    this.mode().input(value.mode)
    this.dhcp().input(value.dhcp)
    this.cidr().input(value.cidr)
    this.gateway().input(value.gateway)
  }

  vlan() {
    return new LabeledInputPo('.labeled-input', `:contains("Vlan ID")`)
  }

  clusterNetwork() {
    return new LabeledSelectPo('.labeled-select', `:contains("Cluster Network")`)
  }

  dhcp() {
    return new LabeledInputPo('.labeled-input', `:contains("DHCP Server IP")`)
  }

  mode() {
    return new RadioButtonPo('.radio-group', ':contains("Mode")')
  }

  cidr() {
    return new LabeledInputPo('.labeled-input', `:contains("CIDR")`)
  }

  gateway() {
    return new LabeledInputPo('.labeled-input', `:contains("Gateway")`)
  }
}
