# CDI image deletion tests

The [CDI suite](test_image_cdi_deletion.robot#L1) checks deletion protection
for a VM using the golden PVC directly and for a completed clone PVC.

Its suite setup and teardown manage optional storage through
[cdi_storage.resource](../../../keywords/cdi_storage.resource#L1), which reuses
the existing LVM addon, disk, volume group, and StorageClass keywords.
The Harvester repository only supplies GitHub Actions configuration.

## Use an existing StorageClass

Run from `harvester_robot_tests` with its virtual environment activated:

```bash
export KUBECONFIG=/path/to/kubeconfig
export HARVESTER_OPERATION_STRATEGY=crd
export CDI_STORAGE_CLASS=lvm-cdi
./run.sh -f tests/regression/image/test_image_cdi_deletion.robot
```

The class must support CDI image import and cloning, such as LVM or Longhorn
v2. The suite keeps the supplied class and its backend. Kubernetes credentials
are sufficient for this suite; Harvester REST credentials are not required.
Set `OPENSUSE_IMAGE_URL` to use a local image mirror.

## Let the suite prepare LVM storage

Set `CDI_STORAGE_BACKEND=lvm` and leave `CDI_STORAGE_CLASS` unset:

```bash
export KUBECONFIG=/path/to/disposable-cluster-kubeconfig
export HARVESTER_OPERATION_STRATEGY=crd
unset CDI_STORAGE_CLASS
export CDI_STORAGE_BACKEND=lvm
./run.sh -f tests/regression/image/test_image_cdi_deletion.robot
```

If `run.sh` loads a `.env`, use these settings there too. A supplied
`CDI_STORAGE_CLASS` takes precedence over automatic preparation.

The suite setup finds Active, Unprovisioned disks of at least 50 GiB, enables
the LVM addon, labels the selected disks with a generated run ID, and creates
the `vg-dm-thin` volume group and a unique node-local StorageClass. It waits
for the CDI StorageProfile's snapshot clone strategy before running the cases.
Missing disks or failed preparation fail the suite instead of skipping it.

Suite teardown first deletes its VMs, clone PVCs, and images. It then waits
for all PVCs and PVs using its class to disappear before removing its labelled
volume group and StorageClass. If volumes remain, cleanup fails and preserves
their storage. An initially enabled LVM addon stays enabled.

Storage is managed by this suite's setup and teardown under both `robot` and
suite-level Pabot. No separate preparation or cleanup test cases are needed.
Other suites using their own LVM setup should run separately on the cluster,
since those helpers share the `vg-dm-thin` volume group name.

## GitHub Actions

For Harvester PR #12188 to select tests PR #3040,
add these standalone lines to the Harvester PR description:

```text
E2E-Tests-Repo: https://github.com/WebberHuang1118/tests
E2E-Tests-Branch: test/12011-cdi-image-deletion
```

The Harvester E2E workflow defaults to `lvm` and passes
`CDI_STORAGE_BACKEND=lvm` into the test container's `.env`. Both CDI deletion
cases are tagged `pr-baseline`, so they run with the regular PR suite without
an `E2E-Tests-Files` override. The suite prepares storage when it runs.
The tests branch contains all storage
preparation and cleanup logic. Both PR branches must include these changes
before running CI.

To disable automatic CDI storage preparation, add
`E2E-Tests-CDI-Storage: none` to the PR description, or select `none` in the
manual workflow's `cdi_storage` input. Direct local Robot runs still default
to `CDI_STORAGE_BACKEND=none` unless it is explicitly supplied.

The runner, such as `dell-139`, hosts the disposable Harvester node VMs. The
StorageClass and LVM storage belong to that cluster; its node VMs need the
unused disks. No StorageClass is configured on the runner host itself.
