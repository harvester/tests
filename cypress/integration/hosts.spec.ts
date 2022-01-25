import { HostsPage } from "../pageobjects/hosts.po";
import { EditYamlPage } from "../pageobjects/editYaml.po";
import { LoginPage } from "../pageobjects/login.po";
const hosts = new HostsPage();
const editYaml = new EditYamlPage();
const login = new LoginPage();

describe('Hosts Page', () => {
    it('should insert custom name into YAML', () => {
        login.login();
        hosts.navigateHostsPage();
        hosts.editHostsYaml();
        editYaml.insertCustomName('This is a custom name');
    });
});