*** Settings ***
Documentation    Rancher AI Keywords - Reusable keywords for Rancher AI operations
Library          ../libs/keywords/rancher_ai_keywords.py


*** Keywords ***
Prompt Rancher
    [Arguments]    ${prompt}    ${harvester_cluster_id}
    [Documentation]    Prompt Rancher AI and returns the response.
    ${conversation_result}=    rancher_ai_keywords.prompt    ${prompt}    ${harvester_cluster_id}
    Log    ${conversation_result}
    RETURN    ${conversation_result}

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
    [Arguments]    ${prompt}    ${response}    ${extra_criteria}=None    ${evaluation_steps}=None
    ${evaluation_result}=    Evaluate Response
    ...    ${prompt}    ${response}    ${extra_criteria}    ${evaluation_steps}
    Should Be True    ${evaluation_result.passed}    ${evaluation_result.reason}

Prompt Rancher And Confirm
    [Documentation]    Send a request and reply once to its validated confirmation block.
    ...    Fails if confirmation is missing, malformed, incomplete, or requested again.
    ...    Uses the same connection for both turns; does not reconnect or replay.
    ...    Returns both initial_response and final_response; answer is the final narrative.
    [Arguments]    ${prompt}    ${harvester_cluster_id}    ${decision}=yes
    ${conversation_result}=    rancher_ai_keywords.prompt_and_confirm
    ...    ${prompt}    ${harvester_cluster_id}    ${decision}
    RETURN    ${conversation_result}
