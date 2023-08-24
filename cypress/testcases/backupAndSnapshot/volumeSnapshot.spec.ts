import { onlyOn } from "@cypress/skip-test";
import { VolumePage } from "@/pageobjects/volume.po";
import VolumeSnapshot from "@/pageobjects/volumeSnapshot.po";
import { PageUrl } from "@/constants/constants";

const volumes = new VolumePage();
const volumeSnapshots = new VolumeSnapshot();

describe('Validation volume snapshot', () => {
  const volumeName = 'test';
  let createVolumeSnapshotSuccess: boolean = false ;
  const volumeSnapshotName = 'test-volume-snapshot';

  beforeEach(() => {
    cy.login({url: PageUrl.volumeSnapshot});
  });

  it('Create a volume snapshot', () => {
    // Create a volume to test the snapshot operation
    const namespace = 'default';

    const id = `${namespace}/${volumeName}`;

    // delete volume 
    volumes.deleteFromStore(id);

    // create a new volume
    volumes.goToCreate();
    volumes.setNameNsDescription(volumeName, namespace);
    volumes.setBasics({size: '4'});
    volumes.save();
    volumes.censorInColumn(volumeName, 3, namespace, 4, 'Ready');

    // create a snapshot
    volumes.clickVolumeSnapshotAction(volumeName, volumeSnapshotName);

    // check vm snapshot
    volumeSnapshots.goToList();
    volumeSnapshots.checkState(volumeSnapshotName);

    // check volume Snapshot Counts
    volumes.checkSnapshotCount(volumeName, 1);
    createVolumeSnapshotSuccess = true
  })

  it('Resotre New volume from volume snapshot', () => {
    onlyOn(createVolumeSnapshotSuccess);
    
    const newName = 'create-new-from-snapshot';

    volumes.deleteFromStore(`default/${volumeSnapshotName}`);

    volumeSnapshots.goToList();
    volumeSnapshots.restoreNew(volumeSnapshotName, newName);

    // check volume
    volumes.checkState(newName);

    // delete volume
    volumes.deleteFromStore(`default/${newName}`);
  })
})