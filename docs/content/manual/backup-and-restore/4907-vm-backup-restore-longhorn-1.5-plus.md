---
title: VM backup restore use Longhorn v1.5+ attach/detach mechanism
---

* Related issues: [#4907](https://github.com/harvester/harvester/issues/4907) [ENHANCEMENT] Take advantage of the attach/detach mechanism in Longhorn v1.5+

## Category: 
* Backup and Restore

## Verification Steps
Case 1: snapshot can work on a stopped VM.
- This test have already been covered in e2e backend automation of test plan
  -  `test_restore_from_vm_snapshot_while_pvc_detached_from_source` in [test_4_vm_snapshot.py L457-L487](https://github.com/harvester/tests/blob/790c494fceba390253d8130641aa5db5d0289096/harvester_e2e_tests/integrations/test_4_vm_snapshot.py#L457-L487)

Case 2: restore a snapshot from detached volumes can work.
- This test have already been covered in e2e backend automation of test plan
  -  `test_create_vm_snapshot_while_pvc_detached` in [test_4_vm_snapshot.py L425-L453](https://github.com/harvester/tests/blob/790c494fceba390253d8130641aa5db5d0289096/harvester_e2e_tests/integrations/test_4_vm_snapshot.py#L425-L453)

Case 3: backup can work on a stopped VM
1. Create a VM.
1. After the VM is ready, stop the VM.
1. Check VM volumes are detached.
1. Take a backup on the VM. The backup can be ready.

Case 4: race condition doesn't break VMBackup
1. Create a VM.
1. After the VM is ready, stop the VM.
1. Check VM volumes are detached.
1. Take multiple backup on the VM in a short time. All backup can be ready.

Case 5: restore a backup from detached volumes can work:
1. Follow Case 3.
1. Make sure VM volumes are detached.
1. Restore the backup to a new VM. The new VM can be ready.
1. Restore the backup to replace the old VM. The old VM can be ready.

## Expected Results
* Case 1: snapshot can work on a stopped VM 
   - VM volumes are detached after we stop VM.
      ```
      node1:~ # kubectl get volume -A
      NAMESPACE         NAME                                       STATE      ROBUSTNESS   SCHEDULED   SIZE          NODE   AGE
      longhorn-system   pvc-5a861225-920d-4059-b501-f02b2fd0ff27   detached   unknown                  10737418240          19m
      ```
   - Take the vm snapshot, The snapshot of vm in off state can be ready.
* Case 2: restore a snapshot from detached volumes can work. 
   - Restore the snapshot to a new VM. The new VM can be ready.
   - Restore the snapshot to replace the old VM. The old VM can be ready.

* Case 3: backup can work on a stopped VM. 
   - VM volumes are detached after we stop VM.
      ```
      NAMESPACE         NAME                                       STATE      ROBUSTNESS   SCHEDULED   SIZE          NODE   AGE
      longhorn-system   pvc-d1226d97-ab90-4d40-92f9-960b668093c2   detached   unknown                  10737418240          5m12s
      ```
   -  Take the vm backup, The backup of vm in off state can be ready.

* Case 4: race condition doesn't break VMBackup 
   - Take multiple backup on the VM in a short time. All backup can be ready.

* Case 5: restore a backup from detached volumes can work 
   - Restore the backup to a new VM. The new VM can be ready.
   - Restore the backup to replace the old VM. (Retain Volume), The old VM can be ready.
   - Restore the backup to replace the old VM. (Delete Volume), The old VM can be ready.
