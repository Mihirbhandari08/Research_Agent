"""
app/harness/policies/evaluator.py
=================================
Policy evaluation logic enforcing tool and action permissions before execution.
"""

from typing import Literal

from app.harness.exceptions import PolicyViolationError
from app.harness.policies.models import ActionPolicy

DecisionType = Literal["allow", "deny", "require_approval"]


class PolicyEvaluator:
    """Evaluates runtime actions against configured security permissions."""

    def __init__(self, policy: ActionPolicy) -> None:
        self.policy = policy

    def evaluate(self, action: str) -> DecisionType:
        """
        Evaluates permissions for a given action or tool name.

        Args:
            action: Name of the action or tool to evaluate (e.g., 'web_search').

        Returns:
            DecisionType: "allow", "deny", or "require_approval".
        """
        # 1. Explicitly blocked/forbidden actions take precedence
        if action in self.policy.forbidden_actions:
            return "deny"

        # 2. Check if action requires human-in-the-loop approval
        if action in self.policy.require_approval_actions:
            return "require_approval"

        # 3. If a whitelist is configured, check if action is permitted on it
        if self.policy.allowed_actions:
            if action in self.policy.allowed_actions:
                return "allow"
            else:
                # Secure default: whitelists act as exclusive restrictions
                return "deny"

        # 4. Secure default: If no whitelist is specified, allow by default (as long as it wasn't blacklisted)
        return "allow"

    def check_permission(self, action: str) -> None:
        """
        Verifies if an action is allowed. Raises PolicyViolationError if denied.

        Args:
            action: The action or tool to check.

        Raises:
            PolicyViolationError: If the policy evaluator denies the action.
        """
        decision = self.evaluate(action)
        if decision == "deny":
            raise PolicyViolationError(
                message=f"Action '{action}' violates execution policies and is forbidden.",
                action=action,
            )
