"""LLM-based graders"""

from opik.evaluation.metrics import GEval

TOOL_APPROPRIATENESS_SCORING_RUBRIC = """
### Evaluation Criteria
1- Analyze the user's command to understand what action is being requested.
2- Examine the list of tools the agent called.
3- Determine if the tools called are necessary to fulfill the command (e.g. UpdateDevice for write operations, GetDeviceState for read operations).
4- Check if the agent called get_user_context when the command requires personalization or user preferences.
5- Check for unnecessary or forbidden tool calls that are not relevant to the command.

### Scoring Instructions
Assign a score between 0 and 1 based on the following criteria:
- 1.0 = All tools called are necessary and sufficient for the command, with no unnecessary or missing tools.
- 0.0 = The agent called wrong tools, skipped required tools, or used UpdateDevice for a read-only query.
- between 0 and 1 = The agent partially used the right tools but included unnecessary calls or missed some required ones.
"""

tool_appropriateness_grader = GEval(
    task_introduction="You are evaluating a smart home assistant. Given a user command and the list of tools the agent called, assess whether the tool choices were appropriate for fulfilling the request.",
    evaluation_criteria=TOOL_APPROPRIATENESS_SCORING_RUBRIC,
    name="llm:tool_appropriateness",
)

INTENT_RESOLUTION_SCORING_RUBRIC = """
### Evalution Criteria
1- Analyze the user's command to understand what is being requested.
2- Examine the expected device changes to understand what devices are expected to be changed.
3- Determine if the agent correctly understood the user's intent.
4- Assess if the agent took the appropriate action based on the expected device changes.
5- Check for irrelevent changes or actions that are not related to the user's intent.

### Scoring Instructions
Assign a score between 0 and 1 based on the following criteria:
- 1.0 = The agent correctly interpreted the user's intent and took the appropriate action.
- 0.0 = The agent misunderstood or ignored the user's intent.
- between 0 and 1 = The agent partially understood the user's intent or if the agent tooks actions that are in the expected device changes but not all the expected devices were changed.
"""

intent_relevance_grader = GEval(
    task_introduction="You are evaluating a smart home assistant. Given the user's command, the expected device changes, and the agent's response, assess whether the agent correctly understood the user's intent.",
    evaluation_criteria=INTENT_RESOLUTION_SCORING_RUBRIC,
    name="llm:intent_relevance",
)
