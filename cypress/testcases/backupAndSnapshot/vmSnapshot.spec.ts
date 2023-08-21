import { onlyOn } from "@cypress/skip-test";
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import VMSnapshot from "@/pageobjects/vmSnapshot.po";
import { PageUrl } from "@/constants/constants";

const vms = new VmsPage();
const vmsnapshots = new VMSnapshot();

describe('VM snapshot Form Validation', () => {
  const vmName = 'test';
  let createVMSnapshotSuccess: boolean = false ;
  const vmSnapshotName = 'test-vm-snapshot';

  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  it('Take a vm snaphost from vm', () => {
    // Create a vm to test the snapshot operation
    const namespace = 'default';

    const id = `${namespace}/${vmName}`;
    const imageEnv = Cypress.env('image');
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    vmsnapshots.deleteFromStore(`${namespace}/${vmSnapshotName}`)
    vms.deleteVMFromStore(id)
    vms.goToCreate();
    vms.deleteVMFromStore(`${namespace}/${vmName}`);
    vms.setNameNsDescription(vmName, namespace);
    vms.setBasics('1', '1');
    vms.setVolumes(volume);
    vms.save();

    // create a vm snapshot
    vms.checkVMState(vmName, 'Running');
    vms.clickVMSnapshotAction(vmName, vmSnapshotName);

    // check vm snapshot
    vmsnapshots.goToList();
    vmsnapshots.checkState(vmSnapshotName)
    createVMSnapshotSuccess = true
  })

  it('Resotre New VM from vm snapshot', () => {
    onlyOn(createVMSnapshotSuccess);
    
    const newVMName = 'create-new-from-snapshot';

    vms.deleteVMFromStore(`default/${newVMName}`)
    vmsnapshots.goToList();
    vmsnapshots.restoreNew(vmSnapshotName);
    vms.checkVMState(newVMName);

    // delete vm
    vms.deleteVMFromStore(`default/${newVMName}`);
  })

  it('Resotre Existing VM from vm snapshot', () => {
    onlyOn(createVMSnapshotSuccess);
    
    vms.goToList();
    vms.clickAction(vmName, 'Stop');
    vms.checkVMState(vmName, 'Off')
    vmsnapshots.goToList();
    vmsnapshots.restoreExistingVM(vmSnapshotName);
    vms.checkVMState(vmName);

    // delete vm
    vms.deleteVMFromStore(`default/test`);
  })
})