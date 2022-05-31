import YAML from 'js-yaml'
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { ImagePage } from "@/pageobjects/image.po";

const vms = new VmsPage();
const image = new ImagePage();

/**
 * 1. Create image with cloud image available for openSUSE. http://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.3/images/openSUSE-Leap-15.3.x86_64-NoCloud.qcow2
 * 2. Click save
 * 3. Try to edit the description
 * 4. Try to edit the URL
 * 5. Try to edit the Labels
 * Expected Results
 * 1. Image should show state as Active.
 * 2. Image should show progress as Completed.
 * 3. User should be able to edit the description and Labels
 * 4. User should not be able to edit the URL
 * 5. User should be able to create a new image with same name.
 */
describe('Create an image with valid image URL', () => {
    const IMAGE_NAME = 'auto-image-valid-url-test';
    const IMAGE_URL = 'http://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.3/images/openSUSE-Leap-15.3.x86_64-NoCloud.qcow2';
    const value = {
        name: IMAGE_NAME,
        url: IMAGE_URL,
        size: '544 MB',
        labels: {
            y1: 'z1',
            y2: 'z2'
        }
    }

    it('Create an image with valid image URL', () => {
        cy.login();

        // create IMAGE
        image.goToCreate();
        image.create(value);
        image.checkState(value);

        // edit IMAGE
        image.goToEdit(IMAGE_NAME);

        const namespace = 'default';

        const editValue = {
            name: IMAGE_NAME,
            url: 'xx',
            description: 'Edit image test',
            labels: {
                edit: 'edit'
            },
            namespace,
        }
        
        image.edit(editValue);

        // delete IMAGE
        image.delete(IMAGE_NAME);

        // create IMAGE with the same name
        image.goToCreate();
        image.create(value);
        image.checkState(value);

        // delete IMAGE
        image.delete(IMAGE_NAME);
    });
});

/**
 * 1. Create image with invalid URL. e.g. - https://test.img
 * Expected Results
 * 1. Image state show as Failed
 */
 describe('Create image with invalid URL', () => {
    const IMAGE_NAME = 'auto-image-invalid-url-test';

    it('Create image with invalid URL', () => {
        cy.login();

        // create invalid IMAGE
        image.goToCreate();
        const namespace = 'default';

        const value = {
            name: IMAGE_NAME,
            url: 'https://test.img'
        }

        image.create(value);
        image.checkState(value, false);

        // delete IMAGE
        image.delete(IMAGE_NAME);
    });
});

/**
 * 1. create vm “vm-1”
 * 2. create a image “img-1” by export the volume used by vm “vm-1”
 * 3. delete vm “vm-1”
 * 4. delete image “img-1”
 * Expected Results
 * 1. image “img-1” will be deleted
 */
describe('Delete VM with exported image', () => {
    const IMAGE_NAME = 'img-1';
    const VM_NAME = 'vm-1';

    it('Delete VM with exported image', () => {
        cy.login();

        const imageEnv = Cypress.env('image');
        const namespace = 'default';

        // create VM
        const value = {
            name: VM_NAME,
            cpu: '2',
            memory: '4',
            image: imageEnv.name,
            namespace,
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
        vms.delete(namespace, VM_NAME);

        // delete IMAGE
        image.delete(IMAGE_NAME);
    });
});

/**
 * 1. create vm “vm-1”
 * 2. create a image “img-1” by export the volume used by vm “vm-1”
 * 3. delete vm “vm-1”
 * 4. update image “img-1” labels
 * Expected Results
 * 1. image “img-1” will be updated
 */
describe('Update image labels after deleting source VM', () => {
    const IMAGE_NAME = 'img-1';
    const VM_NAME = 'vm-1';

    it('Update image labels after deleting source VM', () => {
        cy.login();

        const imageEnv = Cypress.env('image');
        const namespace = 'default';

        const value = {
            name: VM_NAME,
            cpu: '2',
            memory: '4',
            image: imageEnv.name,
            namespace,
        }

        // create VM
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
        vms.delete(namespace, VM_NAME);

        // edit IMAGE
        image.goToEdit(IMAGE_NAME);

        const editValue = {
            name: IMAGE_NAME,
            url: 'xx',
            description: 'Edit image test',
            labels: {
                edit: 'edit'
            }
        }
        
        image.edit(editValue, true);

        // delete IMAGE
        image.delete(IMAGE_NAME);
    });
});

/**
 * 1. Upload cloud image to images page
 * 2. Create new vm with image using appropriate template
 * 3. Check State
 * Expected Results
 * 1. Image should upload.
 */
//  describe('Create a cloud image via upload', () => {
//     const IMAGE_NAME = 'auto-image-cloud-upload-test';
//     const VM_NAME = 'auto-image-cloud-test-vm';

//     it('Create a cloud image via upload', () => {
//         login.login();

//         // upload IMAGE
//         image.goToCreate();

//         const value = {
//             name: IMAGE_NAME,
//             size: '542 MB',
//             path: 'openSUSE-Leap-15.3.x86_64-1.0.1-NoCloud-Build2.97.qcow2',
//             labels: {
//                 from: 'upload',
//                 y2: 'z2'
//             }
//         }

//         image.createFromUpload(value);
//         image.checkState(value);

//         // create VM
//         const vmValue = {
//             name: VM_NAME,
//             cpu: '2',
//             memory: '4',
//             image: IMAGE_NAME,
//         }

//         vms.create(vmValue);

//         // check VM state
//         vms.goToConfigDetail(VM_NAME);
//         vms.goToYamlDetail(VM_NAME);

//         // delete VM
//         vms.delete(VM_NAME)

//         // delete IMAGE
//         image.delete(IMAGE_NAME)
//     });
// });

/**
 * 1. Upload ISO image to images page
 * 2. Create new vm with image using appropriate template
 * 3. Check State
 * Expected Results
 * 1. Image should upload.
 */
describe('Create a ISO image via upload', () => {
    const IMAGE_NAME = 'auto-image-iso-upload-test';
    const VM_NAME = 'auto-image-iso-test-vm';

    it('Create a ISO image via upload', () => {
        cy.login();

        // create IMAGE
        image.goToCreate();
        const namespace = 'default';

        const value = {
            name: IMAGE_NAME,
            size: '16 MB',
            path: 'cypress/fixtures/cirros-0.5.2-aarch64-disk.img',
            labels: {
                from: 'upload',
                y2: 'z2'
            }
        }

        image.createFromUpload(value);
        image.checkState(value);

        // create VM
        const vmValue = {
            name: VM_NAME,
            cpu: '2',
            memory: '4',
            image: IMAGE_NAME,
            namespace,
        }

        vms.create(vmValue);

        // check VM state
        vms.goToConfigDetail(VM_NAME);
        vms.goToYamlDetail(VM_NAME);
        
        // delete VM
        vms.delete(namespace, VM_NAME)

        // delete IMAGE
        image.delete(IMAGE_NAME)
    });
});
