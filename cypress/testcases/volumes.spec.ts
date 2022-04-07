import YAML from 'js-yaml'
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { ImagePage } from "@/pageobjects/image.po";
import { VolumePage } from "@/pageobjects/volume.po";
import { LoginPage } from "@/pageobjects/login.po";

const login = new LoginPage();
const vms = new VmsPage();
const image = new ImagePage();
const volumes = new VolumePage();

/**
 * 1. Create new VM
 * 2. Export volume to image from volumes page
 * 3. Create new VM from image
 * Expected Results
 * 1. image should upload/complete in images page
 * 2. New VM should create
 */
describe('Create image from Volume', () => {
    const IMAGE_NAME = 'img-2';
    const VM_NAME = 'vm-2';
    const ANOTHER_VM_NAME = 'vm-3';

    it('Create image from Volume', () => {
        login.login();

        // create VM
        const value = {
            name: VM_NAME,
            cpu: '2',
            memory: '4',
            image: 'ubuntu-18.04-server-cloudimg-amd64.img',
        }

        vms.create(value);

        // check VM state
        vms.goToConfigDetail(VM_NAME);
        vms.goToYamlDetail(VM_NAME);

        // export IMAGE
        image.exportImage(VM_NAME, IMAGE_NAME);

        // check IMAGE state
        image.goToList();
        image.checkState({
            name: IMAGE_NAME,
            size: '10 GB'
        });

        // delete VM
        vms.delete(VM_NAME);

		// create VM
		vms.create({
			name: ANOTHER_VM_NAME,
			cpu: '2',
			memory: '4',
			image: IMAGE_NAME
		});

		// check VM state
        vms.goToConfigDetail(ANOTHER_VM_NAME);
        vms.goToYamlDetail(ANOTHER_VM_NAME);

		// delete VM
		vms.delete(ANOTHER_VM_NAME);

        // delete IMAGE
        image.delete(IMAGE_NAME);
    });
});

/**
 * 1. Navigate to volumes page
 * 2. Click Create
 * 3. Select an image
 * 4. Input a size
 * 5. Click Create
 * Expected Results
 * 1. Page should load
 * 2. Volume should create successfully and go to succeeded in the list
 */
describe('Create volume root disk VM Image Form', () => {
    const VOLUME_NAME = 'volume-e2e-image';

    it('Create volume root disk VM Image Form', () => {
        login.login();

        // create VOLUME
        const value = {
            name: VOLUME_NAME,
            size: '10',
            image: 'ubuntu-18.04-server-cloudimg-amd64.img'
        }

        volumes.create(value);

        // check state
        volumes.checkState(value);

        // delete VOLUME
        volumes.delete(VOLUME_NAME);
    });
});

/**
 * 1. Create a VM with a root volume
 * 2. Write 10Gi data into it.
 * 3. Delete the VM but not the volume
 * 4. Verify Volume still exists
 * 5. Delete the volume
 * Expected Results
 * 1. VM should create
 * 2. VM should delete
 * 3. Volume should still show in Volume list
 * 4. Volume should delete
 */
 describe('Delete volume that was attached to VM but now is not', () => {
    const VM_NAME = 'vm-e2e-1';

    it('Delete volume that was attached to VM but now is not', () => {
        login.login();

        // create VM
        const value = {
            name: VM_NAME,
            cpu: '2',
            memory: '4',
            image: 'ubuntu-18.04-server-cloudimg-amd64.img',
        }

        vms.create(value);

        // check VM state
        vms.goToConfigDetail(VM_NAME);
        vms.goToYamlDetail(VM_NAME);

        // delete VM
        vms.delete(VM_NAME, { removeRootDisk: false });

        // check VOLUME state
        volumes.checkStateByVM(VM_NAME);

        // delete VOLUME
        volumes.deleteVolumeByVM(VM_NAME);
    });
});
