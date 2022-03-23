import { HostsPage } from "../pageobjects/hosts.po";
import { EditYamlPage } from "../pageobjects/editYaml.po";
import { LoginPage } from "../pageobjects/login.po";
const hosts = new HostsPage();
const editYaml = new EditYamlPage();
const login = new LoginPage();

/**
 * This will insert custom YAML into the hosts page while editing
 */
export function insertCustomYAML() {}
it('should insert custom name into YAML', () => {
    cy.login();
    hosts.navigateHostsPage();
    hosts.editHostsYaml();
    editYaml.insertCustomName('This is a custom name');
});
