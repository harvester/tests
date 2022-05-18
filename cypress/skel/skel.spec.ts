import { LoginPage } from "../pageobjects/login.po";
import SettingsPage from "../pageobjects/settings.po";
const login = new LoginPage();
const settings = new SettingsPage();

/**
 * 1. Login to the page
 * 2. Edit the Type
 * 3. Save the Changes
 * 4. Validate that the changes saved
 */
export function testSkelTest() {}
describe('Test Skel Page', () => {
    it('Change the type for test skel page', () => {
        login.login();
        settings.goTo();
        const address = 'https://releases.rancher.com/harvester-ui/dashboard/latest/**';
        settings.checkUiSource('External', address);
    });
});

/**
 * 1. Login
 * 2. Change Password
 * 3. Log out
 * 4. Login with new Password
 * @notImplemented
 */
export function changePassword() {};

/**
 * 1. Log in as admin
 * 2. Navigate to user admin page
 * 3. Delete user
 * 4. Log out
 * 5. Try to log in as deleted user
 * 6. Verify that login fails
 * @notImplemented
 */
export function deleteUser() {};