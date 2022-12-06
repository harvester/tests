import YAML from 'js-yaml'
import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { HostsPage } from "@/pageobjects/hosts.po";
import { generateName } from '@/utils/utils';

const vms = new VmsPage();
const hosts = new HostsPage();

/**
 * https://harvester.github.io/tests/manual/virtual-machines/vm_schedule_on_node/
 */
describe('VM scheduling on Specific node', () => { 
  beforeEach(() => {
    cy.login();
  });

  it('Schedule VM on the Node which is Enable Maintenance Mode', () => {
    const VM_NAME = generateName('vm-scheduling')
    const NAMESPACE = 'default'
    const hostList = Cypress.env('host');

    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: [hostList[0].name, hostList[1].name]});
    
    hosts.goToList();
    hosts.enableMaintenance(hostList[0].name);
    
    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: [hostList[1].name], excludeNodes: [hostList[0].name]});

    hosts.goToList();
    hosts.clickAction(hostList[0].name, 'Disable Maintenance Mode');

    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: [hostList[0].name, hostList[1].name]});
  })
})

