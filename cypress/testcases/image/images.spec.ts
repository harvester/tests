import { Constants } from "@/constants/constants";
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { ImagePage } from "@/pageobjects/image.po";
import { generateName } from '@/utils/utils';
import { HCI } from '@/constants/types';

const constants = new Constants();
const vms = new VmsPage();
const image = new ImagePage();

describe('Auto setup image from cypress environment', () => {
  it('Auto setup image from cypress environment', () => {
    const imageEnv = Cypress.env('image');
    const IMAGE_NAME = Cypress._.toLower(imageEnv.name);
    const IMAGE_URL = imageEnv.url;
    
    const value = {
        name: IMAGE_NAME,
        url: IMAGE_URL,
    }

    cy.login();

    cy.request({
      url: `v1/harvester/${HCI.IMAGE}s`,
      headers: {
        accept: 'application/json'
      }
    }).then(res => {
      expect(res?.status, 'Check Image list').to.equal(200);
      const images = res?.body?.data || []
      const imageFound = images.find((i:any) => i?.spec?.displayName === IMAGE_NAME)

      if (imageFound) {
        return
      } else {
        const namespace = 'default';

        image.goToCreate();
        image.setNameNsDescription(IMAGE_NAME, namespace);
        image.setBasics({url: IMAGE_URL});
        image.save();
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });
      }
    })
  })
})

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
    const imageEnv = Cypress.env('image');
    const IMAGE_NAME = generateName('auto-image-valid-url-test');
    const IMAGE_URL = imageEnv.url;

    it('Create an image with valid image URL', () => {
        cy.login();

        // create IMAGE
        const namespace = 'default';

        cy.intercept('POST', `v1/harvester/${HCI.IMAGE}s`).as('create');
        image.goToCreate();
        image.setNameNsDescription(IMAGE_NAME, namespace);
        image.setBasics({url: IMAGE_URL});
        image.setLabels({
            labels: {
                thefirstlabel: 'thefirstlabel',
                thesecondlabel: 'thesecondlabel'
            }
        });
        image.save();
        cy.wait('@create').should((res: any) => {
            expect(res.response?.statusCode, 'Create VM').to.equal(201);
            const imageObj = res?.response?.body || {}
            const imageId = imageObj?.id || '';

            // check IMAGE state
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });

            // edit IMAGE
            image.goToEdit(IMAGE_NAME);
            image.name().self().find('input').should('be.disabled');
            image.url().self().find('input').should('be.disabled');
            image.setLabels({
                labels: {
                    edit: 'edit'
                }
            })
            image.update(imageId);

            // delete IMAGE
            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
        

        image.goToCreate();
        image.setNameNsDescription(IMAGE_NAME, namespace);
        image.setBasics({url: IMAGE_URL});
        image.save();
        // create IMAGE with the same name
        cy.wait('@create').should((res: any) => {
            expect(res.response?.statusCode, 'Create VM').to.equal(201);
            const imageObj = res?.response?.body || {}
            const imageId = imageObj?.id || '';

            // check IMAGE state
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });

            // delete IMAGE
            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
    });
});

/**
 * 1. Create image with invalid URL. e.g. - https://test.img
 * Expected Results
 * 1. Image state show as Failed
 */
 describe('Create image with invalid URL', () => {
    const IMAGE_NAME = generateName('auto-image-invalid-url-test');

    it('Create image with invalid URL', () => {
        cy.login();

        // create invalid IMAGE
        const namespace = 'default';

        cy.intercept('POST', `v1/harvester/${HCI.IMAGE}s`).as('create');
        image.goToCreate();
        image.setNameNsDescription(IMAGE_NAME, namespace);
        image.setBasics({url: 'https://test.img'});
        image.save();
        cy.wait('@create').should((res: any) => {
            expect(res.response?.statusCode, 'Create VM').to.equal(201);
            const imageObj = res?.response?.body || {}
            const imageId = imageObj?.id || '';

            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Failed', 2, { timeout: constants.timeout.uploadTimeout });
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, '0%', 5, { timeout: constants.timeout.uploadTimeout });

            // delete IMAGE
            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
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
    const IMAGE_NAME = generateName('img-1');
    const VM_NAME = generateName('vm-1');

    it('Delete VM with exported image', () => {
        cy.login();

        const imageEnv = Cypress.env('image');
        const namespace = 'default';
        const volumes = [{
            buttonText: 'Add Volume',
            create: false,
            image: `default/${imageEnv.name}`,
        }];

        // create VM
        vms.goToCreate();
        vms.setNameNsDescription(VM_NAME, namespace);
        vms.setBasics('2', '4');
        vms.setVolumes(volumes);
        vms.save();
        
        // export IMAGE
        image.exportImage(VM_NAME, IMAGE_NAME, namespace);
        image.goToList();
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });

        // delete VM
        vms.delete(namespace, VM_NAME);

        cy.window().then(async (win) => {
            const imageList = (win as any).$nuxt.$store.getters['harvester/all'](HCI.IMAGE);
            const imageObj = imageList.find((I: any) => I.spec.displayName === IMAGE_NAME);
            const imageId = imageObj?.id;

            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
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
    const IMAGE_NAME = generateName('img-1');
    const VM_NAME = generateName('vm-1');

    it('Update image labels after deleting source VM', () => {
        cy.login();

        const imageEnv = Cypress.env('image');
        const namespace = 'default';
        const volumes = [{
            buttonText: 'Add Volume',
            create: false,
            image: `default/${imageEnv.name}`,
        }];

        // create VM
        vms.goToCreate();
        vms.setNameNsDescription(VM_NAME, namespace);
        vms.setBasics('2', '4');
        vms.setVolumes(volumes);
        vms.save();
        vms.censorInColumn(VM_NAME, 3, namespace, 4, 'Running', 2, { timeout: constants.timeout.maxTimeout, nameSelector: '.name-console a' });

        // export IMAGE
        image.exportImage(VM_NAME, IMAGE_NAME, namespace);

        // check IMAGE state
        image.goToList();
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
        image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });

        // delete VM
        vms.delete(namespace, VM_NAME);

        // edit IMAGE
        image.goToEdit(IMAGE_NAME);
        cy.window().then(async (win) => {
            const imageList = (win as any).$nuxt.$store.getters['harvester/all'](HCI.IMAGE);
            const imageObj = imageList.find((I: any) => I.spec.displayName === IMAGE_NAME);
            const imageId = imageObj?.id;

            image.setLabels({
                labels: {
                    thefirstlabel: 'thefirstlabel',
                    thesecondlabel: 'thesecondlabel'
                }
            });
            image.update(imageId);
            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
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
//         vms.goToYamlEdit(VM_NAME);

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
    const IMAGE_NAME = generateName('auto-image-iso-upload-test');
    const VM_NAME = generateName('auto-image-iso-test-vm');

    it('Create a ISO image via upload', () => {
        cy.login();

        // create IMAGE
        const namespace = 'default';

        cy.intercept('POST', `v1/harvester/${HCI.IMAGE}s/*`).as('create');
        image.goToCreate();
        image.setNameNsDescription(IMAGE_NAME, namespace);
        image.setBasics({path: 'cypress/fixtures/cirros-0.5.2-aarch64-disk.img'});
        image.save({upload: true});
        cy.wait('@create').should((res: any) => {
            expect(res.response?.statusCode, 'Create VM').to.equal(201);
            const imageObj = res?.response?.body || {}
            const imageId = imageObj?.id || '';

            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Active', 2, { timeout: constants.timeout.uploadTimeout });
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, 'Completed', 5, { timeout: constants.timeout.uploadTimeout });
            image.censorInColumn(IMAGE_NAME, 3, namespace, 4, '16 MB', 6, { timeout: constants.timeout.uploadTimeout });

            // create VM
            const volumes = [{
                buttonText: 'Add Volume',
                create: false,
                image: `default/${IMAGE_NAME}`,
            }];

            vms.goToCreate();
            vms.setNameNsDescription(VM_NAME, namespace);
            vms.setBasics('2', '4');
            vms.setVolumes(volumes);
            vms.save();
            vms.censorInColumn(VM_NAME, 3, namespace, 4, 'Running', 2, { timeout: constants.timeout.maxTimeout, nameSelector: '.name-console a' });

            // delete VM
            vms.delete(namespace, VM_NAME)

            // delete IMAGE
            image.delete(namespace, IMAGE_NAME, { id: imageId });
        })
    });
});
