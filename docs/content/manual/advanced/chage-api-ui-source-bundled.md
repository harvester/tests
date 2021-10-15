---
title: Change api-ui-source bundled	
---
1. Log in as admin
1. Navigate to advanced settings
1. Change api-ui-source to bundled
1. Save
1. Refresh page
1. Check page source for dashboard loading location

## Expected Results
1. Log in should complete
1. Settings should save
1. dashboard location should be loading from `/dashboard/_nuxt/`
    - (verify it in browser's developers tools)