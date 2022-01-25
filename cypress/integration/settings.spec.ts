import { LoginPage } from "../pageobjects/login.po";
import { SettingsPage } from "../pageobjects/settings.po";
import { SidebarPage } from "../pageobjects/sidebar.po";
const login = new LoginPage();
const settings = new SettingsPage();
const sidebar = new SidebarPage();


describe('Advanced Settings Page', () => {
    // it('should navigate to the Advanced Settings Page', () => {
    //     login.login();
    //     sidebar.advancedSettings();
    // });
    // it('should edit the uisource setting', () => {
    //     login.login();
    //     sidebar.advancedSettings();
    //     settings.editUiSource();
    // });
    it('change UI source type to external', () => {
        login.login();
        settings.changeUiSourceType(1);
    });
});
