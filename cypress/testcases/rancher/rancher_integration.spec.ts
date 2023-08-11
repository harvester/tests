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
describe('Rancher Integration Test', function () {

    const imageEnv = Cypress.env('image');
    // const IMAGE_NAME = imageEnv.name;
    // const IMAGE_URL = imageEnv.url;
    const IMAGE_NAME = 'focal-server-cloudimg-amd64.img';
    const IMAGE_URL = 'https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img';

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
        image.setNameNsDescription(value.name, "default");
        image.setBasics({ url: value.url });
        image.save();
        image.checkState(value);

    });

    it('Prepare Harvester VLAN network', () => {
        cy.login();

        network.createVLAN('vlan1', 'default', '1', 'mgmt')

    });

    it('Rancher import Harvester', { baseUrl: constants.rancherUrl }, () => {
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


    it('Check Harvester Cluster Status', { baseUrl: constants.rancherUrl }, () => {
        // cy.login();
        cy.visit('/');
        cy.wait(5000);

        rancher.rancherLogin();

        rancher.visit_virtualizationManagement();

        rancher.checkState(rData.harvester_cluster_name);

    });



});


