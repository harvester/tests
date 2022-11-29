import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

export default class VMSnapshot extends CruResourcePo {
  constructor() {
    super({
      type: 'harvesterhci.io.vmsnapshot',
      realType: HCI.BACKUP,
    });
  }

  checkState(name:  string, state: string = 'Ready', namespace: string = 'default') {
    this.censorInColumn(name, 3, namespace, 4, state, 2);
  }

  restoreNew(name: string) {
    this.clickAction(name, 'Restore New');
    new LabeledSelectPo('.labeled-select', `:contains("Namespace")`).isDisabled();
    new LabeledInputPo('.labeled-input', `:contains("Virtual Machine Name ")`).input('create-new-from-snapshot');
    this.clickFooterBtn('Create');
  }

  restoreExistingVM(name: string) {
    this.clickAction(name, 'Replace Existing');
    new LabeledSelectPo('.labeled-select', `:contains("Namespace")`).isDisabled();
    new LabeledInputPo('.labeled-input', `:contains("Virtual Machine Name")`).isDisabled();
    new LabeledSelectPo('.labeled-select', `:contains("Snapshot")`).self().contains(name);
    this.clickFooterBtn('Create');
  }

  clickFooterBtn(text: string = 'Create') {
    cy.get('.footer .buttons').find('.btn').contains(text).click();
  }
}
