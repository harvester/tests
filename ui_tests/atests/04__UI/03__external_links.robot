*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Library             OperatingSystem
Library             yaml
Suite Teardown      Close All Browsers


*** Variables ***
${DOCS_URL}         https://docs.harvesterhci.io/latest/
${FORUMS_URL}       https://forums.rancher.com/c/harvester/
${SLACK_URL}        https://slack.rancher.io
${FILE_ISSUE_URL}   https://github.com/harvester/harvester/issues/new/choose
${Config_FILENAME}  local.yaml
${SUPPORT_DESC}     support bundle description for creation
${BUNDLE_PREFIX}    supportbundle_
${BUNDLE_SUFFIX}    .zip
${DOWNLOAD_TIMEOUT}                 20m
${SUPPORT_Bundle_WAIT_TIMEOUT}      5m


*** Test Cases ***
Links In Community Support Section
    [setup]         Login to Harvester Dashboard And Click Support Link
    [Teardown]      Close Browser
    [Template]      Community Support Section Should Have Link of
    ${DOCS_URL}
    ${FORUMS_URL}
    ${SLACK_URL}
    ${FILE_ISSUE_URL}

Download KubeConfig File
    [setup]         Login to Harvester Dashboard
    [Teardown]      Close Browser
    Given Click Support Link On The Bottom Of Navigation
    And Click Download KubeConfig
    And File Is Downloaded
    Then Folder of Downloads Should Have File As        ${Config_FILENAME}
    And File Should Able To Loaded As YAML              ${Config_FILENAME}

Generate Support Bundle
    [setup]         Login to Harvester Dashboard
    [Teardown]      Close Browser
    Given Click Support Link On The Bottom Of Navigation
    And Click Generate Support Bundle
    And Input Description   ${SUPPORT_DESC}
    Then Create Support Bundle
    When Generate Dialog Disappear
    And File Is Downloaded
    Then Folder Of Downloads Should Have File Like    prefix=${BUNDLE_PREFIX}   suffix=${BUNDLE_SUFFIX}
    # TODO: other critiria to verify support bundle content



*** Keywords ***
Login to Harvester Dashboard And Click Support Link
    Login to Harvester Dashboard
    Click Support Link On The Bottom Of Navigation

Click Support Link On The Bottom Of Navigation
    Click Link      css:div.footer a.pull-right
    Wait Until Element Is Visible       css:main div.banner-graphic     timeout=${BROWSER_WAIT_TIMEOUT}

Community Support Section Should Have Link of
    [arguments]     ${URL}
    Element Should Be Visible   xpath://div[@class="community"]//a[@href='${URL}']

Click Download KubeConfig
    Click Button    xpath://button[contains(text(), "KubeConfig")]

File Is Downloaded
    [Teardown]      Go Back
    Sleep           3s
    Go To           chrome://downloads/
    Sleep           1s
    ${_timeout} =   Get Selenium Timeout
    Set Selenium Timeout    ${DOWNLOAD_TIMEOUT}
    ${result} =     Execute Async Javascript
    ...             var callback = arguments[arguments.length - 1];
    ...             var mgr = document.querySelector('downloads-manager').shadowRoot;
    ...             var item = mgr.querySelector('downloads-item').shadowRoot;
    ...             var show_btn = item.getElementById('show');
    ...             var retry_btn = item.querySelector('cr-button[focus-type="retry"]');
    ...             var retries = 3;
    ...             setInterval(() => {
    ...                 if (show_btn.parentElement.hidden === false) {
    ...                     callback(item.querySelector("#name").innerText);
    ...                 } else if (!retry_btn.parentElement.hidden && retries > 0) {
    ...                     retries--;
    ...                     retry_btn.click();
    ...                 } else if (retries < 0) {
    ...                     callback("download failed");
    ...                 }
    ...             }, 3000);
    Set Selenium Timeout    ${_timeout}
    Should Not Be Empty     ${result}
    Log     File ${result} Downloaded.

Folder of Downloads Should Have File As
    [arguments]     ${filename}
    File Should Exist   ${BROWSER_DOWNLOAD_PATH}/${filename}

File Should Able To Loaded As YAML
    [arguments]     ${filename}
    yaml.Safe Load      ${BROWSER_DOWNLOAD_PATH}/${filename}

Click Generate Support Bundle
    Click Button    xpath://button[contains(text(), "Generate Support Bundle")]

Input Description
    [arguments]     ${desc}
    Input Text      xpath://div[@role='dialog']//div[./label[contains(text(), "Description")]]/textarea
    ...             ${desc}

Create Support Bundle
    Click Button    xpath://div[@role='dialog']//button[@type='submit']

Generate Dialog Disappear
    Wait Until Element Is Not Visible   xpath://div[@role='dialog']
    ...     timeout=${SUPPORT_Bundle_WAIT_TIMEOUT}

Folder Of Downloads Should Have File Like
    [arguments]         ${prefix}=""    ${suffix}=""
    File Should Exist   ${BROWSER_DOWNLOAD_PATH}/${prefix}*${suffix}
