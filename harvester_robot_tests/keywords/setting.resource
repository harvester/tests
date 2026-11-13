*** Settings ***
Documentation    Setting Keywords
Library          ../libs/keywords/setting_keywords.py
Resource         variables.resource
Resource         common.resource
Resource         storage.resource


*** Variables ***
${LHv2_SETTING_ID}    longhorn-v2-data-engine-enabled
${PR_SETTING_ID}      persistent-reservation-enabled


*** Keywords ***
Enable
    [Arguments]    ${setting_id}
    [Documentation]    Enable setting by ID
    ${setting}=    setting_keywords.enable    ${setting_id}
    Sleep    ${SLEEP_TIMEOUT}    Buffer time before checking
    RETURN    ${setting}

Configured Message Should Be None
    [Arguments]    ${setting_id}
    [Documentation]    Assert configured condition message is None
    ${configured_msg}=    setting_keywords.get_condition_message    ${setting_id}    configured
    Should Be Equal    ${configured_msg}    ${None}

Is Disabled
    [Arguments]    ${setting_id}
    [Documentation]    Assert setting is disabled
    ${value}=    setting_keywords.get_value  ${setting_id}
    Should Not Be Equal    ${value}    true
    Configured Message Should Be None    ${setting_id}

Is Enabled
    [Arguments]    ${setting_id}
    [Documentation]    Assert setting is enabled
    ${value}=    setting_keywords.get_value  ${setting_id}
    Should Be Equal    ${value}    true
    Configured Message Should Be None    ${setting_id}

# longhorn-v2-data-engine-enabled
Enable LHv2 Data Engine
    [Documentation]    Enable Setting ``${LHv2_SETTING_ID}``
    Enable    ${LHv2_SETTING_ID}

LHv2 Data Engine Is Disabled
    [Documentation]    Check Setting ``${LHv2_SETTING_ID}`` is ``false`` and no v2 pods
    Is Disabled    ${LHv2_SETTING_ID}
    storage.Standard Nodes Have No v2 IM Pods

LHv2 Data Engine Is Enabled
    [Documentation]    Check Setting ``${LHv2_SETTING_ID}`` is ``true`` and v2 pods are running
    Is Enabled    ${LHv2_SETTING_ID}
    storage.Standard Nodes Have Running v2 IM Pods

Wait Until LHv2 Data Engine Is Enabled
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    LHv2 Data Engine Is Enabled


# generic
Setting Default Should Be
    [Arguments]    ${setting_id}    ${expected}
    [Documentation]    Assert the setting exists and has the expected default
    ${default}=    setting_keywords.get_default    ${setting_id}
    Should Be Equal As Strings    ${default}    ${expected}
    ...    msg=Setting ${setting_id} default is '${default}', expected '${expected}'

Get Setting Value
    [Arguments]    ${setting_id}
    [Documentation]    Return the setting's raw value (None when unset)
    ${value}=    setting_keywords.get_value    ${setting_id}
    RETURN    ${value}

Get Setting Effective Value
    [Arguments]    ${setting_id}
    [Documentation]    Return the setting's value, or its default when unset
    ${value}=    setting_keywords.get_effective_value    ${setting_id}
    RETURN    ${value}

Update Setting
    [Arguments]    ${setting_id}    ${value}
    [Documentation]    Set the setting's value. ${None} removes the value, so
    ...    the default applies again.
    setting_keywords.update    ${setting_id}    ${value}

Try To Update Setting
    [Arguments]    ${setting_id}    ${value}
    [Documentation]    Attempt a setting update that may be rejected by the
    ...    setting webhook. Returns a result dict {success, code, message}.
    ${result}=    setting_keywords.try_update    ${setting_id}    ${value}
    RETURN    ${result}

Get KubeVirt Configuration
    [Documentation]    Return spec.configuration of the harvester-system/kubevirt CR
    ${configuration}=    setting_keywords.get_kubevirt_configuration
    RETURN    ${configuration}

# persistent-reservation-enabled
KubeVirt Persistent Reservation Is
    [Arguments]    ${enabled}
    [Documentation]    Single-shot assertion backing
    ...    `KubeVirt Persistent Reservation Should Be`
    ${configuration}=    Get KubeVirt Configuration
    ${pr}=    Evaluate    $configuration.get('persistentReservationConfiguration')
    Should Not Be Equal    ${pr}    ${None}
    ...    msg=KubeVirt CR has no persistentReservationConfiguration
    Dictionary Should Contain Key    ${pr}    enabled
    ...    msg=KubeVirt persistentReservationConfiguration has no explicit enabled field: ${pr}
    Should Be Equal As Strings    ${pr}[enabled]    ${enabled}    ignore_case=True
    ...    msg=KubeVirt persistentReservationConfiguration is ${pr}, expected enabled=${enabled}

KubeVirt Persistent Reservation Should Be
    [Arguments]    ${enabled}
    [Documentation]    Wait until the KubeVirt CR explicitly sets
    ...    spec.configuration.persistentReservationConfiguration.enabled to
    ...    ${enabled} (the setting controller writes it asynchronously).
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    KubeVirt Persistent Reservation Is    ${enabled}

Virt Handler Pods Are Ready With pr-helper
    [Arguments]    ${present}
    [Documentation]    Single-shot assertion backing
    ...    `Virt Handler Pods Should Have pr-helper`
    ${pods}=    List Pods By Label    harvester-system    kubevirt.io=virt-handler
    Should Not Be Empty    ${pods}    msg=No virt-handler pods found
    FOR    ${pod}    IN    @{pods}
        Should Be Equal    ${pod.metadata.deletion_timestamp}    ${None}
        ...    msg=virt-handler pod ${pod.metadata.name} is being deleted
        Should Be Equal As Strings    ${pod.status.phase}    Running
        ...    msg=virt-handler pod ${pod.metadata.name} is ${pod.status.phase}
        ${containers}=    Evaluate    [c.name for c in $pod.spec.containers]
        ${ready}=    Evaluate    all(s.ready for s in ($pod.status.container_statuses or []))
        Should Be True    ${ready}
        ...    msg=virt-handler pod ${pod.metadata.name} is not ready
        IF    ${present}
            Should Contain    ${containers}    pr-helper
            ...    msg=virt-handler pod ${pod.metadata.name} has no pr-helper container: ${containers}
        ELSE
            Should Not Contain    ${containers}    pr-helper
            ...    msg=virt-handler pod ${pod.metadata.name} still has a pr-helper container
        END
    END

Virt Handler Pods Should Have pr-helper
    [Arguments]    ${present}=${True}
    [Documentation]    Wait until every virt-handler pod is Running and ready,
    ...    with (present=${True}) or without (present=${False}) the
    ...    pr-helper container that virt-operator adds when persistent
    ...    reservation is enabled.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Virt Handler Pods Are Ready With pr-helper    ${present}
