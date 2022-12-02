import YAML from 'js-yaml'
import { rancherPage } from "@/pageobjects/rancher.po";
import { rke_guest_clusterPage } from "@/pageobjects/rancher_guest_cluster.po";
import { ImagePage } from "@/pageobjects/image.po";
import SettingsPagePo from "@/pageobjects/settings.po";
import NetworkPage from "@/pageobjects/network.po";
import type { CypressChainable } from '@/utils/po.types'
import { Constants } from '../../constants/constants'
import cypress from 'cypress';


const constants = new Constants();
const rancher = new rancherPage();
const rke_guest_cluster = new rke_guest_clusterPage();
const image = new ImagePage();
const settings = new SettingsPagePo();
const network = new NetworkPage();

let rData = {
    name: '',
    harvester_cluster_name: '',
    cloud_credential: '',
    rke1_cluster_name: '',
    rke2_cluster_name: '',
    k3s_cluster_name: '',
    cloud_provider_name: '',
    csi_driver_name: '',
    dhcp_lb_name: '',
    pool_lb_name: '',
    vip_pool_cidr: '',
    vip_pool_namespace: '',
    rke2_cluster_attributes: {
        cpus: '',
        memory: '',
        disk: '',
        namespace: '',
        image: '',
        network_name: '',
        ssh_user: '',
        rke2_latest: '',
        rke2_stable: '',
        k3s_latest: '',
        k3s_stable: '',
        user_data_template: ''
    },
    rke1_cluster_attributes: {
        cpus: '',
        memory: '',
        disk: '',
        namespace: '',
        image: '',
        network_name: '',
        ssh_user: '',
        rke1_latest: '',
        rke1_stable: '',
        user_data_template: ''
    }
};

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
describe('Rancher Integration Test', function() {

    const imageEnv = Cypress.env('image');
    const IMAGE_NAME = imageEnv.name;
    const IMAGE_URL = imageEnv.url;
    
    const value = {
        name: IMAGE_NAME,
        url: IMAGE_URL,
    }

    beforeEach(() => {
        cy.fixture('rancher').then((data) => {
            rData = data;

        });
    })

    it('Prepare Harvester Image', () => {
        cy.login();

        // create IMAGE according to the value set
        image.goToCreate();
        image.create(value);
        image.checkState(value);

    });

    it('Prepare Harvester VLAN network', () => {
        cy.login();

        // Enable network
        settings.enableVLAN('harvester-mgmt')

        // Create vlan1, id:1 virtual network
        network.createVLAN('vlan1', 'default', '1')

    });



    it('Rancher import Harvester', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');
        
        rancher.rancherLogin();
        
        rancher.importHarvester().then((el) => {
            let copyImportUrl = el.text();
            console.log('Get: ', copyImportUrl)
            cy.log(copyImportUrl);
            cy.task('setGlobalVariable', copyImportUrl)
        }).as('importCluster');

    });


    it('Harvester import Rancher', () => {
        cy.login();
        rancher.registerRancher();
    });

    
    it('Check Harvester Cluster Status', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
        
        rancher.visit_virtualizationManagement();

        rancher.checkState(rData.harvester_cluster_name);

    });

    it('Create Cloud Credential', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();

        rancher.createCloudCredential(rData.cloud_credential, rData.harvester_cluster_name);

    });

    it('Provisiong RKE2 Cluster', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
    
        rancher.provision_RKE2_Cluster(rData.rke2_cluster_name, rData.rke2_cluster_attributes);
        
    });

    it('Check RKE2 Cluster Status', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');
        rancher.rancherLogin();

        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);

        rancher.checkState(rData.rke2_cluster_name);

    });

    it('Provisiong K3s Cluster', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
        
        rancher.provision_K3s_Cluster(rData.k3s_cluster_name, rData.rke2_cluster_attributes);
         
    });

    it('Check K3s Cluster Status', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');
        rancher.rancherLogin();

        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);

        rancher.checkState(rData.k3s_cluster_name);

    });

    it('Verify RKE2 CSI driver', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
    
        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);
        rancher.checkState(rData.rke2_cluster_name);
        cy.log('Confirm RKE2 cluster exists and active');

        rke_guest_cluster.access_guest_cluster(rData.rke2_cluster_name);

        rke_guest_cluster.visitInstalledApps();

        rke_guest_cluster.checkCSI_version(rData.csi_driver_name);

        // ToDo: Check whether nginix already deployed prior to the next step
        rke_guest_cluster.deployNginxPVC();
        
        rke_guest_cluster.checkNginxStatus('nginx-pvc', 'Active');
        cy.log('Checked Deploy Nginx Correctly');

        rke_guest_cluster.checkHarvester_PVC();
        
    });

    

    it('Verify RKE2 Cloud Provider', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
    
        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);
        rancher.checkState(rData.rke2_cluster_name);
        cy.log('Confirm RKE2 cluster exists and active');

        rke_guest_cluster.access_guest_cluster(rData.rke2_cluster_name);

        rke_guest_cluster.visitInstalledApps();

        rke_guest_cluster.check_cloudProvider_version(rData.cloud_provider_name);

    });


    it('Verify RKE2 DHDP Load Balancer', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
    
        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);
        rancher.checkState(rData.rke2_cluster_name);
        cy.log('Confirm RKE2 cluster exists and active');

        rke_guest_cluster.access_guest_cluster(rData.rke2_cluster_name);

        rke_guest_cluster.createLoadBalancer(rData.dhcp_lb_name,'dhcp');

        rke_guest_cluster.check_DHCP_LB_status(rData.dhcp_lb_name);

    });

    it('Create Harvester VIP Pool', () => {
        cy.login();

        settings.createVIPpools(rData.vip_pool_namespace, rData.vip_pool_cidr);
        
    });

    it('Create RKE2 Pool Load Balancer', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();
    
        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);
        rancher.checkState(rData.rke2_cluster_name);
        cy.log('Confirm RKE2 cluster exists and active');

        rke_guest_cluster.access_guest_cluster(rData.rke2_cluster_name);

        rke_guest_cluster.createLoadBalancer(rData.pool_lb_name,'pool');

        rke_guest_cluster.check_Pool_LB_status(rData.pool_lb_name);

    });

    it.only('Delete Active RKE2 Cluster', { baseUrl: constants.rancherUrl}, () => {

        cy.visit('/');
        rancher.rancherLogin();

        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);

        rancher.checkState(rData.rke2_cluster_name);

        rancher.delete_rke2_cluster(rData.rke2_cluster_name);

    });

    it('Delete Active K3s Cluster', { baseUrl: constants.rancherUrl}, () => {

        cy.visit('/');
        rancher.rancherLogin();

        cy.wait(1000).visit(constants.rancher_clusterManagmentPage);

        rancher.checkState(rData.k3s_cluster_name);

        rancher.delete_k3s_cluster(rData.k3s_cluster_name);

    });

    it.only('Delete Cloud Credential', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();

        rancher.visit_cloudCredential();

        rancher.checkExists(rData.cloud_credential);

        rancher.delete_cloud_credential(rData.cloud_credential);

    });

    it.only('Delete imported Harveter cluster', { baseUrl: constants.rancherUrl}, () => {
        // cy.login();
        cy.visit('/');

        rancher.rancherLogin();

        rancher.visit_virtualizationManagement();

        rancher.checkExists(rData.harvester_cluster_name);

        rancher.delete_imported_harvester_cluster(rData.harvester_cluster_name);


    });

});


