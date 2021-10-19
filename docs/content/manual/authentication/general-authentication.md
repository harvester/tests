---
title: Authentication Validation	
---
1. Enable Access Control . Choose “Allow any valid User” as “Site Access”. Make sure any user is able to access the site.
1. Enable Access Control . Choose “Restrict to Specific User” and add few users. Make sure only the specified users have access to the server. Others should get authentication error.
1. Enable Access Control . Choose “Restrict to Specific User” and add a group. Make sure only all users belonging to the group have access to the server Others should get authentication error.
1. Log in as a normal user (who has access to server but not a member of any environment) , a new default environment should be created for this user with this user account being the owner of the environment.Account entry should get created for this 1. user.
1. Log in as a normal user (who has access to server) , create a new environment. This user should become the owner of the environment.
1. As owner of environment , Add a user as “member” of an environment.Make sure this user gets access to this environment.
1. As owner of environment , Add a user as “owner” of an environment.Make sure this user gets access to this environment. User should also have ability to manage this environment which is to add/delete member of the environment.
1. As owner of environment , Add a group as “member” of an environment.Make sure that all users that belong to this group get access to the environment.
1. As owner of environment , Add a group as “owner” of an environment.Make sure all users of the group gets access to this environment. User should also have ability to manage this environment which is to add/delete member of the environment.
1. As owner of environment , change the role of a member of the environment from “owner” to “member”. Make sure his access control reflects this change.
1. As owner of environment , change the role of a member of the environment from “member” to “owner”. Make sure his access control reflects this change.
1. As owner of environment, remove an existing “owner” member of the environment.Make sure this user does not have access to environment anymore.
1. As owner of environment, remove an existing “member” member of the environment.Make sure this user does not have access to environment anymore.
1. As owner of environment, deactivate the environment. Members of the environment should have no access to environment. Owners should only be able to see in their manage environments but not list of active environments.
1. As owner of environment, Activate a deactivated environment. Members of the environment should now have access to environment.
1. As owner of environment, delete a deactivated environment.Members of the environment should not have access to environment. All hosts relating to the environment should be purged (only hosts created through docker-machine). Custom hosts will not be purged.
1. As admin user, deactivate an existing account. Account should have no access to rancher server.
1. As admin user, activate a deactivated account.Account should get back access to rancher server.
1. As admin user, delete an existing account. Once account is purged, make sure that account is not a member of environments.
1. Log in as a deleted account when account is still not purged.User should have no access to rancher server (like in deactivated state).
1. Log in as a deleted account when account is purged.When user tries to log in , a new account entry will get created and it will not have any access to any existing environment this account had access to before the account was deleted.
1. Delete a user that is a member of the project. List the member of the project , it should return the deleted as member of the project but should reflect the user as “unknown user”.
1. As member user of environment, trying to add a member to environment should fail.
1. As member user of environment, trying to delete an existing member to the environment should fail
1. As member user of environment, trying to deactivate an environment should fail
1. As member user of environment, trying to delete an environment should fail.
1. As member user of environment, trying to change the role of an existing member to the environment should fail.
1. As admin user, change account type of existing "user" to "admin". Check that they have access to "Admin" tab.
## Special Characters relating test cases:
1. User name having special characters ( In this case user DN will have special characters)
1. Group name having special characters( In this case group DN will have special characters)
1. Password having special characters

Test the above 3 test cases , by having "required" site access set for user/group as applicable.
## Local Authentication (Special Cases):
1. Enable Local auth by creating the default admin account.
1. As default admin , create account with type “user”.
1. As default admin , create an account with type “admin”.
1. As created admin accounts , create account with type “user”.
1. As created admin accounts, create an account with type “admin”.
1. Should not be allowed to create 2 accounts with same login user name.
1. Create accounts with entering password manually.
1. Create accounts by generating password.
1. Reset password for accounts.
1. User accounts should not be allowed to create accounts.
## Restrictions
1. No look up for users. So there is no validation done when members are added to site access or when added to environments.
1. When groups needed to be added to site access or environments, it has to be done only by selecting the groups from the list of groups that is presented in the dropdown.
## Upgrade Testing
### On the old version:
1. Enable authentication with admin user (user1).
1. Add group (group1 which has user3 and user4).
1. Add another user (user2).
1. Select Allow members of Environments, plus Authorized Users and Organizations, and Save.
1. Authenticate with user (user3) who belongs to (group1).
1. Log in with user3, an environment should be created called (user3-Default) where user3 is the owner.
1. Log in with user2, an environment should be created called (user2-Default) where user2 is the owner.
1. Add user3 as a "member" in user2-Default environment.
### On the new version:
1. Make sure authentication is enabled.
1. Authenticate with the admin user (user1)
1. Make sure that three environments exists (Default, user2-Default, and user3-Default).
1. Make sure to log in with user2 and user3
1. Log in with user3 and click on Manage Environments, you should see user2-Default and user3-Default.
1. Make sure that you can't edit the user2-Default while you logged in with user3.
1. Make sure that when login with user4 (for the first time), a new environment will be created that called (user4-Default).
