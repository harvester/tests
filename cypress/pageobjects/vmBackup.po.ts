import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import { HCI } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

import { Constants } from "@/constants/constants";
const constants = new Constants();

export default class VMBackup extends CruResourcePo {
  constructor() {
    super({
      type: HCI.BACKUP,
    });
  }

  checkState(name:  string, state: string = 'Ready',  namespace: string = 'default') {
    this.censorInColumn(name, 3, namespace, 4, state, 2, { timeout: constants.timeout.uploadTimeout });
  }

  restoreNew(name: string, newVMName: string, namespace?: string) {
    this.clickAction(name, 'Restore New');
    if (namespace) {
      new LabeledSelectPo('.labeled-select', `:contains("Namespace")`).select({option: namespace});
    }

    new LabeledInputPo('.labeled-input', `:contains("Virtual Machine Name ")`).input(newVMName);
    new LabeledSelectPo('.labeled-select', `:contains("Backup")`).self().contains(name);
    this.clickFooterBtn('Create');
  }

  restoreExistingVM(name: string) {
    this.clickAction(name, 'Replace Existing');
    new LabeledSelectPo('.labeled-select', `:contains("Namespace")`).isDisabled();
    new LabeledInputPo('.labeled-input', `:contains("Virtual Machine Name")`).isDisabled();
    new LabeledSelectPo('.labeled-select', `:contains("Backup")`).self().contains(name);
    this.clickFooterBtn('Create');
  }

  clickFooterBtn(text: string = 'Create') {
    cy.get('.footer .buttons').find('.btn').contains(text).click();
  }
}
