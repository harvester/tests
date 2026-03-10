*** Settings ***
Documentation    NVIDIA Driver Toolkit Addon Test Cases
...             This suite tests the enable, disable, and basic functionality
...             of the nvidia-driver-toolkit add-on in Harvester, including interaction with the pcidevices-controller addon.
Test Tags        regression    addons    nvidia-driver-toolkit

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/addon.resource

Suite Setup      Suite Setup For Nvidia Addon Tests
Suite Teardown   Suite Teardown For Nvidia Addon Tests

*** Variables ***
${ADDON_PCIDEVICES}           pcidevices-controller
${PCIDEVICES_NAMESPACE}       harvester-system
${PCIDEVICES_CONTROLLER_LABEL}    app.kubernetes.io/name=harvester-pcidevices-controller
${PCIDEVICES_WEBHOOK_SERVICE}     pcidevices-webhook
${ADDON_NVIDIA_TOOLKIT}       nvidia-driver-toolkit
${NVIDIA_TOOLKIT_NAMESPACE}   harvester-system
${NVIDIA_TOOLKIT_LABEL}       app.kubernetes.io/name=nvidia-driver-toolkit
${NVIDIA_TOOLKIT_SERVICE}     nvidia-driver-toolkit
${INITIAL_STATE_PCIDEVICES}    ${None}
${INITIAL_STATE_NVIDIA_TOOLKIT}    ${None}
${NVIDIA_IMAGE_REPO}          ${NVIDIA_TOOLKIT_IMAGE_REPO}
${NVIDIA_IMAGE_TAG}           ${NVIDIA_TOOLKIT_IMAGE_TAG}
${NVIDIA_DRIVER_LOCATION}     ${NVIDIA_TOOLKIT_DRIVER_LOCATION}

*** Test Cases ***
Test Nvidia Driver Toolkit Addon End-to-End
    [Tags]    p0    coretest    nvidia-driver-toolkit
    [Documentation]    Verify nvidia-driver-toolkit addon can be enabled, configured, and basic functionality works
    ...               Steps:
    ...                   1. Store initial state of pcidevices-controller addon
    ...                   2. Enable pcidevices-controller addon and wait for deployment
    ...                   3. Verify harvester-pcidevices-controller pods are running
    ...                   4. Verify pcidevices-webhook service is running
    ...                   5. Store initial state of nvidia-driver-toolkit addon
    ...                   6. Enable nvidia-driver-toolkit addon and wait for deployment
    ...                   7. Set image repo, tag, and driver location for the addon
    ...                   8. Verify nvidia-driver-toolkit addon configuration is applied
    ...               Expected Result:
    ...                   - Both addons enabled and running
    ...                   - The configuration was correctly applied to the nvidia-driver-toolkit addon
    ...                   - Addons restored to initial state after test

    # Step 1: Store initial state of pcidevices-controller
    Given Initial PCI Addon State Is Captured    ${ADDON_PCIDEVICES}

    # Step 2: Enable pcidevices-controller
    When PCI Devices Addon Is Enabled    ${ADDON_PCIDEVICES}

    # Step 3: Verify controller pods running
    Then PCI Devices Controller Pods Should Be Running    ${PCIDEVICES_NAMESPACE}    ${PCIDEVICES_CONTROLLER_LABEL}

    # Step 4: Verify webhook service running
    And PCI Devices Webhook Service Should Be Running    ${PCIDEVICES_NAMESPACE}    ${PCIDEVICES_WEBHOOK_SERVICE}

    # Step 5: Store initial state of nvidia-driver-toolkit
    Given Initial Nvidia Addon State Is Captured    ${ADDON_NVIDIA_TOOLKIT}

    # Step 6: Enable nvidia-driver-toolkit
    When Nvidia Addon Is Enabled    ${ADDON_NVIDIA_TOOLKIT}

    # Step 7: Set image repo, tag, and driver location
    And Nvidia Toolkit Addon Is Configured    ${ADDON_NVIDIA_TOOLKIT}    ${NVIDIA_IMAGE_REPO}    ${NVIDIA_IMAGE_TAG}    ${NVIDIA_DRIVER_LOCATION}

    # Step 8: Validate addon configuration is applied
    And Nvidia Toolkit Configuration Should Be Applied    ${ADDON_NVIDIA_TOOLKIT}    ${NVIDIA_IMAGE_REPO}    ${NVIDIA_IMAGE_TAG}    ${NVIDIA_DRIVER_LOCATION}

    # Cleanup handled in suite teardown

*** Keywords ***
Initial Nvidia Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the nvidia-driver-toolkit addon
    ${initial_state}=    Addon - Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_NVIDIA_TOOLKIT}    ${initial_state}
    Log    Captured initial nvidia-driver-toolkit addon state: ${initial_state}

Nvidia Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the nvidia-driver-toolkit addon and wait for deployment
    ${is_enabled}=    Addon - Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Addon - Enable    ${addon_name}
    Addon - Wait For Enabled    ${addon_name}    timeout=900
    Log    Nvidia-driver-toolkit addon ${addon_name} is enabled

Nvidia Toolkit Addon Is Configured
    [Arguments]    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    [Documentation]    Set image repo, tag, and driver location for the nvidia-driver-toolkit addon
    Addon - Configure Nvidia Toolkit    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    Log    Nvidia-driver-toolkit addon configured with repo: ${image_repo}, tag: ${image_tag}, driver: ${driver_location}

Nvidia Toolkit Configuration Should Be Applied
    [Arguments]    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    [Documentation]    Verify the nvidia-driver-toolkit addon configuration has been applied
    Addon - Verify Nvidia Toolkit Configured    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    Log    Nvidia-driver-toolkit addon configuration verified successfully

Suite Setup For Nvidia Addon Tests
    [Documentation]    Initialize test environment for nvidia-driver-toolkit addon tests
    Log    Setting up test environment for nvidia-driver-toolkit addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For Nvidia Addon Tests
    [Documentation]    Cleanup and restore addon state after tests
    Log    Running suite teardown for nvidia-driver-toolkit addon tests
    # Restore nvidia-driver-toolkit addon to initial state
    Run Keyword If    '${INITIAL_STATE_NVIDIA_TOOLKIT}' != ${None}
    ...    Addon - Restore State    ${ADDON_NVIDIA_TOOLKIT}    ${INITIAL_STATE_NVIDIA_TOOLKIT}
    # Restore pcidevices-controller addon to initial state
    Run Keyword If    '${INITIAL_STATE_PCIDEVICES}' != 'None'
    ...    Addon - Restore State    ${ADDON_PCIDEVICES}    ${INITIAL_STATE_PCIDEVICES}
    # Standard cleanup
    Cleanup test resources
    Log    Suite teardown completed

Initial PCI Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the addon
    ${initial_state}=    Addon - Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_PCIDEVICES}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

PCI Devices Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the pcidevices-controller addon and wait for deployment
    ${is_enabled}=    Addon - Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Addon - Enable    ${addon_name}
    Addon - Wait For Enabled    ${addon_name}    timeout=900
    Log    PCI Devices addon ${addon_name} is enabled

PCI Devices Controller Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify pcidevices-controller pods are running
    Addon - Wait For Pods Running    ${namespace}    ${label}    timeout=900
    Log    All pcidevices-controller pods are running in ${namespace}

PCI Devices Webhook Service Should Be Running
    [Arguments]    ${namespace}    ${service_name}
    [Documentation]    Verify pcidevices-webhook service is running
    Addon - Wait For Service Running    ${namespace}    ${service_name}    timeout=300
    Log    pcidevices-webhook service is running in ${namespace}

Suite Setup For PCI Devices Addon Tests
    [Documentation]    Initialize test environment for PCI Devices addon tests
    Log    Setting up test environment for PCI Devices addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For PCI Devices Addon Tests
    [Documentation]    Cleanup and restore addon state after tests
    Log    Running suite teardown for PCI Devices addon tests
    Run Keyword If    '${INITIAL_STATE_PCIDEVICES}' != 'None'
    ...    Addon - Restore State    ${ADDON_PCIDEVICES}    ${INITIAL_STATE_PCIDEVICES}
    Cleanup test resources
    Log    Suite teardown completed
