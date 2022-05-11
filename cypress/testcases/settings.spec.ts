import { LoginPage } from "../pageobjects/login.po";
import { SettingsPage } from "../pageobjects/settings.po";
import { SidebarPage } from "../pageobjects/sidebar.po";
const login = new LoginPage();
const settings = new SettingsPage();
const sidebar = new SidebarPage();

/**
 * 1. Login
 * 2. Navigate to the Advanced Settings Page via the sidebar
 */
export function navigateAdvanceSettingsPage() {};
describe('should navigate to the Advanced Settings Page', () => {
    it('should navigate to the Advanced Settings Page', () => {
        cy.login();
        sidebar.advancedSettings();
    });
});
/**
 * 1. Login
 * 2. Navigate to the Advanced Settings Page via URL
 * 3. Edit UI Source via UI
 */
export function editUiSource() {};
describe('should edit the uisource setting', () => {
    it('should edit the uisource setting', () => {
        cy.login();
        sidebar.advancedSettings();
        settings.editUiSource();
    });
});
/**
 * 1. Login
 * 2. Navigate to the Advanced Settings Page via URL
 * 3. Edit UI Source via UI
 * 4. Change the UISource Type
 * 5. Validate that the URL changed
 */
export function changeUiSourceType() {};
describe('change UI source type to external', () => {
    it('change UI source type to external', () => {
        cy.login();
        settings.changeUiSourceType(1);
    });
});
