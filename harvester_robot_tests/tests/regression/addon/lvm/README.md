# LVM addon suites

The LVM suites share cluster-wide resources: the CSI addon, a physical
BlockDevice, and the `vg-dm-thin` volume group on it. Preparing and cleaning
those up is not a suite of its own; [`__init__.robot`](./__init__.robot) does
it as the directory's suite setup and teardown, so the order holds no matter
how the suites are started:

1. Setup enables the addon and provisions the shared volume group.
2. The attach, clone, data-integrity, image, snapshot, snapshot-lifecycle,
   negative, and expansion suites run, concurrently under Pabot.
3. Teardown checks that the driver left no helper pods behind, cleans the
   volume group and BlockDevices, then disables the addon.

Under Pabot every process runs this `__init__.robot`, so setup and teardown go
through PabotLib. `Run Setup Only Once` executes the setup in the first process
that reaches it; the others wait for it to finish, and fail with
`Setup failed in other process` if it did not succeed. `Run Teardown Only Once`
executes the teardown in the last queued LVM suite, after every suite queued
before it has finished. No ordering file is needed, and it makes no difference
whether Pabot is pointed at this directory, at `tests/regression/addon`, or at
`tests/`. Under plain `robot` both are an ordinary suite setup and teardown. A
single suite selected with `--suite` still gets its own setup and teardown.

A failing teardown (a leaked helper pod, a volume group that cannot be
unprovisioned) fails the tests of the suite it ran in: the last LVM suite
under Pabot, every LVM suite under plain `robot`.

Setup reuses a volume group that an interrupted run left behind (same
`LVM_TEST_RUN_ID`, disk still `Provisioned`) instead of provisioning another
disk, so a cluster whose teardown never ran can simply be run again.

The LVM suites are opt-in in `run.sh` because they consume an active,
unprovisioned physical BlockDevice of at least 50 GiB: broad runs add
`--exclude lvm`. Run the directory explicitly (`-f tests/regression/addon/lvm`)
or include the `lvm` tag (`-i lvm`). Runners that call `robot` or `pabot`
directly get the LVM suites unless they exclude the tag themselves. The suites
use Kubernetes CRDs and do not support the REST operation strategy.

`LVM_TEST_RUN_ID` labels the selected BlockDevices so the workload suites and
the teardown, which run in other Pabot processes than the setup, can find the
disks it chose. It defaults to `lvm-robot`; override it only when separate LVM
runs need distinct IDs.

The addon manifest comes from
[harvester/experimental-addons](https://github.com/harvester/experimental-addons).
By default the branch is derived from the cluster release (`v<major>.<minor>`, so a
v1.9.x cluster installs the chart pinned on `v1.9`); dev builds without a release
version, or a release whose branch is not cut yet, use `main`. Set `LVM_ADDON_URL`
to apply a specific manifest instead, e.g. a mirror in air-gapped setups.

The data-integrity suite runs plain pods (default image `busybox:1.36.1`,
override with `WORKLOAD_POD_IMAGE`) against LVM PVCs to checksum real data
across republish and snapshot-restore. The image is pulled from the registry,
so the cluster needs egress (or a pre-loaded/mirrored image) when this suite
runs.

The snapshot-lifecycle suite verifies backend state on the node (via a
transient privileged hostPID probe pod running the host's `lvs`) and the
driver's snapshot-location ConfigMap records (harvester/csi-driver-lvm#64).
The location-record cases need a driver build that includes that PR.
