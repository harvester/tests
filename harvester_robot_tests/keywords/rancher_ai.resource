*** Settings ***
Documentation    Rancher AI Keywords - Reusable keywords for Rancher AI operations
Library          ../libs/keywords/rancher_ai_keywords.py
Resource         rancher.resource

*** Variables ***
# Required suite configuration; populated by suite setup.
${HARVESTER_CLUSTER_ID}    ${EMPTY} 

# Evaluation context; populated by the prompt keywords.
${PROMPT}      ${EMPTY}
${RESPONSE}    ${EMPTY}

*** Keywords ***
Wait For Rancher AI Deployments Ready
    [Documentation]    Wait for AI deployments in Rancher's local cluster.
    ...    Uses cattle-ai-agent-system and gives each deployment its own timeout.
    ...    Fails on the first unsuccessful wait; does not skip or ignore failures.
    FOR    ${deployment}    IN    rancher-ai-agent    rancher-mcp-server    harvester-mcp-server
        rancher.Wait For Deployment Ready
        ...    local    cattle-ai-agent-system    ${deployment}    20
    END

Prompt Rancher
    [Arguments]    ${_prompt}
    [Documentation]    Prompt Rancher AI
    Should Not Be Empty    ${HARVESTER_CLUSTER_ID}
    ...    HARVESTER_CLUSTER_ID must be configured in suite setup.
    ${conversation_result}=    rancher_ai_keywords.prompt
    ...    ${_prompt}    ${HARVESTER_CLUSTER_ID}
    Log    ${conversation_result}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}

Evaluate Response
    [Arguments]    ${prompt}    ${response}    ${extra_criteria}=None    ${evaluation_steps}=None
    [Documentation]    DeepEval the RESPONSE is contextually relevant and positive to the PROMPT
    ${evaluation_result}=    rancher_ai_keywords.evaluate_response
    ...    ${prompt}    ${response}    ${extra_criteria}    ${evaluation_steps}
    Log    Prompt: ${prompt}
    Log    Response: ${response}
    Log    ${evaluation_result}
    Log    Judge Reason: ${evaluation_result.reason}
    RETURN    ${evaluation_result}

Rancher should reply
    [Arguments]    ${extra_criteria}=None    ${evaluation_steps}=None
    ${evaluation_result}=    Evaluate Response
    ...    ${PROMPT}    ${RESPONSE}    ${extra_criteria}    ${evaluation_steps}
    Should Be True    ${evaluation_result.passed}    ${evaluation_result.reason}

Prompt Rancher And Confirm
    [Documentation]    Send a request and reply once to its validated confirmation block.
    ...    Fails if confirmation is missing, malformed, incomplete, or requested again.
    ...    Uses the same connection for both turns; does not reconnect or replay.
    [Arguments]    ${_prompt}    ${decision}=yes
    Should Not Be Empty    ${HARVESTER_CLUSTER_ID}
    ...    HARVESTER_CLUSTER_ID must be configured in suite setup.
    ${conversation_result}=    rancher_ai_keywords.prompt_and_confirm
    ...    ${_prompt}    ${HARVESTER_CLUSTER_ID}    ${decision}
    Log    ${conversation_result}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}
