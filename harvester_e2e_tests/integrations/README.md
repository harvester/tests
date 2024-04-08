# Naming Of Test Files
To distinguish test cases with order, each file should start with `test_<N>_`, and the `N` is the number point out its dependencies of functionality, for example, `volume` and `image` will not dpened on anything, so the number should be `1`; for `vm`, it at least depends on `volume` and `image`, so it's number should be at least `3`.

Here is the table for existing functionality:

| Number | Function | Description |
| ------ | -------- | ----------- |
| 0 | Settings | Any settings could be tested individually if not interact with others |
| 1 | Templates | Template without VM |
| 1 | SSH Keys | SSH Keys without VM |
| 1 | Cloud Configs | Cloud config without VM |
| 1 | Storage Classes | Storageclass without Volume |
| 1 | Image | Download and upload image |
| 1 | Volume | Data volume |
| 2 | Volume | Volume from image |
| 2 | Volume | Volume + Storage class |
| 2 | Image | Image exported from volume |
| 3 | VM | pure VM which created from a image |
| 4 | Backup | VM + backup |
| 4 | Snapshot | VM + (vm/volume) snapshot |
| 5 | VM | VM + cluster network + vm network |
| 9 | Rancher | Fixed number for external Rancher integration |
| 9 | Terraform | Fixed for terraform related test cases |
