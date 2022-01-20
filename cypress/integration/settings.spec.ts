import { LoginPage } from "./pageobjects/login.po";
import { SettingsPage } from "./pageobjects/settings.po";
import { SidebarPage } from "./pageobjects/sidebar.po";
const login = new LoginPage();
const settings = new SettingsPage();
const sidebar = new SidebarPage();


describe('Advanced Settings Page', () => {
    it('should navigate to the Advanced Settings Page', () => {
        login.login();
        login.validateLogin();
        sidebar.advancedSettings();
    });
    it('should edit the uisource setting', () => {
        login.login();
        login.validateLogin();
        sidebar.advancedSettings();
        settings.editUiSource();
    });
    it('change UI source type to external', () => {
        login.login();
        login.validateLogin();
        settings.changeUiSourceType(1);
    });
});
