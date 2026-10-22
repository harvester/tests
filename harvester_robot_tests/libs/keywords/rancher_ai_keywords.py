"""
Rancher AI Keywords
Layer 3: Keyword wrappers for Robot Framework
"""
from rancher_ai.client import RancherAIClient    # noqa E402
from rancher_ai.evaluation.evaluator import ResponseEvaluator    # noqa E402
from rancher_ai.models import ConfirmationConversationResult    # noqa E402
from typing import Optional


class rancher_ai_keywords:
    """Rancher AI keyword wrapper
    """
    def __init__(self):
        self.chat = RancherAIClient()
        self.evaluator = ResponseEvaluator()

    def prompt(self, prompt: str, harvester_cluster_id: str):
        return self.chat.prompt(prompt, harvester_cluster_id)

    def evaluate_response(
        self,
        input: str,
        response: str,
        extra_criteria: Optional[str] = None,
        evaluation_steps: Optional[list[str]] = None,
    ):
        """
        Args:
            input: str, prompt send to Rancher AI
                e.g. "List VM images in the selected cluster."
            response: str, response from Rancher AI
                e.g. "Available images: ubuntu-22.04, opensuse-leap."
            extra_criteria: optional str,
                e.g. "The response must contains a ubuntu-22.04 image."
            evaluation_steps: optional, a list of str,
                e.g.
                [
                "Compare the image names in ACTUAL_OUTPUT with EXPECTED_OUTPUT.",
                "Require all expected image names; ignore order and formatting.",
                "Penalize additional image names not supported by EXPECTED_OUTPUT."
                ]
        """
        return self.evaluator.evaluate_response(
            input, response, extra_criteria, evaluation_steps,
        )

    def prompt_and_confirm(
        self, prompt: str, harvester_cluster_id: str, decision: str = "yes",
    ) -> ConfirmationConversationResult:
        """Reply once to a validated confirmation request and preserve both turns.

        Args:
            prompt: Original user request, not the confirmation answer.
            harvester_cluster_id: Target Harvester cluster ID.
            decision: yes to confirm, no to cancel; no implicit boolean conversion.
        """
        return self.chat.prompt_and_confirm(prompt, harvester_cluster_id, decision)
