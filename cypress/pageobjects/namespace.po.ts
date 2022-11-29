import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';



export default class NamespacePage extends CruResourcePo {
  constructor() {
    super({
      type: HCI.NAMESPACE
    });
  }

  setNameDescription(name: string, description?: string | undefined): void {
    if (name) {
      this.name().input(name)
    }

    if (description) {
      this.description().input(description)
    }
  }
}
