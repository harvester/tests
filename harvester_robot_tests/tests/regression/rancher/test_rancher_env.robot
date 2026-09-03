*** Settings ***
Documentation    Shared Rancher Test Environment (Setup/Teardown)
...             Imports Harvester into Rancher and creates the shared network/image/
...             credential resources used by the other rancher/ suites, then
...             publishes them via PabotLib so those suites can run in parallel
...             against one shared environment instead of each importing Harvester
...             separately. See rancher-ordering.txt for the intended stage layout:
...             this suite's setup test runs first, the other suites run in
...             parallel after it, then this suite's teardown test runs last.
Test Tags       rancher    rke2    regression
Resource        ../../../keywords/rancher.resource

*** Test Cases ***
Setup Rancher Test Environment
    [Tags]    env    env-setup    env-required
    [Documentation]    Import Harvester into Rancher and create the shared
    ...               network/image/credential resources, then publish them
    ...               for the guestcluster/charts/rbac suites to reuse.
    Suite Setup For Rancher Integration Tests
    Publish Shared Rancher Environment

Teardown Rancher Test Environment
    [Tags]    env    env-teardown    env-required
    [Documentation]    Reload the environment published by the setup test above
    ...               and tear it all down. Must run after every other rancher/
    ...               suite has finished (see rancher-ordering.txt). Safe no-op
    ...               if nothing was published (e.g. the setup test failed
    ...               before reaching Publish Shared Rancher Environment).
    ${status}    ${env_json}=    Run Keyword And Ignore Error
    ...    Get Parallel Value For Key    RANCHER_SHARED_ENV
    IF    '${status}' == 'PASS' and '${env_json}' != '${EMPTY}'
        Load Shared Rancher Environment    ${env_json}
        Suite Teardown For Rancher Integration Tests
    ELSE
        Log    No shared environment was published - nothing to tear down.    console=yes
    END
