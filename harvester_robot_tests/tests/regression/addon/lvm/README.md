# Parallel LVM suite ordering

The LVM suites share cluster-wide resources: the CSI addon, physical
BlockDevices, and `vg-dm-thin`. Pabot normally schedules suite files as soon as
a worker is available, so alphabetical file order alone cannot guarantee that
setup has completed or that every workload has released the volume group before
cleanup starts.

[`lvm-order.txt`](./lvm-order.txt) fixes the execution into three stages:

1. Enable the addon and provision the shared volume group.
2. Run the attach, snapshot, and expansion suites concurrently.
3. Clean the volume group and BlockDevices, then disable the addon.

Each `#WAIT` is a Pabot stage barrier: every suite above it must finish before
any suite below it can start. `run.sh` selects the ordering file automatically
when `tests/regression/addon/lvm` is run with `-p`.

The LVM flow is opt-in because it consumes an active, unprovisioned physical
BlockDevice of at least 50 GiB. Broad serial and parallel runs exclude the `lvm`
tag. Run the directory explicitly or use the exact `-i lvm` tag; compound LVM tag
expressions are rejected so they cannot accidentally bypass staged ordering. The
suite uses Kubernetes CRDs and does not support the REST operation strategy.

Pabot 5.2.2 does not support comments in ordering files. A line beginning with
`#` is treated as a suite name unless it is one of Pabot's directives, such as
`#WAIT` or `#SLEEP`. The explanation therefore lives here instead of directly
inside `lvm-order.txt`, avoiding ignored-suite warnings during every test run.
