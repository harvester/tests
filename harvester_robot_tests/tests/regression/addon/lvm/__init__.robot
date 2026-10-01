*** Settings ***
Documentation    LVM addon suites. The addon and the volume group are shared by
...              every suite in this directory, so they are prepared and cleaned
...              up here instead of in suites of their own. PabotLib runs the
...              setup in whichever process gets here first while the others
...              wait for it, and runs the teardown only after every LVM suite
...              has finished. Under plain robot both are an ordinary suite
...              setup and teardown. See README.md in this directory.

Library          pabot.PabotLib
Resource         ../../../../keywords/lvm.resource

Suite Setup      Run Setup Only Once    Prepare LVM Test Environment
Suite Teardown   Run Teardown Only Once    Teardown LVM Test Environment
