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



export class rancherPage {

    private login_page_usernameInput = '#username';
    private login_page_passwordInput = '#password > .labeled-input > input';
    private login_page_loginButton = '#submit > span';
    private main_page_title = '.title';
    private dashboardURL = 'dashboard/home';

    private boostrap_page_welcome = '.info-box > :nth-child(1)';
    private boostrap_page_boostrapPWInput = 'input';
    private boostrap_page_boostrapPWSubmit = '#submit > span';
    private boostrap_page_radioSelectPW = ':nth-child(2) > .radio-container';
    private boostrap_page_newPWInput = ':nth-child(5) > .password > .labeled-input > input';
    private boostrap_page_newPWRepeat = '[style=""] > .labeled-input > input';
    // private boostrap_page_checkAgreeEULA = '#checkbox-eula > .checkbox-container > .checkbox-custom';
    private boostrap_page_checkAgreeEULA = '[data-testid="setup-agreement"] > .checkbox-container > .checkbox-custom';
    private boostrap_page_confirmLogin = '.btn > span';
    private home_page_mainMenu = '.menu';
    private home_page_virtualManagement = ':nth-child(7) > .option > div';

    private virtual_page_importButton = '.actions > .btn';
    private virtual_page_clusterName = ':nth-child(1) > .labeled-input > input';
    private virtual_page_createCluster = '.cru-resource-footer > div > .role-primary';

    private cloudCredential_page_createButton = '.actions > .btn';
    private cloudCredential_page_harvester = '.subtypes-container > :nth-child(5)';
    private cloudCredential_page_clusterName = 'input[placeholder="A unique name"]';
    private cloudCredential_page_confirmCreate = 'button[class="btn role-primary"]';

    private clusterManagement_page_create = '[href="/dashboard/c/local/manager/provisioning.cattle.io.cluster/create"]';
    private clusterManagement_rke_selector = '.slider';

    private clusterCreation_page_harvester = ':nth-child(4) > .name';

    private rke2Creation_page_clusterName = 'input[placeholder="A unique name for the cluster"]';
    private rke2Creation_page_cpus = '[provider="harvester"] > :nth-child(1) > :nth-child(1) > :nth-child(1) > .labeled-input > input';
    private rke2Creation_page_memory = '[provider="harvester"] > :nth-child(1) > :nth-child(1) > :nth-child(2) > .labeled-input > input';
    private rke2Creation_page_disk = ':nth-child(1) > :nth-child(2) > :nth-child(1) > .labeled-input > input';
    private rke2Creation_page_namespaceCombo = '#vs6__combobox';
    private rke2Creation_page_namespaceOption = '#vs6__option-1';
    private rke2Creation_page_imageCombo = '#vs7__combobox';
    private rke2Creation_page_imageOption = '#vs7__option-0';
    private rke2Creation_page_networkNameCombo = '#vs8__combobox';
    private rke2Creation_page_networkNameOption = '#vs8__option-0';
    private rke2Creation_page_ssh_user = 'input[placeholder="e.g. ubuntu"]';
    private rke2Creation_page_showAdvanced = '.advanced > .hand';
    private rke2Creation_page_userDataInput = ':nth-child(4) > .yaml-editor > .code-mirror > .vue-codemirror > .CodeMirror > .CodeMirror-scroll > .CodeMirror-sizer > [style="position: relative; top: 0px;"] > .CodeMirror-lines > [style="position: relative; outline: none;"] > .CodeMirror-code > [style="position: relative;"] > .CodeMirror-line';

    private rke2Creation_page_k8sCombo = '#vs1__combobox';
    private rke2Creation_page_k8s_rke2Latest = '#vs1__option-1';
    private rke2Creation_page_k8s_rke2Stable = '#vs1__option-2';

    private rke2Creation_page_k8s_k3sLatest = '#vs1__option-4';
    private rke2Creation_page_k8s_k3sStable = '#vs1__option-5';

    private rke2Creation_page_createButton = '.cru-resource-footer > div > .role-primary';

    private search: string = '.input-sm';

    private check_cluster_item = '.row-check';
    private delete_cluster_button = '#promptRemove';
    private confirm_delete_string = '#confirm';
    private confirm_delete_button = '.bg-error';

    // public registration_URL;

    /**
     * First time login using vagrant 
     */
    //  public firstTimeLogin_vagrant() {
    //         cy.exec('cd $VAGRANT_PATH && vagrant ssh rancher_box -c "docker ps --format {{.ID}} | xargs docker logs 2>&1 | grep \'Bootstrap Password:\' | sed \'s/.*Password: //\'"', { env: { VAGRANT_PATH: constants.vagrant_pxe_path} }).then((result) => {
    //             
    //         })

    // }

    /**
     * First time login using ssh 
     */
    public firstTimeLogin() {


        var rancher_vm_ip = (constants.rancherUrl as string).slice(8);
        cy.log(rancher_vm_ip);
        // cy.exec('sshpass -p vagrant ssh vagrant@192.168.0.34 -t "docker ps --format {{.ID}} | xargs docker logs 2>&1 | grep \'Bootstrap Password:\' | sed \'s/.*Password: //\'"', { env: { VM_PASSWORD: constants.rancher_vm_password} }).then((result) => {
        cy.exec('sshpass -p $VM_PASSWORD ssh $VM_USER@$VM_IP -t "docker ps --format {{.ID}} | xargs docker logs 2>&1 | grep \'Bootstrap Password:\' | sed \'s/.*Password: //\'"',
            { env: { VM_PASSWORD: constants.rancher_vm_password, VM_USER: constants.rancher_vm_user, VM_IP: rancher_vm_ip } }).then((result) => {
                cy.log(result.stdout);

                cy.get(this.boostrap_page_boostrapPWInput).type(result.stdout).log('Input bootstrap secret');
                cy.get(this.boostrap_page_boostrapPWSubmit).click();

                // cy.log('Select a specific password to use')
                cy.get(this.boostrap_page_radioSelectPW).click().log('Select a specific password to use');

                // cy.log('Input new password')
                cy.get(this.boostrap_page_newPWInput).type(constants.rancher_password).log('Input new password');
                // cy.log('Confirm password again')
                cy.get(this.boostrap_page_newPWRepeat).type(constants.rancher_password).log('Confirm password again');

                // cy.log('Agree EULA')
                cy.get(this.boostrap_page_checkAgreeEULA).click().log('Agree EULA');

                cy.log('Continue to access rancher')
                cy.get(this.boostrap_page_confirmLogin).click().log('Continue to access rancher');
            })

    }

    /**
     * Rancher login page: Input username and password -> submit 
     */
    public login() {
        cy.get(this.login_page_usernameInput).type(constants.rancher_user).log('Input username');
        cy.get(this.login_page_passwordInput).type(constants.rancher_password).log('Input password');
        cy.get(this.login_page_loginButton).click().log('Login with local user');
    }

    /**
    * Check the rancher landing page is first time login or not
    */
    public rancherLogin() {

        cy.visit('/')
        cy.wait(1000).get('body').then($body => {
            if ($body.find(this.boostrap_page_welcome).length) {
                cy.log('First time login')
                this.firstTimeLogin();

            } else {
                cy.log('Not first time login')
                this.login();
            }

        })

        this.validateLogin()

    }

    /**
    * Validate correctly login to Rancher dashboard page
    */
    public validateLogin() {
        cy.get(this.main_page_title, { timeout: constants.timeout.maxTimeout })
        cy.url().should('contain', constants.rancher_dashboardPage);
    }

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

    public importHarvester() {
        cy.visit('/home')
        cy.get(this.home_page_mainMenu).click();
        cy.get(this.home_page_virtualManagement).should('contain', 'Virtualization Management').click();
        cy.visit(constants.virtualManagePage)
        cy.get(this.virtual_page_importButton).should('contain', 'Import Existing').click();
        cy.get(this.virtual_page_clusterName).type('harvester')
        cy.get(this.virtual_page_createCluster).should('contain', 'Create').click();
        cy.visit(constants.virtualManagePage + '/create#memberRoles');

        cy.contains(constants.rancherUrl, { timeout: 5000 });

        return cy.get('.copy');

    }

    public registerRancher() {

        cy.task('getGlobalVariable').then((globalVar) => {
            const url = (globalVar as string).trim();
            cy.log(url);
            settings.goTo();
            settings.checkIsCurrentPage();
            cy.get('#cluster-registration-url').click();
            cy.get('.icon.icon.icon-edit').click();

            cy.get('input').clear().type(url);

        })

        cy.get('.cru-resource-footer > div > .btn').should('contain', 'Save').click();
    }

    // public checkState(value: ValueInterface, valid: boolean = true) {
    //     cy.get(this.search).type(value.harvester);
    //     // state indicator for status of image upload status e.g. active or uploading
    //     cy.contains(value.harvester).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Pending', { timeout: constants.timeout.provisionTimeout }).should('be.visible');
    // }

    // public selectCluster(value: string) {
    //     const radio = new RadioButtonPo('.vs2__combobox .vs__dropdown-toggle', `:contains("Enabled")`);
    //     radio.input('Enabled');
    //     new LabeledSelectPo('section .labeled-select.hoverable', `:contains("Cluster ")`).select(value)
    // }

    public checkStatus(value: ValueInterface, valid: boolean = true, target: string) {

        let key: keyof ValueInterface;
        for (key in value) {
            if (target == key) {
                cy.log(target);
                // cy.get(this.search).should('be.visible');
                cy.wait(1000).get(this.search).then(($search) => {
                    cy.wrap($search).click().type(value[target]);
                    cy.contains(value[target]).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Pending', { timeout: constants.timeout.provisionTimeout }).should('be.visible');
                });

            } else {
                cy.log('target not found');
            }
        }

    }

    public checkState(target: string, valid: boolean = true) {

        cy.wait(1000).get(this.search).then(($search) => {
            cy.wrap($search).click().type(target);
            cy.contains(target).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Pending', { timeout: constants.timeout.provisionTimeout }).should('be.visible');
        });

    }

    public checkExists(target: string, valid: boolean = true) {
        cy.wait(1000).get(this.search).clear();

        cy.wait(1000).get(this.search).then(($search) => {
            cy.wrap($search).click().type(target);
            // cy.contains(target).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Removing', { timeout: constants.timeout.provisionTimeout }).should('not.exist');
            cy.contains(target).parentsUntil('tbody', 'tr').should('exist', { timeout: constants.timeout.downloadTimeout });
        });

    }

    public checkNotExists(target: string, valid: boolean = true) {
        cy.wait(1000).get(this.search).clear();

        cy.wait(1000).get(this.search).then(($search) => {
            cy.wrap($search).click().type(target);
            // cy.contains(target).parentsUntil('tbody', 'tr').find('td.col-badge-state-formatter').contains(valid ? 'Active' : 'Removing', { timeout: constants.timeout.provisionTimeout }).should('not.exist');
            cy.contains(target).parentsUntil('tbody', 'tr').should('not.exist', { timeout: constants.timeout.downloadTimeout });
        });

    }

    public createCloudCredential(cloud_credential: string, harvester_cluster_name: string) {

        this.visit_cloudCredential();

        cy.wait(1000).get(this.cloudCredential_page_createButton).click();

        cy.get(this.cloudCredential_page_harvester).should('contain', 'Harvester').click();

        cy.get(this.cloudCredential_page_clusterName).type(cloud_credential);

        cy.get('.vs__search').click().then(($list) => {
            cy.contains(harvester_cluster_name).click();
        })

        cy.get(this.cloudCredential_page_confirmCreate).should('contain', 'Create').click();

        cy.contains(cloud_credential);
    }

    public input_RKE2_Cluster_Content(rke2_cluster_attributes: any) {

        this.visit_clusterManagement();

        cy.get(this.clusterManagement_page_create).click();

        // Set RKE2 checkbox back to default
        cy.get('span[class="label no-select hand active"]').then((el) => {
            let active = el.text();
            console.log('Current activate in: ', active)
            cy.log(active);
            if (active == 'RKE2/K3s') {
                cy.get(this.clusterManagement_rke_selector).click();
            }
        })

        // toggle slide
        cy.wait(1000).get(this.clusterManagement_rke_selector).click().then((el) => {

            cy.get(this.clusterCreation_page_harvester).should('contain', 'Harvester').click();

            // Input CPUs
            cy.get(this.rke2Creation_page_cpus).clear().type(rke2_cluster_attributes.cpus);

            // Input Memory
            cy.get(this.rke2Creation_page_memory).clear().type(rke2_cluster_attributes.memory);

            // Input Disk
            cy.get(this.rke2Creation_page_disk).clear().type(rke2_cluster_attributes.disk);

            // Select Namespace
            cy.get(this.rke2Creation_page_namespaceCombo).click().then(($list) => {
                cy.get(this.rke2Creation_page_namespaceOption).should('contain', rke2_cluster_attributes.namespace).click();
            })

            // Select Image
            cy.get(this.rke2Creation_page_imageCombo).click().then(($list) => {
                cy.get(this.rke2Creation_page_imageOption).should('contain', rke2_cluster_attributes.image).click();
            })

            // Select Network
            cy.get(this.rke2Creation_page_networkNameCombo).click().then(($list) => {
                cy.get(this.rke2Creation_page_networkNameOption).should('contain', rke2_cluster_attributes.network_name).click();
            })

            // Input SSH user 
            cy.get(this.rke2Creation_page_ssh_user).type(rke2_cluster_attributes.ssh_user);

            // Click Adanced Settings
            cy.get(this.rke2Creation_page_showAdvanced).click();

            // Input User data
            cy.get(this.rke2Creation_page_userDataInput).type(rke2_cluster_attributes.user_data_template, {
                parseSpecialCharSequences: false,
            });

        })

    }

    public provision_RKE2_Cluster(rke2_name: string, rke2_cluster_attributes: any) {

        this.visit_clusterManagement();

        this.input_RKE2_Cluster_Content(rke2_cluster_attributes)

        // Input RKE2 cluster name
        cy.get(this.rke2Creation_page_clusterName).type(rke2_name);

        // Select Kubernetes version
        cy.get(this.rke2Creation_page_k8sCombo).scrollIntoView().click().then(($list) => {
            cy.get(this.rke2Creation_page_k8s_rke2Latest).should('contain', rke2_cluster_attributes.rke2_latest).click();
        })

        cy.get(this.rke2Creation_page_k8sCombo).scrollIntoView().click().then(($list) => {
            cy.get(this.rke2Creation_page_k8s_rke2Stable).should('contain', rke2_cluster_attributes.rke2_stable).click();
        })

        cy.get(this.rke2Creation_page_k8sCombo).scrollIntoView().click().then(($list) => {
            cy.get(this.rke2Creation_page_k8s_rke2Latest).should('contain', rke2_cluster_attributes.rke2_latest).click();
        })

        // cy.get(this.rke2Creation_page_createButton).click()

        // Click the Create button to start provisioning RKE2 cluster 
        cy.get(this.rke2Creation_page_createButton).click().then((el) => {
            cy.wait(3000).visit(constants.rancher_clusterManagmentPage);
        });

        cy.wait(3000).visit(constants.rancher_clusterManagmentPage);
    }


    public provision_K3s_Cluster(k3s_name: string, rke2_cluster_attributes: any) {

        this.input_RKE2_Cluster_Content(rke2_cluster_attributes)

        // Input RKE2 cluster name
        cy.get(this.rke2Creation_page_clusterName).type(k3s_name);

        // Select Kubernetes version
        cy.get(this.rke2Creation_page_k8sCombo).scrollIntoView().click().then(($list) => {
            cy.get(this.rke2Creation_page_k8s_k3sLatest).should('contain', rke2_cluster_attributes.k3s_latest).click();
        })

        // Confirm to create cluster
        // cy.get(this.rke2Creation_page_createButton).click()

        cy.get(this.rke2Creation_page_createButton).click().then((el) => {
            cy.wait(3000).visit(constants.rancher_clusterManagmentPage);
        });

        cy.wait(3000).visit(constants.rancher_clusterManagmentPage);

    }


    public delete_rke2_cluster(rke2_cluster_name: string) {

        cy.get(this.check_cluster_item).eq(1).click();
        cy.log('Check the RKE2 cluster');

        cy.get(this.delete_cluster_button).click();
        cy.log('Check the Delete cluster button');

        cy.get(this.confirm_delete_string).type(rke2_cluster_name);
        cy.log('Enter the RKE2 cluster name to confirm');

        cy.get(this.confirm_delete_button).click();
        cy.log('Click the doulbe confirm delete button');

        this.checkNotExists(rke2_cluster_name);
    }

    public delete_k3s_cluster(k3s_cluster_name: string) {

        cy.get(this.check_cluster_item).eq(0).click();
        cy.log('Check the K3s cluster');

        cy.get(this.delete_cluster_button).click();
        cy.log('Check the Delete cluster button');

        cy.get(this.confirm_delete_string).type(k3s_cluster_name);
        cy.log('Enter the RKE2 cluster name to confirm');

        cy.get(this.confirm_delete_button).click();
        cy.log('Click the doulbe confirm delete button');

        this.checkNotExists(k3s_cluster_name);

    }


    public delete_cloud_credential(cloud_credential: string) {

        cy.get(this.check_cluster_item).eq(0).click();
        cy.log('Check the cloud credential');

        cy.get(this.delete_cluster_button).click();
        cy.log('Click the Delete button');

        cy.get(this.confirm_delete_button).click();
        cy.log('Click the doulbe confirm delete button');

        cy.contains(cloud_credential).should('not.exist', { timeout: constants.timeout.downloadTimeout });

    }

    public delete_imported_harvester_cluster(harvester_cluster_name: string) {

        cy.get(this.check_cluster_item).eq(0).click();
        cy.log('Check the Harvester Cluster');

        cy.get(this.delete_cluster_button).click();
        cy.log('Click the Delete button');

        cy.get(this.confirm_delete_string).type(harvester_cluster_name);
        cy.log('Enter the Harvester cluster name to confirm');

        cy.get(this.confirm_delete_button).click();
        cy.log('Click the doulbe confirm delete button');

        cy.contains('There are no Harvester Clusters');

    }

}
