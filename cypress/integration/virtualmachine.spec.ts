import { VmsPage } from "../pageobjects/virtualmachine.po";
import { LoginPage } from "../pageobjects/login.po";

const vms = new VmsPage();
const login = new LoginPage();

describe('VM Page', () => {
  it('Create a vm with all the default values', () => {
    login.login();
    vms.goToCreate();

    const defaultValue = {
      namespace: 'default',
      name: 'test-vm-name-automation',
      description: 'test-vm-description-automation',
      cpu: '2',
      memory: '4',
      image: 'ubuntu-18.04-server-cloudimg-amd64.img',
      network: 'vlan1',
    }
    vms.setValue(defaultValue);

    vms.save();
  });
});
