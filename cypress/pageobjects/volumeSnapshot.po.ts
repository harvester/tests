import LabeledInputPo from '@/utils/components/labeled-input.po';
import { HCI, HCI_URL } from '@/constants/types'
import CruResourcePo from '@/utils/components/cru-resource.po';

export default class VolumeSnapshot extends CruResourcePo {
  constructor() {
    super({
      type: HCI_URL.volumeSnapshot,
      realType: HCI.volumeSnapshot,
    });
  }

  checkState(name:  string, state: string = 'Active', namespace: string = 'default') {
    this.censorInColumn(name, 3, namespace, 4, state, 2);
  }

  restoreNew(name: string, newVolumeName: string) {
    this.clickAction(name, 'Restore');
    new LabeledInputPo('.labeled-input', `:contains("New Volume Name")`).input(newVolumeName);
    cy.get('.v--modal-box,.v--modal .card-actions').contains('Create').click();
  }
}
