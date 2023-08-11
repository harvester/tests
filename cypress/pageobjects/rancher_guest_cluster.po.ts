import type { CypressChainable } from '@/utils/po.types';
import { Constants } from '../constants/constants';
import SettingsPagePo from "@/pageobjects/settings.po";
import LabeledInputPo from '@/utils/components/labeled-input.po';
import LabeledSelectPo from '@/utils/components/labeled-select.po';
import RadioButtonPo from '@/utils/components/radio-button.po'
import { List } from 'cypress/types/lodash';


const constants = new Constants();
const settings = new SettingsPagePo();
var registrationURL;

interface ValueInterface {
    namespace?: string,
    name: string,
    description?: string,
    url?: string,
    size?: string,
    path?: string,
    labels?: any,
    harvester: string,
    cloud_credential: string,
    rke2_cluster_name: string,
}



export class rke_guest_clusterPage {
    
    private search: string = '.input-sm';

    private ns_dropdown_icon = '.ns-dropdown > .icon';
    private ns_dropdown = '.ns-dropdown';
    private all_namespace_item = '#all > .ns-item > div';
    private apps_menu_item = ':nth-child(3) > .header > h6';
    private installed_apps_item = ':nth-child(2) > a > .label';

    private workload_item = ':nth-child(2) > .header';
    private deployment_item = ':nth-child(3) > a';
    private create_deployment = '.actions > .btn';
    private input_deploy_name = 'input[placeholder="A unique name"]';
    private deployment_pod = '#pod > a';
    private add_label_button = '.mb-20 > .key-value > .footer > .btn'
    private label_key = 'input[placeholder="e.g. foo"]';
    private label_value = 'textarea[placeholder="e.g. bar"]';
    private deploy_storage = '#pod > .side-tabs > .tabs > #storage > a > span'; 
    private deploy_storage_dropdown = '#vs14__combobox';
    private deploy_create_pvc = '#vs14__option-4';
    private input_pvc_name = '.bordered-section > :nth-child(1) > :nth-child(1) > .col > .labeled-input > input';
    private deploy_sc_dropdown = '#vs18__combobox';
    private deploy_select_harvester_sc = '#vs18__option-0 > div';
    private deploy_storage_capacity = '.bordered-section > :nth-child(1) > :nth-child(3) > :nth-child(2) > .labeled-input > input';
    private deploy_mount_path = '#mount-path-0';
    private singleNode_read_write = 'span[aria-label="Single-Node Read/Write"]';
    private deploy_container_tab = '#container-0 > a ';
    private container_image_name = 'input[placeholder="e.g. nginx:latest"]';
    private create_nginx_deployment = '.role-primary';
    
    private storage_item = ':nth-child(5) > .header';
    private storage_storageClass = '.list-unstyled > :nth-child(2) > a';
    private persistentVolumeClaims = ':nth-child(4) > a';
    private psersistentVolume = '.list-unstyled > :nth-child(1) > a';

    private serviceDiscoveryitem = ':nth-child(4) > .header';
    private createServiceDiscovery = '.actions > .btn';
    private loadbalancer_SD = ':nth-child(4) > .subtype-container > .subtype-body';

    private lb_url_link = '.details > :nth-child(3) > :nth-child(2)';
    private lb_name_field = 'input[placeholder="A unique name"]';
    private lb_port_field = '.port-name > input';
    private lb_port_number = '.port > input';
    private lb_target_port = '.target-port > input';
    private lb_selector_tab = '#selectors > a';
    private lb_selector_key = '.key > input';
    private lb_selector_value = '.no-resize';
    private lb_addon_config_tab = '#add-on-config > a > span';

    private lb_dhcp_option = '#vs2__combobox > .vs__selected-options > .vs__selected';
    private lb_ipam_selected = '#vs2__combobox > .vs__selected-options';
    private lb_pool_option = '#vs2__option-1 > div';
    private create_lb_button = '.role-primary';


    public visit_globalSettings() {
        cy.visit(constants.rancher_settingPage);
    }

    public visit_virtualizationManagement() {
        cy.visit(constants.rancher_virtualizationManagement);
    }

    public visit_clusterManagement() {
        cy.visit(constants.rancher_clusterManagmentPage);
    }

    public visit_cloudCredential() {
        cy.visit(constants.rancher_cloudCredentialPage);
    }

    public visit_nodeTemplate() {
        cy.visit(constants.rancher_nodeTamplatePage);
    }

    
    public checkState(target: string, expectation: string, valid: boolean = true) {

        cy.wait(1000).get(this.search).then(($search) => {
            cy.wrap($search).click().type(target);
            cy.contains(target).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? expectation : 'Pending', { timeout: constants.timeout.provisionTimeout }).should('be.visible');
        });

    }
    
    public access_guest_cluster(clusterName:string) {
        cy.get('.menu-icon').click();
        cy.get('.cluster-name').contains(clusterName).click();
        cy.log('Access' + clusterName + 'guest cluster management page');
    }

    public visitInstalledApps() {

        cy.get(this.ns_dropdown_icon).click();
        cy.get(this.ns_dropdown).click();
        cy.log('Click the namespace dropdown list');

        cy.get(this.all_namespace_item).click();
        cy.log('Switch to all namespace view');

        cy.get(this.ns_dropdown).click();
        cy.log('Collpase the namespace dropdown');

        cy.get(this.apps_menu_item).contains('Apps').click({force: true});
        cy.log('Click Apps item');

        cy.get(this.installed_apps_item).contains('Installed Apps').click();
        cy.log('Expand Installed Apps');

    }

    public checkCSI_version(csi_driver_name: string) {

        this.checkState(csi_driver_name, 'Deployed');
        cy.log('Checked Harvester csi driver deployed correctly');

        cy.contains(csi_driver_name).parentsUntil('tbody', 'tr').find('[data-testid="sortable-cell-0-2"]').then((el) => {
            let csi_driver_version = el.text();
            console.log('Get: ', csi_driver_version)
            cy.log('csi driver version:' + csi_driver_version);
           
        });
        cy.log('Checked CSI Driver Version');
    }

    public check_cloudProvider_version(cloud_provider_name: string) {

        this.checkState(cloud_provider_name, 'Deployed');
        cy.log('Checked Harvester cloud provider deployed correctly');

        cy.contains(cloud_provider_name).parentsUntil('tbody', 'tr').find('[data-testid="sortable-cell-0-2"]').then((el) => {
            let cloud_provider_version = el.text();
            console.log('Get: ', cloud_provider_version)
            cy.log('csi driver version:' + cloud_provider_version);
           
        });
        cy.log('Checked Cloud Provider Version');


    }

    public deployNginxPVC() {

        cy.get(this.workload_item).contains('Workload').click();
        cy.log('Click Workload item');

        cy.get(this.deployment_item).contains('Deployments').click();
        cy.log('Click Deployments');

        cy.wait(1000).get(this.create_deployment).click();
        cy.log('Click Create Deployments Button');

        cy.get(this.input_deploy_name).type('nginx-pvc');
        cy.log('Input deployment name');
        
        cy.get(this.deployment_pod).contains('Pod').click();
        cy.log('Click Pod Tab');

        cy.get(this.add_label_button).click();
        cy.log('Click Add Label');

        cy.get(this.label_key).type('test');
        cy.get(this.label_value).type('test');
        cy.log('Input test/test to Pod Label');

        cy.get(this.deploy_storage).contains('Storage').click();
        cy.log('Click Storage');

        cy.get(this.deploy_storage_dropdown).click();
        cy.get(this.deploy_create_pvc).click();
        cy.log('Select Create Persistent Volume Claims');

        cy.get(this.input_pvc_name).type('harvester-pvc');
        cy.log('Input Persistent Volume Claims Name')

        cy.get(this.deploy_sc_dropdown).click();
        cy.get(this.deploy_select_harvester_sc).click();
        cy.log('Select Harvester Storage Class');

        cy.get(this.deploy_storage_capacity).type('5');
        cy.log('Input Storage Capacity');

        // cy.get(this.deploy_mount_path).type("/test");
        // cy.log('Input mount path');

        cy.get(this.singleNode_read_write).click();
        cy.log('Select Single-Node Read/Write');

        cy.get(this.deploy_container_tab).contains('container-0').click();
        cy.log('Click Containers Tab');
        
        cy.get(this.container_image_name).type('nginx:latest');
        cy.log('Input Container Image Name');

        cy.get(this.create_nginx_deployment).click();
        cy.wait(2000).log('Click to create Nginx Deployment');
        
    }

    public checkHarvester_PVC() {

        cy.get(this.storage_item).click();
        cy.log('Click Storage');

        cy.get(this.storage_storageClass).click();
        cy.log('Click StorageClasses');

        this.checkState('harvester', 'Active');
        cy.log('Check harvester set as default storage class');

        cy.get(this.persistentVolumeClaims).click();
        cy.log('Click the PersistentVolumeClaims');

        this.checkState('harvester-pvc', 'Bound');
        cy.log('Check harvester-pvc already created and bound');

        cy.get(this.psersistentVolume).click();
        cy.log('Click the PersistentVolumes');

        this.checkState('harvester-pvc', 'Bound');
        cy.log('Check a PVC created with harvester-pvc type');
        
    }

    public checkNginxStatus(target: string, expectation: string, valid: boolean = true) {

        cy.get(this.workload_item).contains('Workload').click();
        cy.log('Click Workload item');

        cy.get(this.deployment_item).contains('Deployments').click();
        cy.log('Click Deployments');

        this.checkState(target, expectation);

    }

    public createLoadBalancer(name:string, type: string) {

        cy.get(this.serviceDiscoveryitem).contains('Service Discovery').click();
        cy.log('Click Service Discovery');

        cy.get(this.createServiceDiscovery).contains('Create').click();
        cy.log('Click Create Button');

        cy.get(this.loadbalancer_SD).contains('Load Balancer').click();
        cy.log('Click Load Balancer');

        cy.get(this.lb_name_field).type(name);
        cy.log('Given Load Balancer Name: ' + name);

        cy.get(this.lb_port_field).type('myport');
        cy.log('Given Port Name: myport');

        cy.get(this.lb_port_number).type('8080');
        cy.log('Given Port number: 8080');

        cy.get(this.lb_target_port).type('80');
        cy.log('Given Targe Port: 80');

        cy.get(this.lb_selector_tab).contains('Selectors').click();
        cy.log('Click Selectors tab');

        cy.get(this.lb_selector_key).type('test');
        cy.get(this.lb_selector_value).type('test');
        cy.wait(1000).log('Given selector key/value: test/test');

        cy.get(this.lb_addon_config_tab).contains('Add-on Config').click();
        cy.log('Add-on Config tab');

        if (type == 'dhcp'){
            cy.get(this.lb_dhcp_option).contains('DHCP');
            cy.log('Check the selected option is DHCP');
        } else if (type == 'pool'){
            cy.get(this.lb_ipam_selected).click();
            cy.get(this.lb_pool_option).contains('Pool').click();
            cy.log('Select Pool option');
        }
        
        cy.get(this.create_lb_button).click();
        cy.log('Click to create Load Balancer');
    }

    public check_DHCP_LB_status (lb_dhcp_name: string) {

        this.checkState(lb_dhcp_name, 'Active');
        cy.log('Checked DHCP Load Balacner exists and active');

        cy.contains(lb_dhcp_name).parentsUntil('tbody', 'tr').find('td.col-link-detail').contains(lb_dhcp_name).click();

        // Check can route to DHCP LB by accessing the URL
        cy.get(this.lb_url_link).then((el) => {
            let lb_dhcp_ip = el.text();
            console.log('Get: ', lb_dhcp_ip);
            cy.log(lb_dhcp_ip);
            cy.task('setGlobalVariable', lb_dhcp_ip);
            let lb_dhcp_url = "http://" + lb_dhcp_ip + ":8080";
            cy.log(lb_dhcp_url);

            cy.origin(lb_dhcp_url, () => {
                cy.visit('/');
                cy.get('h1').contains('Welcome to nginx');
            });

        });

    }

    public check_Pool_LB_status (lb_pool_name: string) {

        this.checkState(lb_pool_name, 'Active');
        cy.log('Checked DHCP Load Balacner exists and active');

        cy.contains(lb_pool_name).parentsUntil('tbody', 'tr').find('td.col-link-detail').contains(lb_pool_name).click();

        // Check can route to Pool LB by accessing the URL
        cy.get(this.lb_url_link).then((el) => {
            let lb_pool_ip = el.text();
            console.log('Get: ', lb_pool_ip);
            cy.log(lb_pool_ip);
            cy.task('setGlobalVariable', lb_pool_ip);
            let lb_pool_url = "http://" + lb_pool_ip + ":8080";
            cy.log(lb_pool_url);

            cy.origin(lb_pool_url, () => {
                cy.visit('/');
                cy.get('h1').contains('Welcome to nginx');
            });

        });

    }

}
