*** Settings ***
Documentation    Server-side pagination (SQL cache) of the lists of the Harvester API.
...    See https://github.com/harvester/harvester/issues/9513 and
...    https://github.com/harvester/harvester/pull/12145.
...    The expectations come from the Kubernetes API or from the VMs of the suite.
Test Tags         list-api    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource
Resource    ../../../keywords/list_api.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
&{TEST_VM}
@{VM_NAMES}                 vm-a    vm-b    vm-c    vm-d    vm-e
# The display names sort differently than the names
@{VM_DISPLAY_NAMES}         Web 2    DB 1    Web 1    Web Server    DB 2
@{VMS_BY_DISPLAY_NAME}      vm-b    vm-e    vm-c    vm-a    vm-d
@{NS_GROUPS}                a    a    b
&{CONFIG_MAP_GROUPS}        cm-a1=a    cm-a2=a    cm-b1=b    cm-none=${EMPTY}
# The types whose list no other suite changes while this one runs, so it can be compared
# with the Kubernetes list. Not the storage classes: every image creates one.
@{STABLE_TYPES}
...    node    harvesterhci.io.setting    harvesterhci.io.addon
...    devices.harvesterhci.io.pcidevice    devices.harvesterhci.io.usbdevice
...    devices.harvesterhci.io.sriovgpudevice    devices.harvesterhci.io.vgpudevice
...    devices.harvesterhci.io.sriovnetworkdevice
# The types the UI lists, a type that the cluster does not have is skipped
@{OTHER_TYPES}
...    node    namespace    persistentvolumeclaim    secret    configmap    event    pod
...    storage.k8s.io.storageclass    kubevirt.io.virtualmachineinstance
...    k8s.cni.cncf.io.network-attachment-definition    harvesterhci.io.virtualmachineimage
...    harvesterhci.io.virtualmachinetemplate    harvesterhci.io.virtualmachinetemplateversion
...    harvesterhci.io.keypair    harvesterhci.io.setting    harvesterhci.io.addon
...    devices.harvesterhci.io.pcidevice    devices.harvesterhci.io.usbdevice
...    devices.harvesterhci.io.usbdeviceclaim    devices.harvesterhci.io.sriovgpudevice
...    devices.harvesterhci.io.vgpudevice    devices.harvesterhci.io.sriovnetworkdevice
# The namespaces the support bundle collects by default, see DefaultNamespaces() in harvester
@{SUPPORT_BUNDLE_NAMESPACES}
...    cattle-dashboards    cattle-fleet-local-system    cattle-fleet-system
...    cattle-fleet-clusters-system    cattle-monitoring-system    fleet-local
...    harvester-system    local    longhorn-system    cattle-logging-system
...    cattle-provisioning-capi-system


*** Test Cases ***
VM List Matches Kubernetes
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then Query Should Match Kubernetes    ${VM_PATH}/${VM_NS}
    ...    apis/kubevirt.io/v1/namespaces/${VM_NS}/virtualmachines

List Without Sort Is Ordered By Namespace And Name
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${VM_NAMES}

Other Namespace Has No Test VM
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${test_ids}=    Prefixed IDs    ${VM_NS}    @{VM_NAMES}
    Then Query Should Not Contain IDs    ${VM_PATH}/default    ${test_ids}

Projects Or Namespaces Selects The Namespace
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${expected}=    Prefixed IDs    ${VM_NS}    @{VM_NAMES}
    Then Query IDs Should Be    ${VM_PATH}    ${expected}
    ...    projectsornamespaces=${VM_NS}    sort=metadata.name

Filter By Exact Name
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-a'] }}    filter=metadata.name=vm-a

Equals Is Exact And Tilde Is Partial
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${NO_IDS}    filter=metadata.name=vm-
    And VM Query Should Return    ${VM_NAMES}    filter=metadata.name~vm-    sort=metadata.name

Sort By Name
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${VM_NAMES}    sort=metadata.name
    And VM Query Should Return    ${VM_NAMES}[::-1]    sort=-metadata.name

Sort By Display Name
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${VMS_BY_DISPLAY_NAME}    sort=${DISPLAY_NAME_FIELD}
    And VM Query Should Return    ${VMS_BY_DISPLAY_NAME}[::-1]    sort=-${DISPLAY_NAME_FIELD}

Sort By Status Then By Name
    [Documentation]    All VMs have the same status
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${VM_NAMES}[::-1]    sort=status.printableStatus,-metadata.name

Pages Of A Sorted List
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${expected}=    Prefixed IDs    ${VM_NS}    @{VM_NAMES}
    Then Pages Should Hold    ${VM_PATH}/${VM_NS}    ${expected}    sort=metadata.name    pagesize=2
    And VM Query Should Return    ${{ ['vm-c', 'vm-b'] }}    sort=-metadata.name    page=2    pagesize=2

Continue And Next Link Return The Same Page
    [Documentation]    continue is ignored, so the pagination.next link returns the first page again
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${first}=    When Query    ${VM_PATH}/${VM_NS}    sort=metadata.name    pagesize=2
    Then Should Not Be Empty    ${first}[body][continue]
    And Query IDs Should Be    ${VM_PATH}/${VM_NS}    ${first}[ids]    sort=metadata.name    pagesize=2
    ...    continue=${first}[body][continue]
    ${next}=    Relative Link    ${first}[body][pagination][next]
    And Query IDs Should Be    ${next}    ${first}[ids]

Page Size Larger Than The List
    [Documentation]    The first page has all VMs, the page after it is empty and has the total count
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${expected}=    Prefixed IDs    ${VM_NS}    @{VM_NAMES}
    Then Pages Should Hold    ${VM_PATH}/${VM_NS}    ${expected}    sort=metadata.name    pagesize=50

Filter By Status
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${VM_NAMES}    filter=${STOPPED}    sort=metadata.name
    And VM Query Should Return    ${NO_IDS}    filter=status.printableStatus=Running

Filter By Display Name Partial
    [Documentation]    The partial match ignores the case
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-a', 'vm-c', 'vm-d'] }}
    ...    filter=${DISPLAY_NAME_FIELD}~Web    sort=metadata.name
    And VM Query Should Return    ${{ ['vm-a', 'vm-c', 'vm-d'] }}
    ...    filter=${DISPLAY_NAME_FIELD}~web    sort=metadata.name

Filter By Display Name Exact
    [Documentation]    = matches the whole value, a part of it is not found
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-c'] }}    filter=${DISPLAY_NAME_FIELD}="Web 1"
    And VM Query Should Return    ${NO_IDS}    filter=${DISPLAY_NAME_FIELD}=Web

Filter Value With A Space Has To Be Quoted
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-d'] }}    filter=${DISPLAY_NAME_FIELD}~"Web Server"
    And Query Should Be Rejected    ${VM_PATH}/${VM_NS}    filter=${DISPLAY_NAME_FIELD}~Web Server

Comma Is OR
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-a', 'vm-b'] }}
    ...    filter=metadata.name=vm-a,metadata.name=vm-b    sort=metadata.name
    And VM Query Should Return    ${{ ['vm-a', 'vm-e'] }}
    ...    filter=metadata.name=vm-a,${DISPLAY_NAME_FIELD}="DB 2"    sort=metadata.name

Several Filters Are AND
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${filters}=    Create List    ${DISPLAY_NAME_FIELD}~Web    ${DISPLAY_NAME_FIELD}~1
    Then VM Query Should Return    ${{ ['vm-c'] }}    filter=${filters}

Filter Operators
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${{ ['vm-b', 'vm-c', 'vm-d', 'vm-e'] }}
    ...    filter=metadata.name!=vm-a    sort=metadata.name
    And VM Query Should Return    ${{ ['vm-a', 'vm-c'] }}
    ...    filter=metadata.name in (vm-a,vm-c)    sort=metadata.name
    And VM Query Should Return    ${{ ['vm-b', 'vm-d', 'vm-e'] }}
    ...    filter=metadata.name notin (vm-a,vm-c)    sort=metadata.name

Not Indexed Field Is Rejected
    [Documentation]    Only the display name and the status are indexed on top of
    ...    the defaults of Steve, computed values like the CPU cannot be indexed
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then Query Should Be Rejected    ${VM_PATH}/${VM_NS}    422    sort=spec.runStrategy
    And Query Should Be Rejected    ${VM_PATH}/${VM_NS}    422    sort=spec.template.spec.domain.cpu.cores
    And Query Should Be Rejected    ${VM_PATH}/${VM_NS}    422    filter=spec.runStrategy=Halted
    And Query Should Be Rejected    ${VM_PATH}/${VM_NS}    422    filter=metadata.annotations[harvesterhci.io/no-such-annotation]=x

Selectors Limit And Continue Are Ignored
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${no_match}=    Create Dictionary    labelSelector=no-such-label=no-such-value
    ${no_vm}=    Create Dictionary    fieldSelector=metadata.name=no-such-vm
    ${limit}=    Create Dictionary    limit=1
    ${bad_continue}=    Create Dictionary    limit=1    continue=not-a-token
    FOR    ${params}    IN    ${no_match}    ${no_vm}    ${limit}    ${bad_continue}
        Then VM Query Should Return    ${VM_NAMES}    sort=metadata.name    &{params}
    END

Value That Looks Like SQL Is Harmless
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    Then VM Query Should Return    ${NO_IDS}    filter=${DISPLAY_NAME_FIELD}~x';DROP
    And VM Query Should Return    ${VM_NAMES}

Wildcards Of A Partial Match Are Literal
    [Tags]    p1
    [Teardown]    Run Keywords    Delete VMs And Wait Until Gone    vm-wild-1    vm-wild-2    vm-wild-3    vm-wild-4
    ...    AND    Common Test Teardown
    Given Stopped VM is created    vm-wild-1    ${EMPTY}    &{TEST_VM}
    ...    annotations=${{ {$DISPLAY_NAME: '100%'} }}
    And Stopped VM is created    vm-wild-2    ${EMPTY}    &{TEST_VM}
    ...    annotations=${{ {$DISPLAY_NAME: '1000'} }}
    And Stopped VM is created    vm-wild-3    ${EMPTY}    &{TEST_VM}
    ...    annotations=${{ {$DISPLAY_NAME: 'a_c'} }}
    And Stopped VM is created    vm-wild-4    ${EMPTY}    &{TEST_VM}
    ...    annotations=${{ {$DISPLAY_NAME: 'abc'} }}
    And Wait Until VM Query Returns    ${{ ['vm-wild-4'] }}    filter=${DISPLAY_NAME_FIELD}=abc
    Then VM Query Should Return    ${{ ['vm-wild-1'] }}    filter=${DISPLAY_NAME_FIELD}~100%
    And VM Query Should Return    ${{ ['vm-wild-3'] }}    filter=${DISPLAY_NAME_FIELD}~a_c

Display Name Change Is Found
    [Tags]    p1
    [Teardown]    Run Keywords    VM annotation is set    vm-e    ${DISPLAY_NAME}    DB 2    ${VM_NS}
    ...    AND    Common Test Teardown
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    When VM annotation is set    vm-e    ${DISPLAY_NAME}    Renamed    ${VM_NS}
    Then Wait Until VM Query Returns    ${{ ['vm-e'] }}    filter=${DISPLAY_NAME_FIELD}=Renamed
    And VM Query Should Return    ${NO_IDS}    filter=${DISPLAY_NAME_FIELD}="DB 2"

New VM Is Listed And Deleted VM Is Gone
    [Tags]    p1
    [Teardown]    Run Keywords    Run Keyword And Ignore Error    VM is deleted    vm-extra    ${VM_NS}
    ...    AND    Common Test Teardown
    When Stopped VM is created    vm-extra    ${EMPTY}    &{TEST_VM}
    Then Wait Until Keyword Succeeds    2 min    3 s    VM Should Be Listed    vm-extra
    When VM is deleted    vm-extra    ${VM_NS}
    Then Wait Until Keyword Succeeds    2 min    3 s    VM Should Be Listed    vm-extra    ${FALSE}

Status Change Is Indexed
    [Documentation]    Boots a VM from a container disk of a public registry (docker.io). The CI
    ...    feeds its clusters from its own artifact server, nothing shows that it can pull it.
    [Tags]    p1    -pr-baseline
    [Teardown]    Run Keywords    Delete VM And Wait Until Gone    vm-run
    ...    AND    Common Test Teardown
    Given Stopped VM is created    vm-run    ${EMPTY}    &{TEST_VM}
    And Wait Until Keyword Succeeds    2 min    3 s
    ...    VM Should Be Listed    vm-run    ${TRUE}    filter=${STOPPED}
    When VM is started    vm-run    ${VM_NS}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}s    3 s
    ...    VM Should Be Listed    vm-run    ${TRUE}    filter=${RUNNING}
    When VM is stopped    vm-run    ${VM_NS}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}s    3 s
    ...    VM Should Be Listed    vm-run    ${TRUE}    filter=${STOPPED}

Delete Through The VM Store Removes The Selected Disks
    [Documentation]    The VM store wraps the default store of Steve, its delete still
    ...    removes the PVCs of the disks in removedDisks. Needs the fix of harvester/harvester#12444:
    ...    without it the delete fails in the first seconds after the creation. With it, the
    ...    store answers 409 until Wrangler has set the cleanup finalizer, the delete is retried.
    [Tags]    p1
    [Teardown]    Run Keywords    Run Keyword And Ignore Error    Delete VM And Wait Until Gone    vm-pvc
    ...    AND    Common Test Teardown
    # vm/rest.py ignores extra_disks
    Skip If    '%{HARVESTER_OPERATION_STRATEGY=crd}'.lower() == 'rest'
    ...    The blank data disk needs the CRD operation strategy
    &{disk}=    Create Dictionary    size=1Gi
    Given Stopped VM is created    vm-pvc    ${EMPTY}    &{TEST_VM}    extra_disks=${{ [$disk] }}
    And Wait Until Keyword Succeeds    2 min    3 s    Volume Is Present    vm-pvc-disk-1    ${VM_NS}
    And Wait Until Keyword Succeeds    2 min    3 s    VM Should Be Listed    vm-pvc
    When Wait Until Keyword Succeeds    30 s    1 s    VM is deleted through the Harvester API
    ...    vm-pvc    ${VM_NS}    removed_disks=vm-pvc-disk-1
    Then Wait Until Keyword Succeeds    2 min    3 s    VM Should Be Listed    vm-pvc    ${FALSE}
    And Wait Until Volume Is Deleted    vm-pvc-disk-1    ${VM_NS}

VM Schema Columns And Date Fields
    [Documentation]    The columns contain Name and point to metadata.fields[N],
    ...    date columns hold a timestamp instead of a duration
    [Tags]    p1
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${columns}=    Then Schema Columns Should Point To Metadata Fields    kubevirt.io.virtualmachine
    And Date Columns Should Be Timestamps    ${VM_PATH}/${VM_NS}    ${columns}

Every API Server Replica Lists The Same
    [Documentation]    Every replica has a cache of its own
    [Tags]    p2
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${pods}=    And API Server Pods
    FOR    ${pod}    IN    @{pods}
        Then VM Query Should Return    ${VM_NAMES}    pod=${pod}    sort=metadata.name
    END

Every API Server Replica Sees A Change
    [Tags]    p2
    [Teardown]    Run Keywords    VM annotation is set    vm-e    ${DISPLAY_NAME}    DB 2    ${VM_NS}
    ...    AND    Common Test Teardown
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${pods}=    And API Server Pods
    When VM annotation is set    vm-e    ${DISPLAY_NAME}    Replicated    ${VM_NS}
    FOR    ${pod}    IN    @{pods}
        Then Wait Until VM Query Returns    ${{ ['vm-e'] }}    pod=${pod}
        ...    filter=${DISPLAY_NAME_FIELD}=Replicated
    END

Namespace List Has The Namespaces
    [Tags]    p1    namespaces
    ${names}=    Namespace Names    1    2    3
    Given Namespaces should be listed    ${names}
    ${expected}=    Create List    @{names}    default    harvester-system
    Then Query Should Contain IDs    ${NAMESPACE_PATH}    ${expected}

Namespaces Filter By Label
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    ${group_a}=    Namespace Names    1    2
    ${group_b}=    Namespace Names    3
    Given Namespaces should be listed    ${all}
    # The name filter leaves out the namespaces of other runs of the suite
    ${in_a}=    Create List    ${GROUP_LABEL_FIELD}=a    metadata.name~${NS_PREFIX}
    ${in_b}=    Create List    ${GROUP_LABEL_FIELD}=b    metadata.name~${NS_PREFIX}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${group_a}    filter=${in_a}    sort=metadata.name
    And Query IDs Should Be    ${NAMESPACE_PATH}    ${group_b}    filter=${in_b}    sort=metadata.name

Namespaces Filter By Label With In
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    Given Namespaces should be listed    ${all}
    ${filters}=    Create List    ${GROUP_LABEL_FIELD} in (a,b)    metadata.name~${NS_PREFIX}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${all}    filter=${filters}    sort=metadata.name

Namespaces Filter By Label Existence
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    Given Namespaces should be listed    ${all}
    ${exists}=    Create List    ${GROUP_LABEL_FIELD}    metadata.name~${NS_PREFIX}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${all}    filter=${exists}    sort=metadata.name
    ${missing}=    Create List    !${GROUP_LABEL_FIELD}    metadata.name~${NS_PREFIX}
    And Query IDs Should Be    ${NAMESPACE_PATH}    ${NO_IDS}    filter=${missing}

Namespaces Sort By Name
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    Given Namespaces should be listed    ${all}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${all}[::-1]    filter=metadata.name~${NS_PREFIX}    sort=-metadata.name

Namespace Pages Have The Total Count
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    Given Namespaces should be listed    ${all}
    Then Pages Should Hold    ${NAMESPACE_PATH}    ${all}    filter=metadata.name~${NS_PREFIX}
    ...    sort=metadata.name    pagesize=2

Namespaces Projects Or Namespaces
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    ${wanted}=    Namespace Names    1    2
    Given Namespaces should be listed    ${all}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${wanted}
    ...    projectsornamespaces=${NS_PREFIX}-1,${NS_PREFIX}-2    sort=metadata.name

Underscore Of A Partial Match Is Literal
    [Tags]    p1    namespaces
    ${names}=    Namespace Names    1    2    3
    [Teardown]    Run Keywords    Restore Namespace Groups    ${names}    ${NS_GROUPS}
    ...    AND    Common Test Teardown
    Given Namespaces should be listed    ${names}
    When Namespace labels are updated through the Harvester API    ${names}[0]
    ...    ${{ {$GROUP_LABEL: 'ab_cd'} }}
    And Namespace labels are updated through the Harvester API    ${names}[1]
    ...    ${{ {$GROUP_LABEL: 'abxcd'} }}
    ${filters}=    Create List    ${GROUP_LABEL_FIELD}~ab_cd    metadata.name~${NS_PREFIX}
    Then Wait Until Keyword Succeeds    2 min    3 s
    ...    Query IDs Should Be    ${NAMESPACE_PATH}    ${names}[0:1]    filter=${filters}

Support Bundle Link Has The Default Namespaces That Exist
    [Tags]    p1    namespaces
    ${expected}=    Given Existing Namespaces Among    ${SUPPORT_BUNDLE_NAMESPACES}
    Then Query IDs And Count Should Be    ${NAMESPACE_PATH}    ${expected}    link=supportbundle

Namespace Create Update And Delete
    [Documentation]    The namespace store wraps the default store, create, update and delete have to work
    [Tags]    p1    namespaces
    ${name}=    Generate Unique Name    ssp-crud
    [Teardown]    Run Keywords    Run Keyword And Ignore Error    Namespace is deleted through the Harvester API    ${name}
    ...    AND    Common Test Teardown
    ${labels}=    Namespace Group Labels    crud
    When Namespace is created through the Harvester API    ${name}    ${labels}
    Then Wait Until Keyword Succeeds    2 min    3 s    Namespace Should Have Label    ${name}    ${GROUP_LABEL}    crud
    And Query IDs Should Be    ${NAMESPACE_PATH}    ${{ [$name] }}    filter=metadata.name=${name}
    And Namespace Should Be Gone    ${name}-unknown

    ${updated}=    Namespace Group Labels    updated
    When Namespace labels are updated through the Harvester API    ${name}    ${updated}
    Then Wait Until Keyword Succeeds    2 min    3 s    Namespace Should Have Label    ${name}    ${GROUP_LABEL}    updated

    When Namespace is deleted through the Harvester API    ${name}
    Then Wait Until Keyword Succeeds    2 min    3 s    Namespace Should Be Gone    ${name}

Filter Config Maps By The Value Of A Label
    [Tags]    p1    namespaces
    Given Config maps should be listed
    Then Config Maps Should Be    ${{ ['cm-a1', 'cm-a2'] }}    ${GROUP_LABEL_FIELD}=a
    And Config Maps Should Be    ${{ ['cm-b1'] }}    ${GROUP_LABEL_FIELD}=b

Filter Config Maps By A Label With In
    [Tags]    p1    namespaces
    Given Config maps should be listed
    Then Config Maps Should Be    ${{ ['cm-a1', 'cm-a2', 'cm-b1'] }}    ${GROUP_LABEL_FIELD} in (a,b)

Filter Config Maps By The Name With In
    [Tags]    p1    namespaces
    Given Config maps should be listed
    Then Config Maps Should Be    ${{ ['cm-a1', 'cm-none'] }}    metadata.name in (cm-a1,cm-none)

Filter A Cluster Scoped Resource By The Name With In
    [Tags]    p1    namespaces
    ${all}=    Namespace Names    1    2    3
    ${wanted}=    Namespace Names    1    3
    Given Namespaces should be listed    ${all}
    Then Query IDs Should Be    ${NAMESPACE_PATH}    ${wanted}
    ...    filter=metadata.name in (${NS_PREFIX}-1,${NS_PREFIX}-3)    sort=metadata.name

Lists Of Other Types Work
    [Documentation]    The SQL cache serves every list of /v1/harvester, not only the lists of VMs
    [Tags]    p1
    ${nodes}=    Given Kubernetes IDs    api/v1/nodes
    FOR    ${type_id}    IN    @{OTHER_TYPES}
        Then List Of A Type Should Work    ${type_id}
    END
    FOR    ${type_id}    IN    @{STABLE_TYPES}
        And List Of A Type Should Work    ${type_id}    compare_with_kubernetes=${TRUE}
    END
    And Query IDs Should Be    v1/harvester/nodes    ${nodes}[-1:]    sort=-metadata.name    pagesize=1    page=1

Existing VMs Are Not Replayed By A Watch
    [Documentation]    A watch without resourceVersion only sends the changes after the subscription
    [Tags]    p1
    [Teardown]    Run Keywords    Subscription is closed
    ...    AND    Common Test Teardown
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    When Subscription is opened    kubevirt.io.virtualmachine
    ${ids}=    Prefixed IDs    ${VM_NS}    @{VM_NAMES}
    Then No Object Should Be Announced As Created    ${ids}

Watch Create Change And Remove
    [Tags]    p1
    [Teardown]    Run Keywords    Close Subscription And Delete VM    vm-watch
    ...    AND    Common Test Teardown
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    And Subscription is opened    kubevirt.io.virtualmachine
    When Stopped VM is created    vm-watch    ${EMPTY}    &{TEST_VM}
    Then Wait For Event    resource.create    ${VM_NS}/vm-watch
    When VM annotation is set    vm-watch    ${DISPLAY_NAME}    Changed    ${VM_NS}
    Then Wait For Event With Annotation    resource.change    ${VM_NS}/vm-watch    ${DISPLAY_NAME}    Changed
    When VM is deleted    vm-watch    ${VM_NS}
    Then Wait For Event    resource.remove    ${VM_NS}/vm-watch

Changes Mode Notifies About A New VM
    [Tags]    p1
    [Teardown]    Run Keywords    Close Subscription And Delete VM    vm-notify
    ...    AND    Common Test Teardown
    Given VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    And Subscription is opened    kubevirt.io.virtualmachine    mode=resource.changes    debounceMs=${100}
    ...    namespace=${VM_NS}    id=vm-notify
    When Stopped VM is created    vm-notify    ${EMPTY}    &{TEST_VM}
    Then Wait For Event    resource.changes


*** Keywords ***
Local Suite Setup
    Set up test environment
    ${supported}=    Cluster Version Is At Least    1.10.0
    Skip If    not ${supported}    The SQL cache of the lists needs Harvester v1.10
    ${ns}=    Generate Unique Name    ssp
    Set Suite Variable    ${VM_NS}    ${ns}
    Namespace is created    ${VM_NS}
    ${config}=    Test VM Config
    Set Suite Variable    &{TEST_VM}    &{config}
    FOR    ${name}    ${shown_as}    IN ZIP    ${VM_NAMES}    ${VM_DISPLAY_NAMES}
        Stopped VM is created    ${name}    ${EMPTY}    &{TEST_VM}
        ...    annotations=${{ {$DISPLAY_NAME: $shown_as} }}
    END
    Create Namespaces For Queries    @{NS_GROUPS}
    Create Config Maps For Lookups    &{CONFIG_MAP_GROUPS}
    Wait Until Keyword Succeeds    2 min    3 s    VMs should be indexed    ${VMS_BY_DISPLAY_NAME}
    ${namespaces}=    Namespace Names    1    2    3
    Wait Until Keyword Succeeds    2 min    3 s    Namespaces should be listed    ${namespaces}
    Wait Until Keyword Succeeds    2 min    3 s    Config maps should be listed

Local Suite Teardown
    # Parallel-safe: only delete this suite's own namespaces.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Namespace is deleted    ${VM_NS}
    Delete Namespaces For Queries    ${{ len($NS_GROUPS) }}
    Run Keyword And Ignore Error    Namespace is deleted    ${CM_NS}
