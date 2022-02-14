import { VmsPage } from "../pageobjects/virtualmachine.po";
import { LoginPage } from "../pageobjects/login.po";

const vms = new VmsPage();
const login = new LoginPage();

describe('VM Page', () => {
  it('Create a vm with all the default values', () => {
    login.login();
    vms.goToCreate();
    vms.setDefaultValue();
    vms.save();
  });
});
