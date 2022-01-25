import { Constants } from "../constants/constants";
const constants = new Constants();

export class HostsPage {
    private hostList = '.host-list';
    private actionsDropdown = '.role-multi-action';
    private editButton = '.icon-edit';
    private editYamlButton = '.icon-file';

    public navigateHostsPage() {
        cy.visit(constants.hostsPage);
        expect(cy.url().should('eq', constants.hostsPage));
    }

    public editHosts() {
        this.navigateHostsPage();
        cy.get(this.actionsDropdown).first().click();
        cy.get(this.editButton).click();
    }

    public editHostsYaml() {
        this.navigateHostsPage();
        cy.get(this.actionsDropdown).first().click();
        cy.get(this.editYamlButton).click();
    }
}