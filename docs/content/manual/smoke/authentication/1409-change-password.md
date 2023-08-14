---
title: Change user password (e2e_fe)
---

* Related issues: [#1409](https://github.com/harvester/harvester/issues/1409) There's no way to change user password in single cluster UI

## Verification Steps
1. Logged in with user
1. Changed password
1. Logged out
1. Logged back in with new password
1. Verified old password didn't work

## Expected Results
1. Password should change and be accepted on new login
1. Old password shouldn't work