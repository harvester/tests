***** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


**** Test Cases ***
Valid NFS Target
    [setup]     Navigate To Advanced Settings And Edit Option   backup-target
    Given Click Combobox And Select Option      NFS
    And Input NFS Endpoint As   ${BACKUP_NFS_URI}
        Click Save Button
        Click Show Backup Target
    Then Error Message Should Not Exists
    And Navigate To Advanced   Backups
    Then Error Message Should Not Exists In Backups

Invalid NFS Target
    [setup]     Navigate To Advanced Settings And Edit Option   backup-target
    Given Click Combobox And Select Option      NFS
    And Input NFS Endpoint As   ${BACKUP_NFS_URI}/invalid
        Click Save Button
        Click Show Backup Target
    Then Error Message Should Exists
    And Navigate To Advanced   Backups
    Then Error Message Should Exists In Backups

Valid S3 Target
    [setup]     Navigate To Advanced Settings And Edit Option   backup-target
    Given Click Combobox And Select Option      S3
    And Input S3 Infos   ${BACKUP_S3_BUCKET_NAME}   ${BACKUP_S3_BUCKET_REGION}
    ...                  ${BACKUP_S3_KEY_ID}  ${BACKUP_S3_SECRET}
    And Click Save Button
        Click Show Backup Target
    Then Error Message Should Not Exists
    And Navigate To Advanced   Backups
    Then Error Message Should Not Exists In Backups

Invalid S3 Target
    [setup]     Navigate To Advanced Settings And Edit Option   backup-target
    Given Click Combobox And Select Option      S3
    And Input S3 Infos   invalid_bucket_name   invalid_bucket_region
    ...                  invalid_key_id  invalid_secret
    And Click Save Button
        Click Show Backup Target
    Then Error Message Should Exists
    And Navigate To Advanced   Backups
    Then Error Message Should Exists In Backups


**** Keywords ***
Click Combobox And Select Option
    [arguments]     ${option}
    Click Element   xpath://div[./label[contains(text(), "Type")]]/..//div[@role="combobox"]
    Click Element   xpath://ul[@role="listbox"]/li[./div[contains(text(), "${option}")]]

Input NFS Endpoint As
    [arguments]     ${value}
    Input New Text      xpath://div[./label[contains(text(), "Endpoint")]]/Input   ${value}

Input S3 Infos
    [arguments]     ${bucket_name}   ${bucket_region}   ${key_id}   ${secret}
    ...             ${endpoint}=${None}   ${certs}=${None}   ${hosted}=${None}
    Input New Text      xpath://div[./label[contains(text(), "Bucket Name")]]/Input   ${bucket_name}
    Input New Text      xpath://div[./label[contains(text(), "Bucket Region")]]/Input   ${bucket_region}
    Input New Text      xpath://div[./label[contains(text(), "Key ID")]]/Input   ${key_id}
    Input New Text      xpath://div[./label[contains(text(), "Secret")]]/Input   ${secret}
    # TODO: Optional values

Click Save Button
    Scroll Element Into View    xpath://section//button[./span[text()="Save"]]
    Click Button    xpath://section//button[./span[text()="Save"]]
    Wait Until Element Is Visible   xpath://main//header/following-sibling::div
    ...                             timeout=${BROWSER_WAIT_TIMEOUT}

Click Show Backup Target
    Click Button    xpath://button[contains(text(), "Show backup")]

Error Message Should Not Exists
    Sleep   5s
    Wait Until Element Is Not Visible   xpath://div[//button[contains(text(), "backup-target")]]/following-sibling::div[contains(@class, "settings-banner error")]
    ...                                 timeout=${BROWSER_WAIT_TIMEOUT}

Error Message Should Not Exists In Backups
    Sleep   5s
    Wait Until Element Is Not Visible   xpath://main//header/following-sibling::div[contains(@class, "banner error")]
    ...                                 timeout=${BROWSER_WAIT_TIMEOUT}

Error Message Should Exists
    Wait Until Element Is Visible   xpath://div[//button[contains(text(), "backup-target")]]/following-sibling::div[contains(@class, "settings-banner error")]
    ...                             timeout=${BROWSER_WAIT_TIMEOUT}

Error Message Should Exists In Backups
    Wait Until Element Is Visible   xpath://main//header/following-sibling::div[contains(@class, "banner error")]
    ...                             timeout=${BROWSER_WAIT_TIMEOUT}
