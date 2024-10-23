import { generateName } from '@/utils/utils';
import storagePage from "@/pageobjects/storageClasses.po";

const storageClasses = new storagePage();

/**
 * 1. Login
 * 2. Navigate to the Storage Classes create page
 * 3. Input required values
 * 4. Validate the create request
*/
describe('Create a storage class with all the required values', () => {
  beforeEach(() => {
    cy.login();
  });

  it('Create a storage class with the required values', () => {
    const NAME = generateName('test')

    const value = {
      name: NAME,
    }

    storageClasses.create(value);

    storageClasses.delete({ name: NAME })
  });

  /**
   * 1. Login
   * 2. Navigate to the Storage Classes create page
   * 3. Change default values
   * 4. Validate the created storage class
  */
  it('Create a storage class with change default values', () => {
    const NAME = generateName('test')

    const value = {
      name: NAME,
      replicas: '2',
      staleReplicaTimeout: '20',
      migratable: 'No',
      reclaimPolicy: 'Retain the volume for manual cleanup',
      allowVolumeExpansion: 'Disabled',
      volumeBindingMode: 'Bind and provision a persistent volume once a virtual machine using the PersistentVolumeClaim is created',
    }

    storageClasses.create(value);

    storageClasses.checkValue({
      name: NAME,
      replicas: '2',
      staleReplicaTimeout: '20',
      migratable: 'false',
      reclaimPolicy: 'Retain',
      allowVolumeExpansion: false,
      volumeBindingMode: 'WaitForFirstConsumer',
    });

    storageClasses.delete({ name: NAME })
  });
});
