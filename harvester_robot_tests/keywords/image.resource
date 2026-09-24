*** Settings ***
Documentation    Image Keywords
Library    OperatingSystem
Library    ../libs/keywords/image_keywords.py

Resource    variables.resource
Resource    common.resource


*** Keywords ***
Create image from url with name
    [Arguments]    ${image_name}    ${image_url}    ${storage_class}=${EMPTY}    ${checksum}=    ${retry}=${NONE}
    ...    ${backing_image_name}=${EMPTY}
    [Documentation]    Create image from URL using provided name and optional storage class.
    ...    retry overrides spec.retry (import retry limit, cluster default 3);
    ...    retry=${0} makes a doomed import fail on the first attempt.
    ...    backing_image_name sets spec.backingImageName so the Longhorn
    ...    BackingImage and the image's StorageClass get that exact name.
    image_keywords.create image from url    ${image_name}    ${image_url}    storage_class=${storage_class}    checksum=${checksum}    retry=${retry}
    ...    backing_image_name=${backing_image_name}

Create restore image from backing image backup
    [Arguments]    ${image_name}    ${backup_url}    ${checksum}=${EMPTY}
    [Documentation]    Create the image Harvester would itself create when syncing
    ...    backup-target metadata into a cluster where the image is missing:
    ...    sourceType restore with the backing image's backup-store URL
    ...    (…?backingImage=<name>) as spec.url. Harvester restores the
    ...    Longhorn BackingImage from the backup target and derives the
    ...    StorageClass name from that backingImage parameter.
    image_keywords.create image from url    ${image_name}    ${backup_url}    checksum=${checksum}
    ...    source_type=restore

Wait for image downloaded by name
    [Arguments]    ${image_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for image download to complete
    image_keywords.wait for image downloaded    ${image_name}    ${timeout}

Delete image by name
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Delete an image
    image_keywords.delete image    ${image_name}    ${namespace}

Get image status by name
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Get image status
    ${status}=    image_keywords.get image status    ${image_name}    ${namespace}
    RETURN    ${status}

Image is available for VM creation
    [Arguments]    ${image_name}    ${image_url}    ${storage_class}=${EMPTY}    ${backing_image_name}=${EMPTY}
    [Documentation]    Create an image from URL (delegates to Image module).
    ...    storage_class imports onto a third-party StorageClass via CDI.
    ...    backing_image_name pins the Longhorn BackingImage/StorageClass name.
    Create image from url with name    ${image_name}    ${image_url}    storage_class=${storage_class}
    ...    backing_image_name=${backing_image_name}
    Wait for image downloaded by name    ${image_name}

Wait for image deleted by name
    [Arguments]    ${image_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for the image to be fully removed
    image_keywords.wait for image deleted    ${image_name}    ${timeout}

List images
    [Arguments]    ${namespace}=${DEFAULT_NAMESPACE}
    ${images}=    image_keywords.list images    ${namespace}
    RETURN    ${images}

Image Should Be Listed
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    ${images}=    image_keywords.list images    ${namespace}
    ${names}=    Evaluate    [i['metadata']['name'] for i in $images]
    Should Contain    ${names}    ${image_name}

Image Should Exist
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    ${exists}=    image_keywords.image exists    ${image_name}    ${namespace}
    Should Be True    ${exists}

Image Should Not Exist
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    ${exists}=    image_keywords.image exists    ${image_name}    ${namespace}
    Should Not Be True    ${exists}

Image State Is ${state}
    [Arguments]    ${image_name}
    ${status}=    image_keywords.get image status    ${image_name}
    Should Be Equal As Strings    ${status["state"]}    ${state}

Wait Until Image State Is ${state}
    [Arguments]    ${image_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Image State Is ${state}    ${image_name}

Image Size Is Greater Than Zero
    [Arguments]    ${image_name}
    ${status}=    image_keywords.get image status    ${image_name}
    ${size}=    Convert To Integer    ${status["size"]}
    Should Be True    ${size} > 0

Image Backing Image Name Should Be
    [Arguments]    ${image_name}    ${expected}
    [Documentation]    Assert spec.backingImageName of an image
    ${spec}=    image_keywords.get_image_spec    ${image_name}
    Should Be Equal As Strings    ${spec}[backingImageName]    ${expected}

Image Storage Class Name Should Be
    [Arguments]    ${image_name}    ${expected}
    [Documentation]    Assert status.storageClassName, the StorageClass Harvester
    ...    created for (and VMs provision root disks from) this image
    ${status}=    image_keywords.get image status    ${image_name}
    Should Be Equal As Strings    ${status}[storage_class_name]    ${expected}

Cluster Supports Custom Backing Image Name
    [Documentation]    True when the VirtualMachineImage CRD has spec.backingImageName
    ...    (harvester/harvester#11641). Detects the field rather than comparing
    ...    versions: a v1.9.1 rc cut before the backport parses to the same
    ...    release as one that carries it.
    ${supported}=    image_keywords.cluster_supports_backing_image_name
    RETURN    ${supported}

Skip Unless Cluster Supports Custom Backing Image Name
    ${supported}=    Cluster Supports Custom Backing Image Name
    Skip If    not ${supported}    VirtualMachineImage CRD has no spec.backingImageName; skipping

Backing Image Should Exist
    [Arguments]    ${backing_image_name}
    [Documentation]    Assert a Longhorn BackingImage with exactly this name exists
    ${bi}=    image_keywords.get_backing_image    ${backing_image_name}
    Should Not Be Equal    ${bi}    ${NONE}
    ...    msg=Longhorn BackingImage ${backing_image_name} does not exist

Backing Image Should Not Exist
    [Arguments]    ${backing_image_name}
    ${bi}=    image_keywords.get_backing_image    ${backing_image_name}
    Should Be Equal    ${bi}    ${NONE}
    ...    msg=Longhorn BackingImage ${backing_image_name} still exists

Wait Until Backing Image Is Deleted
    [Arguments]    ${backing_image_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Backing Image Should Not Exist    ${backing_image_name}

Image Size Is ${size_gi}Gi
    [Arguments]    ${image_name}
    ${status}=    image_keywords.get image status    ${image_name}
    ${size_bytes}=    Convert To Integer    ${status["size"]}
    ${expected_size_bytes}=    Evaluate    ${size_gi} * 1024 * 1024 * 1024
    Should Be Equal As Integers    ${size_bytes}    ${expected_size_bytes}

Image Export Should Have Started
    [Arguments]    ${image_name}
    [Documentation]    Assert the image controller has begun processing the image
    ...    (its state is no longer Unknown, i.e. status conditions/progress exist)
    ${status}=    image_keywords.get image status    ${image_name}
    Should Not Be Equal As Strings    ${status["state"]}    Unknown
    ...    msg=Image ${image_name} has not been picked up by the image controller yet

Wait Until Image Export Has Started
    [Arguments]    ${image_name}
    [Documentation]    Wait until the image controller has started processing the
    ...    export image. The PVC webhook rejects deleting an exporting volume by
    ...    looking the image up in its informer cache, so a delete issued right
    ...    after creating the image can race the cache and incorrectly succeed.
    ...    Once the controller has stamped the image status, the image has
    ...    propagated through the informer caches and the protection is in effect.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Image Export Should Have Started    ${image_name}

# negative
Try To Create Image
    [Arguments]    ${image_name}    ${image_url}=${EMPTY}    ${source_type}=download    ${checksum}=${EMPTY}
    ...    ${namespace}=${DEFAULT_NAMESPACE}    &{spec}
    [Documentation]    Attempt to create an image expected to be rejected.
    ...    Returns a result dict {success, code, message}; never fails on rejection.
    ...    Extra named args (backing_image_name, backend, storage_class) set the
    ...    matching spec fields.
    ${result}=    image_keywords.try_create_image    ${image_name}    ${image_url}    ${source_type}    ${checksum}
    ...    ${namespace}    &{spec}
    RETURN    ${result}

Try To Update Image Spec
    [Arguments]    ${image_name}    &{spec}
    [Documentation]    Attempt to merge-patch spec fields of an image (expected to be
    ...    rejected). Returns a result dict {success, code, message}; a field
    ...    set to ${NONE} is removed from the spec.
    ${result}=    image_keywords.try_update_image_spec    ${image_name}    &{spec}
    RETURN    ${result}

Try To Get Image
    [Arguments]    ${image_name}
    [Documentation]    Attempt to get an image expected to be missing. Returns result dict.
    ${result}=    image_keywords.try_get_image    ${image_name}
    RETURN    ${result}

Try To Delete Image
    [Arguments]    ${image_name}
    [Documentation]    Attempt to delete an image expected to be missing. Returns result dict.
    ${result}=    image_keywords.try_delete_image    ${image_name}
    RETURN    ${result}

Create An Invalid Image File
    [Arguments]    ${file_name}
    ${path}=    Join Path    ${TEMPDIR}    ${file_name}
    ${content}=    Evaluate    bytes([0]) * 6
    Create Binary File    ${path}    ${content}
    RETURN    ${path}

Upload Image File
    [Arguments]    ${image_name}    ${file_path}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Create an image by uploading a local file through the REST API.
    ${response}=    image_keywords.upload image file
    ...    ${image_name}    ${file_path}    ${namespace}
    RETURN    ${response}

Upload Image File Should Be Rejected
    [Arguments]    ${image_name}    ${file_path}    ${namespace}=${DEFAULT_NAMESPACE}
    ${response}=    Upload Image File    ${image_name}    ${file_path}    ${namespace}
    Should Be Equal As Integers    ${response.status_code}    500

# update
Update Image Metadata
    [Arguments]    ${image_name}    ${metadata}
    [Documentation]    Patch an image's metadata (a dict with labels/annotations)
    image_keywords.update_image    ${image_name}    ${metadata}

Image Label Should Be
    [Arguments]    ${image_name}    ${key}    ${expected}
    ${metadata}=    image_keywords.get_image_metadata    ${image_name}
    Dictionary Should Contain Item    ${metadata}[labels]    ${key}    ${expected}

Image Annotation Should Be
    [Arguments]    ${image_name}    ${key}    ${expected}
    ${metadata}=    image_keywords.get_image_metadata    ${image_name}
    Dictionary Should Contain Item    ${metadata}[annotations]    ${key}    ${expected}

Get Image By Name
    [Arguments]    ${image_name}
    [Documentation]    Get a single image's metadata and assert its name matches
    ${metadata}=    image_keywords.get_image_metadata    ${image_name}
    Should Be Equal As Strings    ${metadata}[name]    ${image_name}