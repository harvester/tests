*** Settings ***
Documentation   Example for Suite documents
Force Tags      Authentication  basic
Suite Setup     Log Browser Settings


*** Keywords ***
Log Browser Settings
    Log  Default browser timeout is ${BROWSER_WAIT_TIMEOUT}   level=warn