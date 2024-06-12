import { VmsPage } from "@/pageobjects/virtualmachine.po";

import { generateName } from '@/utils/utils';
import { Constants } from "@/constants/constants";

const vmPO = new VmsPage();
const constants = new Constants();

describe('Stop VM Negative', () => {
  it('Stop VM Negative', () => {
    cy.login();

    const VM_NAME = generateName('test-vm-scheduling');
    const namespace = 'default'
    const imageEnv = Cypress.env('image');

    const volume = [{
      buttonText: 'Add Volume',
      create: false,
      image: `default/${Cypress._.toLower(imageEnv.name)}`,
      size: 4
    }];

    vmPO.goToCreate();

    vmPO.setNameNsDescription(VM_NAME, namespace);
    vmPO.setBasics('1', '1');
    vmPO.setVolumes(volume);

    const hostList = Cypress.env('host');
    const host = hostList[0];

    vmPO.setNodeScheduling({
      radio: 'specific',
      nodeName: host.customName || host.name, 
    });

    vmPO.save(); 

    vmPO.censorInColumn(VM_NAME, 3, namespace, 4, 'Running', 2, { 
      nameSelector: '.name-console a', 
      timeout: constants.timeout.uploadTimeout 
    });

    vmPO.clickAction(VM_NAME, 'Stop')

    vmPO.censorInColumn(VM_NAME, 3, namespace, 4, 'Stopping', 2, { 
      nameSelector: '.name-console a', 
      timeout: constants.timeout.uploadTimeout 
    });

    vmPO.deleteVMFromStore(`${namespace}/${VM_NAME}`);
  })
})
