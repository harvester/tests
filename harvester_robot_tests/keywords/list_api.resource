*** Settings ***
Documentation    Lists of the Harvester API (filter, sort and pages, served by the SQL
...              cache of Steve), compared with the Kubernetes API, the watch over
...              /v1/harvester/subscribe, and calls that have to go through a store of
...              the Harvester API.
...              The second part holds the suite-level keywords of
...              tests/regression/api/test_list_api.robot, they use its suite variables.
Library          Collections
Library          ../libs/keywords/list_api_keywords.py
Resource         variables.resource
Resource         common.resource
Resource         configmap.resource
Resource         virtualmachine.resource


*** Variables ***
${VM_PATH}                  v1/harvester/kubevirt.io.virtualmachines
${NAMESPACE_PATH}           v1/harvester/namespaces
${CONFIGMAP_PATH}           v1/harvester/configmaps
${DISPLAY_NAME}             harvesterhci.io/vmDisplayName
${DISPLAY_NAME_FIELD}       metadata.annotations[${DISPLAY_NAME}]
${STOPPED}                  status.printableStatus=Stopped
${RUNNING}                  status.printableStatus=Running
${CONTAINER_DISK_IMAGE}     docker.io/kubevirt/cirros-container-disk-demo:latest
${APISERVER_LABELS}         app.kubernetes.io/name=harvester,app.kubernetes.io/component=apiserver
@{NO_IDS}
# Suite variables of test_list_api.robot: the namespace of the VMs, the prefix of
# the namespaces of the namespace queries, the namespace of the config maps and
# the label of the groups
${VM_NS}                    ${EMPTY}
${NS_PREFIX}                ${EMPTY}
${CM_NS}                    ${EMPTY}
@{CM_NAMES}
${GROUP_LABEL}              harvester.test.io/ssp-group
${GROUP_LABEL_FIELD}        metadata.labels[${GROUP_LABEL}]


*** Keywords ***
Prefixed IDs
    [Arguments]    ${prefix}    @{names}
    [Documentation]    The ids <prefix>/<name> of the names, e.g. namespace/name
    ${ids}=    Evaluate    ['${prefix}/' + n for n in $names]
    RETURN    ${ids}

Query
    [Arguments]    ${path}    &{params}
    [Documentation]    GET the list at ${path} of the Harvester API with &{params} as query
    ...    (filter, sort, page, pagesize, ...; a list value repeats the parameter) and
    ...    check for 200. Returns {code, ids, count, body}.
    ${result}=    list_api_keywords.query    ${path}    &{params}
    Should Be Equal As Integers    ${result}[code]    200    ${result}[body]
    RETURN    ${result}

Query IDs Should Be
    [Arguments]    ${path}    ${expected}    ${ignore_order}=${FALSE}    &{params}
    [Documentation]    The ids of the list at ${path} with &{params} are ${expected},
    ...    in this order unless ${ignore_order} is true
    ${result}=    Query    ${path}    &{params}
    Lists Should Be Equal    ${result}[ids]    ${expected}    ignore_order=${ignore_order}

Query Should Be Rejected
    [Arguments]    ${path}    ${code}=${NONE}    &{params}
    [Documentation]    The list at ${path} with &{params} answers with the HTTP status
    ...    ${code}, without retries. Without a code any 4xx or 5xx is accepted.
    ${result}=    list_api_keywords.query    ${path}    retries=${FALSE}    &{params}
    IF    $code is None
        Should Be True    ${result}[code] >= 400    ${result}
    ELSE
        Should Be Equal As Integers    ${result}[code]    ${code}    ${result}[body]
    END

Query IDs And Count Should Be
    [Arguments]    ${path}    ${expected}    &{params}
    [Documentation]    The list at ${path} with &{params} holds ${expected} in any order,
    ...    and its count is the number of them
    ${result}=    Query    ${path}    &{params}
    Lists Should Be Equal    ${result}[ids]    ${expected}    ignore_order=True
    ${length}=    Get Length    ${expected}
    Should Be Equal As Integers    ${result}[count]    ${length}

Query Should Contain IDs
    [Arguments]    ${path}    ${ids}    &{params}
    [Documentation]    The list at ${path} with &{params} has every id of ${ids}, maybe more
    ${result}=    Query    ${path}    &{params}
    FOR    ${id}    IN    @{ids}
        List Should Contain Value    ${result}[ids]    ${id}
    END

Query Should Not Contain IDs
    [Arguments]    ${path}    ${ids}    &{params}
    [Documentation]    The list at ${path} with &{params} has none of the ids of ${ids}
    ${result}=    Query    ${path}    &{params}
    FOR    ${id}    IN    @{ids}
        List Should Not Contain Value    ${result}[ids]    ${id}
    END

Pages Should Hold
    [Arguments]    ${path}    ${expected}    &{params}
    [Documentation]    Page by page (page=1, 2, ... with &{params}, which hold pagesize and
    ...    e.g. sort) the list at ${path} holds ${expected}, in this order: page N has the
    ...    ids of its slice of ${expected}. Every page, also the empty one after the last, has
    ...    the total count instead of the page size and no pages field.
    @{collected}=    Create List
    ${total}=    Get Length    ${expected}
    ${size}=    Convert To Integer    ${params}[pagesize]
    FOR    ${page}    IN RANGE    1    ${total} + 2
        ${result}=    Query    ${path}    page=${page}    &{params}
        Should Be Equal As Integers    ${result}[count]    ${total}    count is the total, not the page size
        Dictionary Should Not Contain Key    ${result}[body]    pages
        IF    not $result['ids']    BREAK
        ${start}=    Evaluate    ($page - 1) * $size
        ${end}=    Evaluate    $page * $size
        Lists Should Be Equal    ${result}[ids]    ${expected}[${start}:${end}]    page ${page}
        Append To List    ${collected}    @{result}[ids]
    END
    Lists Should Be Equal    ${collected}    ${expected}

Query Should Match Kubernetes
    [Arguments]    ${path}    ${k8s_path}
    [Documentation]    The ids of the list at ${path} of the Harvester API are the ones of
    ...    the list at ${k8s_path} of the Kubernetes API, e.g. api/v1/namespaces
    ${expected}=    Kubernetes IDs    ${k8s_path}
    Query IDs Should Be    ${path}    ${expected}    ignore_order=${TRUE}

Kubernetes IDs
    [Arguments]    ${k8s_path}
    [Documentation]    The sorted ids (namespace/name or name) of the list at ${k8s_path} of the
    ...    Kubernetes API, e.g. api/v1/nodes
    ${ids}=    list_api_keywords.get_k8s_ids    ${k8s_path}
    RETURN    ${ids}

List Of A Type Should Work
    [Arguments]    ${type_id}    ${compare_with_kubernetes}=${FALSE}
    [Documentation]    The list of the schema ${type_id} answers with a collection whose
    ...    count is the number of items. With ${compare_with_kubernetes}, the ids are the
    ...    ones of the Kubernetes API. A type the cluster does not have is only logged.
    ${code}    ${schema}=    list_api_keywords.get_schema    ${type_id}
    IF    ${code} == 404
        Log    The cluster has no type ${type_id}
        RETURN
    END
    Should Be Equal As Integers    ${code}    200    ${schema}
    List Should Contain Value    ${schema}[collectionMethods]    GET
    ${collection}=    Evaluate    urllib.parse.urlparse($schema['links']['collection']).path
    ...    modules=urllib.parse
    ${result}=    Query    ${collection}
    Dictionary Should Contain Key    ${result}[body]    data
    IF    $result['count'] is not None
        Length Should Be    ${result}[ids]    ${result}[count]
    END
    IF    ${compare_with_kubernetes}
        ${expected}=    list_api_keywords.get_k8s_ids_of_schema    ${schema}
        Lists Should Be Equal    ${result}[ids]    ${expected}    ignore_order=True
    END

Relative Link
    [Arguments]    ${url}
    [Documentation]    Path and query of a link of the API (e.g. pagination.next), for `Query`
    ${link}=    Evaluate    (lambda u: u.path.lstrip('/') + '?' + u.query)(urllib.parse.urlparse($url))
    ...    modules=urllib.parse
    RETURN    ${link}

Schema Columns Should Point To Metadata Fields
    [Arguments]    ${type_id}
    [Documentation]    The columns of the schema ${type_id} contain Name and point to
    ...    $.metadata.fields[N]. Returns the columns.
    ${code}    ${schema}=    list_api_keywords.get_schema    ${type_id}
    Should Be Equal As Integers    ${code}    200    ${schema}
    ${columns}=    Set Variable    ${schema}[attributes][columns]
    ${names}=    Evaluate    [c['name'] for c in $columns]
    List Should Contain Value    ${names}    Name
    FOR    ${column}    IN    @{columns}
        Should Match Regexp    ${column}[field]    ^\\$\\.metadata\\.fields\\[\\d+\\]$
    END
    RETURN    ${columns}

Date Columns Should Be Timestamps
    [Arguments]    ${path}    ${columns}
    [Documentation]    The date columns of ${columns} (from `Schema Columns Should Point To
    ...    Metadata Fields`) hold a timestamp in metadata.fields of the items at ${path}
    ${result}=    Query    ${path}
    ${dates}=    Evaluate    [int(re.findall(r'[0-9]+', c['field'])[0]) for c in $columns if c.get('type') == 'date']
    ...    modules=re
    Should Not Be Empty    ${dates}    the schema has no date column
    FOR    ${item}    IN    @{result}[body][data]
        FOR    ${index}    IN    @{dates}
            ${value}=    Set Variable    ${item}[metadata][fields][${index}]
            Evaluate    datetime.datetime.fromisoformat($value.replace('Z', '+00:00'))
            ...    modules=datetime
        END
    END

API Server Pods
    [Documentation]    Names of the running pods of the Harvester API server
    @{pods}=    List Pods By Label    harvester-system    ${APISERVER_LABELS}    Running
    Should Not Be Empty    ${pods}    no running pod of the API server
    ${names}=    Evaluate    [p.metadata.name for p in $pods]
    RETURN    ${names}

API Server Pod Path
    [Arguments]    ${pod}    ${path}
    [Documentation]    ${path} on the API server pod ${pod}, through the pod proxy of the
    ...    Kubernetes API. Every replica has its own cache.
    RETURN    api/v1/namespaces/harvester-system/pods/https:${pod}:8443/proxy/${path}

VM is deleted through the Harvester API
    [Arguments]    ${vm_name}    ${namespace}=default    ${removed_disks}=${NONE}
    [Documentation]    Delete the VM through the VM store of Harvester, which also
    ...    removes the PVCs of the disks (volume names) in ${removed_disks}
    list_api_keywords.delete_vm    ${vm_name}    ${namespace}    ${removed_disks}

Namespace is created through the Harvester API
    [Arguments]    ${name}    ${labels}=${NONE}
    [Documentation]    Create the namespace with the dict ${labels} through the namespace
    ...    store of Harvester. `Namespace is created` goes to Kubernetes directly.
    list_api_keywords.create_namespace    ${name}    ${labels}

Namespace is deleted through the Harvester API
    [Arguments]    ${name}
    [Documentation]    Delete the namespace through the namespace store of Harvester
    list_api_keywords.delete_namespace    ${name}

Namespace labels are updated through the Harvester API
    [Arguments]    ${name}    ${labels}
    [Documentation]    Merge the dict ${labels} into the labels of the namespace through the
    ...    namespace store of Harvester, retrying on conflicts
    list_api_keywords.update_namespace_labels    ${name}    ${labels}

Namespace Should Have Label
    [Arguments]    ${name}    ${key}    ${value}
    [Documentation]    The Harvester API returns the namespace with the label ${key}=${value}
    ${code}    ${data}=    list_api_keywords.get_namespace    ${name}
    Should Be Equal As Integers    ${code}    200    ${data}
    Should Be Equal    ${data}[metadata][labels][${key}]    ${value}

Namespace Should Be Gone
    [Arguments]    ${name}
    [Documentation]    The Harvester API neither finds the namespace by its id nor lists it
    ${code}    ${data}=    list_api_keywords.get_namespace    ${name}
    Should Be Equal As Integers    ${code}    404    ${data}
    ${result}=    Query    ${NAMESPACE_PATH}    filter=metadata.name=${name}
    Should Be Empty    ${result}[ids]

Existing Namespaces Among
    [Arguments]    ${names}
    [Documentation]    The namespaces of ${names} that exist in Kubernetes, sorted. Fails if none exists.
    ${existing}=    Kubernetes IDs    api/v1/namespaces
    ${found}=    Evaluate    sorted(set($names) & set($existing))
    Should Not Be Empty    ${found}    none of ${names} exists
    RETURN    ${found}

Subscription is opened
    [Arguments]    ${resource_type}    &{options}
    [Documentation]    Subscribe to the events of ${resource_type} (e.g.
    ...    kubevirt.io.virtualmachine) over /v1/harvester/subscribe, with &{options} like
    ...    mode=resource.changes. Waits for resource.start. List the type before, so its
    ...    cache exists. One subscription at a time, a new one closes the old one.
    list_api_keywords.open_subscription    ${resource_type}    &{options}
    list_api_keywords.next_event    resource.start

Subscription is closed
    [Documentation]    Close the subscription of `Subscription is opened`
    list_api_keywords.close_subscription

Wait For Event
    [Arguments]    ${event}    ${obj_id}=${NONE}
    [Documentation]    Wait for the event ${event} (e.g. resource.create) of the object
    ...    ${obj_id} (namespace/name, any object if not given), other events are skipped.
    ...    Returns the message.
    ${message}=    list_api_keywords.next_event    ${event}    ${obj_id}
    RETURN    ${message}

Wait For Event With Annotation
    [Arguments]    ${event}    ${obj_id}    ${key}    ${value}
    [Documentation]    Wait for an event ${event} of ${obj_id} whose object has the
    ...    annotation ${key}=${value}. Events of other changes are skipped.
    Wait Until Keyword Succeeds    60 s    0 s
    ...    Next Event Should Have Annotation    ${event}    ${obj_id}    ${key}    ${value}

Next Event Should Have Annotation
    [Arguments]    ${event}    ${obj_id}    ${key}    ${value}
    [Documentation]    The next event ${event} of ${obj_id} has the annotation ${key}=${value}
    ${message}=    Wait For Event    ${event}    ${obj_id}
    ${annotations}=    Evaluate
    ...    (($message.get('data') or {}).get('metadata') or {}).get('annotations') or {}
    Dictionary Should Contain Item    ${annotations}    ${key}    ${value}

No Object Should Be Announced As Created
    [Arguments]    ${obj_ids}    ${seconds}=8
    [Documentation]    No resource.create event for one of ${obj_ids} arrives in ${seconds}
    ${events}=    list_api_keywords.receive_events    ${seconds}
    ${replayed}=    Evaluate
    ...    sorted(set(i for n, i in $events if n == 'resource.create') & set($obj_ids))
    Should Be Empty    ${replayed}

# Suite-level keywords of tests/regression/api/test_list_api.robot

VM List Path
    [Arguments]    ${pod}=${NONE}
    [Documentation]    The VM list of ${VM_NS}. With ${pod}, the list of that API server replica.
    IF    $pod is None    RETURN    ${VM_PATH}/${VM_NS}
    ${path}=    API Server Pod Path    ${pod}    ${VM_PATH}/${VM_NS}
    RETURN    ${path}

VM Query Should Return
    [Arguments]    ${names}    ${ignore_order}=${FALSE}    ${pod}=${NONE}    &{params}
    [Documentation]    The VM list of ${VM_NS} with &{params} holds the VMs ${names}, in this
    ...    order unless ${ignore_order} is true. With ${pod}, the list of that replica.
    ${expected}=    Prefixed IDs    ${VM_NS}    @{names}
    ${path}=    VM List Path    ${pod}
    Query IDs Should Be    ${path}    ${expected}    ${ignore_order}    &{params}

Wait Until VM Query Returns
    [Arguments]    ${names}    ${ignore_order}=${TRUE}    ${pod}=${NONE}    &{params}
    [Documentation]    `VM Query Should Return`, retried: the cache needs a moment for a change
    Wait Until Keyword Succeeds    2 min    3 s
    ...    VM Query Should Return    ${names}    ${ignore_order}    ${pod}    &{params}

VMs should be indexed
    [Arguments]    ${names_by_display_name}
    [Documentation]    The cache has the status and the display name of the VMs of ${VM_NS}:
    ...    sorted by display name they are ${names_by_display_name}
    VM Query Should Return    ${names_by_display_name}    filter=${STOPPED}    sort=${DISPLAY_NAME_FIELD}

VM Should Be Listed
    [Arguments]    ${name}    ${listed}=${TRUE}    &{params}
    [Documentation]    The VM list of ${VM_NS} with &{params} has the VM ${name}, or has not
    ...    if ${listed} is false
    ${result}=    Query    ${VM_PATH}/${VM_NS}    &{params}
    ${is_listed}=    Evaluate    $VM_NS + '/' + $name in $result['ids']
    Should Be Equal    ${is_listed}    ${listed}

Delete VM And Wait Until Gone
    [Arguments]    ${name}
    [Documentation]    Delete the VM of ${VM_NS} and wait until the list no longer has it
    VM is deleted    ${name}    ${VM_NS}
    Wait Until Keyword Succeeds    2 min    3 s    VM Should Be Listed    ${name}    ${FALSE}

Delete VMs And Wait Until Gone
    [Arguments]    @{names}
    [Documentation]    `Delete VM And Wait Until Gone` for every VM of ${names}
    FOR    ${name}    IN    @{names}
        Delete VM And Wait Until Gone    ${name}
    END

Test VM Config
    [Documentation]    &{config} of `Stopped VM is created` for a VM of ${VM_NS} that boots
    ...    from a container disk, so no image is needed
    &{config}=    Create Dictionary    namespace=${VM_NS}    container_image=${CONTAINER_DISK_IMAGE}
    RETURN    ${config}

Namespace Group Labels
    [Arguments]    ${group}
    [Documentation]    The labels of a namespace or config map in the group ${group}
    &{labels}=    Create Dictionary    ${GROUP_LABEL}=${group}
    RETURN    ${labels}

Create Namespaces For Queries
    [Arguments]    @{groups}
    [Documentation]    One namespace <prefix>-<N> per group of ${groups}, with the group
    ...    label. Sets ${NS_PREFIX}.
    ${prefix}=    Generate Unique Name    ssp-ns
    Set Suite Variable    ${NS_PREFIX}    ${prefix}
    FOR    ${index}    ${group}    IN ENUMERATE    @{groups}    start=1
        ${labels}=    Namespace Group Labels    ${group}
        Namespace is created    ${NS_PREFIX}-${index}    ${labels}
    END

Namespace Names
    [Arguments]    @{indexes}
    [Documentation]    The names <prefix>-<N> of the namespaces of `Create Namespaces For Queries`
    ${names}=    Evaluate    ['${NS_PREFIX}-' + str(i) for i in $indexes]
    RETURN    ${names}

Namespaces should be listed
    [Arguments]    ${names}
    [Documentation]    The namespace list has exactly the namespaces ${names} of the prefix
    Query IDs Should Be    ${NAMESPACE_PATH}    ${names}    filter=metadata.name~${NS_PREFIX}    sort=metadata.name

Restore Namespace Groups
    [Arguments]    ${names}    ${groups}
    [Documentation]    Set the group label of the namespaces ${names} back to ${groups}
    FOR    ${name}    ${group}    IN ZIP    ${names}    ${groups}
        ${labels}=    Namespace Group Labels    ${group}
        Namespace labels are updated through the Harvester API    ${name}    ${labels}
    END

Delete Namespaces For Queries
    [Arguments]    ${count}
    [Documentation]    Delete the ${count} namespaces of `Create Namespaces For Queries`
    FOR    ${index}    IN RANGE    1    ${count} + 1
        Run Keyword And Ignore Error    Namespace is deleted    ${NS_PREFIX}-${index}
    END

Create Config Maps For Lookups
    [Arguments]    &{groups}
    [Documentation]    A namespace with one config map per name of ${groups}, with the
    ...    group label unless the group is empty. Sets ${CM_NS} and ${CM_NAMES}.
    ${ns}=    Generate Unique Name    ssp-lookup
    Set Suite Variable    ${CM_NS}    ${ns}
    ${names}=    Get Dictionary Keys    ${groups}    sort_keys=${FALSE}
    Set Suite Variable    ${CM_NAMES}    ${names}
    Namespace is created    ${CM_NS}
    FOR    ${name}    ${group}    IN    &{groups}
        ${labels}=    Run Keyword If    $group    Namespace Group Labels    ${group}
        Config map is created    ${name}    ${CM_NS}    ${labels}
    END

Config maps should be listed
    [Documentation]    The config map list of ${CM_NS} has the config maps of
    ...    `Create Config Maps For Lookups`, the ones Kubernetes adds aside
    Config Maps Should Be    ${CM_NAMES}    metadata.name~cm-

Config Maps Should Be
    [Arguments]    ${names}    ${filter}=${NONE}
    [Documentation]    The config map list of ${CM_NS}, sorted by name and filtered by
    ...    ${filter} if given, holds ${names}
    ${expected}=    Prefixed IDs    ${CM_NS}    @{names}
    Query IDs Should Be    ${CONFIGMAP_PATH}/${CM_NS}    ${expected}
    ...    filter=${filter}    sort=metadata.name

Close Subscription And Delete VM
    [Arguments]    ${name}
    [Documentation]    Teardown of the watch tests: close the subscription, delete the VM of ${VM_NS}
    Subscription is closed
    Run Keyword And Ignore Error    VM is deleted    ${name}    ${VM_NS}
