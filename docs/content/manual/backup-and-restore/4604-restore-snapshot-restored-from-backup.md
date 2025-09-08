---
title: Restore the snapshot when the vm already been restored from backup
---

* Related issues: [#4604](https://github.com/harvester/harvester/issues/4604) [BUG] Restore from snapshot not work if target VM is restore-replaced from backup


## Category: 
* Backup and Restore

### Background:
    Given a VM named "vm1" is created and is running
    And a file named "test-backup.txt" is created with specific content
    And the md5sum of "test-backup.txt" is computed
    And a backup of "vm1" is taken and is ready
    And a file named "test-snapshot.txt" is created with specific content
    And the md5sum of "test-snapshot.txt" is computed
    And a snapshot of "vm1" is taken and is ready

### Scenario: Restore VM from snapshot and verify data integrity
    Given the VM "vm1" is stopped
    When the VM is restored from the snapshot, replacing the current VM
    Then the VM should come up running
    And the file "test-backup.txt" should exist with the same content and md5sum
    And the file "test-snapshot.txt" should exist with the same content and md5sum

### Scenario: Restore from snapshot to a new VM and verify data integrity
    When a new VM is created from the snapshot of "vm1"
    Then the new VM should be running
    And the file "test-backup.txt" should exist with the same content and md5sum
    And the file "test-snapshot.txt" should exist in the new VM with the same content and md5sum
