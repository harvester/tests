*** Settings ***
Documentation    Rancher AI Keywords - Reusable keywords for Rancher AI operations
Library          ../libs/keywords/rancher_ai_keywords.py


*** Keywords ***
Prompt
    [Arguments]    ${prompt}    ${harvester_cluster_id}
    [Documentation]    Sends input to Rancher AI and returns the response.
    ${conversation_result}=    rancher_ai_keywords.prompt    ${prompt}    ${harvester_cluster_id}
    Log    ${conversation_result}
    RETURN    ${conversation_result}

Response Evaluation
    [Arguments]    ${prompt}    ${response}    ${acceptance_criteria}=None    ${evaluation_steps}=None
    [Documentation]    DeepEval the ACTUAL_OUTPUT is contextually relevant to the INPUT context
    ${evaluation_result}=    rancher_ai_keywords.evaluate_response
    ...    ${prompt}    ${response}    ${acceptance_criteria}    ${evaluation_steps}
    Log    Prompt: ${prompt}
    Log    Response: ${response}
    Log    ${evaluation_result}
    Log    Judge Reason: ${evaluation_result.reason}
    RETURN    ${evaluation_result}

Response Evaluation Should Pass
    [Arguments]    ${prompt}    ${response}    ${criteria}=None    ${evaluation_steps}=None
    ${evaluation_result}=    Response Evaluation
    ...    ${prompt}    ${response}    ${criteria}    ${evaluation_steps}
    Should Be True    ${evaluation_result.passed}    ${evaluation_result.reason}

Response Evaluation Should Fail
    [Arguments]    ${prompt}    ${response}    ${criteria}=None    ${evaluation_steps}=None
    ${evaluation_result}=    Response Evaluation
    ...    ${prompt}    ${response}    ${criteria}    ${evaluation_steps}
    Should Not Be True    ${evaluation_result.passed}    ${evaluation_result.reason}