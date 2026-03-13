"""LLM-based graders using Opik's LiteLLM client for multi-provider support."""

import json
from typing import Any

from opik.evaluation import models
from opik.evaluation.metrics import base_metric
from opik.evaluation.metrics.score_result import ScoreResult


class ToolAppropriatenessGrader(base_metric.BaseMetric):
    """
    LLM-as-judge grader for tool appropriateness.
    Evaluates whether the agent called the right tools for the given command.
    """

    _PROMPT = """
You are evaluating a smart home assistant. Assess whether the tools the agent called were appropriate for the user's command.

User command: {command}
Tools called by the agent: {called_tools}
Expected tools: {expected_tools}
Forbidden tools (must not be called): {forbidden_tools}

### Evaluation Criteria
1- Analyze the user's command to understand what action is being requested.
2- Determine if the tools called are necessary to fulfill the command (e.g. UpdateDevice for write operations, GetDeviceState for read operations).
3- Check if the agent called get_user_context when the command requires personalization or user preferences.
4- Check if any forbidden tools were called.
5- Check if any expected tools were missing.

### Scoring Instructions
Respond with a JSON object only, no backticks or extra text:
{{
    "score": <float between 0 and 1>,
    "reason": "<one sentence explanation>"
}}
- 1.0 = All tools called are necessary and sufficient, no forbidden or missing tools.
- 0.0 = Wrong tools called, required tools missing, or forbidden tools used.
- between 0 and 1 = Partially correct tool usage.
"""

    def __init__(self, name: str = "llm:tool_appropriateness", model_name: str = "gpt-4o-mini"):
        super().__init__(name=name)
        self._llm = models.LiteLLMChatModel(model_name=model_name)

    def score(self, output, input=None, expected_output=None, forbidden_tools=None, **kwargs: Any) -> ScoreResult:
        prompt = self._PROMPT.format(
            command=input or "",
            called_tools=output or [],
            expected_tools=expected_output or [],
            forbidden_tools=forbidden_tools or [],
        )
        response = self._llm.generate_string(input=prompt)
        parsed = json.loads(response)
        return ScoreResult(name=self.name, value=parsed["score"], reason=parsed["reason"])


class IntentRelevanceGrader(base_metric.BaseMetric):
    """
    LLM-as-judge grader for intent resolution.
    Evaluates whether the agent correctly understood and acted on the user's intent.
    """

    _PROMPT = """
You are evaluating a smart home assistant. Assess whether the agent correctly understood the user's intent.

User command: {command}
Expected device changes: {expected_output}
Agent's response: {agent_response}

### Evaluation Criteria
1- Analyze the user's command to understand what is being requested.
2- Examine the expected device changes to understand what devices should have been changed.
3- Determine if the agent correctly understood the user's intent.
4- Assess if the agent took the appropriate action based on the expected device changes.
5- Check for irrelevant changes or actions not related to the user's intent.

### Scoring Instructions
Respond with a JSON object only, no backticks or extra text:
{{
    "score": <float between 0 and 1>,
    "reason": "<one sentence explanation>"
}}
- 1.0 = The agent correctly interpreted the user's intent and took the appropriate action.
- 0.0 = The agent misunderstood or ignored the user's intent.
- between 0 and 1 = The agent partially understood the intent or only acted on some of the expected changes.
"""

    def __init__(self, name: str = "llm:intent_relevance", model_name: str = "gpt-4o-mini"):
        super().__init__(name=name)
        self._llm = models.LiteLLMChatModel(model_name=model_name)

    def score(self, output, input=None, expected_output=None, **kwargs: Any) -> ScoreResult:
        prompt = self._PROMPT.format(
            command=input or "",
            expected_output=expected_output or "",
            agent_response=output or "",
        )
        response = self._llm.generate_string(input=prompt)
        parsed = json.loads(response)
        return ScoreResult(name=self.name, value=parsed["score"], reason=parsed["reason"])


tool_appropriateness_grader = ToolAppropriatenessGrader()
intent_relevance_grader = IntentRelevanceGrader()
