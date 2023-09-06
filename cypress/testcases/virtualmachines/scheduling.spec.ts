import { VmsPage } from "@/pageobjects/virtualmachine.po";
import { HostsPage } from "@/pageobjects/hosts.po";

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
    const hostList = Cypress.env('host');
    const hostNames: string[] = hostList.map((host: any) => host.name);
    const maintenanceNode = hostNames[0]
    const filterMaintenanceNames = hostNames.filter(name => name !== maintenanceNode);

    // Check whether all nodes can be selected
    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: hostNames});
    
    hosts.goToList();
    hosts.enableMaintenance(hostNames[0]);
    
    // Maintenance nodes should not be selected
    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: filterMaintenanceNames, excludeNodes: [maintenanceNode]});

    hosts.goToList();
    hosts.clickAction(hostList[0].name, 'Disable Maintenance Mode');

    // Check whether all nodes can be selected
    vms.goToCreate();
    vms.selectSchedulingType({type: 'specific'});
    vms.checkSpecificNodes({includeNodes: hostNames});
  })
})

