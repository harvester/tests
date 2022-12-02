import { onlyOn } from "@cypress/skip-test";
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import VMBackup from '@/pageobjects/vmBackup.po';
import { PageUrl } from "@/constants/constants";

const vms = new VmsPage();
const vmBackups = new VMBackup();

describe('VM Backup Validation', () => {
  const vmName = 'test';
  let createVMBackupSuccess: boolean = false ;
  const vmBackupName = 'test-vm-backup';

  beforeEach(() => {
    cy.login({url: PageUrl.virtualMachine});
  });

  it('Take a vm backup from vm', () => {
    // Create a vm to test the backup operation
    const namespace = 'default';

    const id = `${namespace}/${vmName}`;
    const imageEnv = Cypress.env('image');
    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      size: '2',
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
    }];

    vmBackups.deleteFromStore(`${namespace}/${vmBackupName}`)
    vms.deleteVMFromStore(id)
    vms.goToCreate();
    vms.deleteVMFromStore(`${namespace}/${vmName}`);
    vms.setNameNsDescription(vmName, namespace);
    vms.setBasics('1', '1');
    vms.setVolumes(volume);
    vms.save();

    // create a vm snapshot
    vms.checkVMState(vmName, 'Running');
    vms.clickVMBackupAction(vmName, vmBackupName);

    // check vm snapshot
    vmBackups.goToList();
    // vmBackups.checkState(vmBackupName, vmName);
    vmBackups.censorInColumn(vmBackupName, 3, namespace, 4, vmName, 5, { timeout: 5000, nameSelector: 'a' });

    createVMBackupSuccess = true
  })

  it('Resotre New VM from vm backup', () => {
    onlyOn(createVMBackupSuccess);
    
    const newVMName = 'create-new-from-backup';

    vms.deleteVMFromStore(`default/${newVMName}`)
    vmBackups.goToList();
    vmBackups.restoreNew(vmBackupName, newVMName);
    vms.checkVMState(newVMName);

    // delete vm
    vms.deleteVMFromStore(`default/${newVMName}`);
  })

  it('Resotre New VM in another namespace from vm backup', () => {
    onlyOn(createVMBackupSuccess);
    
    const newVMName = 'create-new-from-backup';

    vms.deleteVMFromStore(`default/${newVMName}`)
    vmBackups.goToList();
    vmBackups.restoreNew(vmBackupName, newVMName, 'harvester-public');
    vms.checkVMState(newVMName);

    // delete vm
    vms.deleteVMFromStore(`default/${newVMName}`);
  })

  it('Resotre Existing VM from vm backup', () => {
    onlyOn(createVMBackupSuccess);
    
    vms.goToList();
    vms.clickAction(vmName, 'Stop');
    vms.checkVMState(vmName, 'Off')
    vmBackups.goToList();
    vmBackups.restoreExistingVM(vmBackupName);
    vms.checkVMState(vmName);

    // delete vm
    vms.deleteVMFromStore(`default/test`);
  })

  it('delete backup', () => {
    onlyOn(createVMBackupSuccess);
    
    vmBackups.goToList();
    vmBackups.deleteFromStore(`default/${vmBackupName}`);
  })
})