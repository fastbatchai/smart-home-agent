import json

from opik.evaluation.metrics import base_metric
from opik.evaluation.metrics.score_result import ScoreResult


def _parse_expected(expected_output):
    if isinstance(expected_output, str):
        return json.loads(expected_output)
    return expected_output


class ToolSelectionQuality(base_metric.BaseMetric):
    def __init__(self, name="det:tool_selection_quality"):
        super().__init__(name=name)

    def score(self, output, expected_output, forbidden_tools=None, **kwargs):
        called_tools = list(output) if output else []
        required_tools = list(expected_output) if expected_output else []
        forbidden = list(forbidden_tools) if forbidden_tools else []

        for tool in called_tools:
            if tool in forbidden:
                return ScoreResult(name=self.name, value=0.0, reason=f"Forbidden tool called: {tool}")

        remaining_required = list(required_tools)
        for tool in called_tools:
            if tool in remaining_required:
                remaining_required.remove(tool)

        if remaining_required:
            return ScoreResult(name=self.name, value=0.0, reason=f"Missing required tools: {remaining_required}")

        return ScoreResult(name=self.name, value=1.0, reason="All required tools called and no forbidden tools used")


class AgentPlanEfficiency(base_metric.BaseMetric):
    def __init__(self, name="det:agent_plan_efficiency"):
        super().__init__(name=name)

    def score(self, output, expected_output, **kwargs):
        called_tools = list(output) if output else []
        optimal_tools = list(expected_output) if expected_output else []

        actual_count = len(called_tools)
        optimal_count = len(optimal_tools)

        if actual_count == 0:
            return ScoreResult(name=self.name, value=0.0, reason="No tools called")

        it = iter(called_tools)
        is_subsequence = all(tool in it for tool in optimal_tools)

        if not is_subsequence:
            return ScoreResult(name=self.name, value=0.0, reason=f"Wrong order or missing tools. Called: {called_tools}, Expected: {optimal_tools}")

        if actual_count == optimal_count:
            return ScoreResult(name=self.name, value=1.0, reason=f"Correct order and count: {called_tools}")

        score = optimal_count / actual_count
        return ScoreResult(name=self.name, value=score, reason=f"Correct order but extra calls. Optimal: {optimal_count}, Actual: {actual_count}")


class MemoryRetrievalQuality(base_metric.BaseMetric):
    def __init__(self, name="det:memory_retrieval_quality"):
        super().__init__(name=name)

    def score(self, output, expected_output, **kwargs):
        context = output or ""
        keywords = list(expected_output) if expected_output else []

        if not keywords:
            return ScoreResult(name=self.name, value=1.0, reason="No keywords to check")

        missing = [kw for kw in keywords if kw.lower() not in context.lower()]
        if not missing:
            return ScoreResult(name=self.name, value=1.0, reason=f"All {len(keywords)} keywords found")
        return ScoreResult(name=self.name, value=0.0, reason=f"Missing keywords: {missing}")


class MemoryRetrievalCoverage(base_metric.BaseMetric):
    def __init__(self, name="det:memory_retrieval_coverage"):
        super().__init__(name=name)

    def score(self, output, expected_output, **kwargs):
        context = output or ""
        keywords = list(expected_output) if expected_output else []

        if not keywords:
            return ScoreResult(name=self.name, value=1.0, reason="No keywords to check")

        found = [kw for kw in keywords if kw.lower() in context.lower()]
        missing = [kw for kw in keywords if kw.lower() not in context.lower()]
        ratio = len(found) / len(keywords)
        reason = f"{len(found)}/{len(keywords)} keywords found"
        if missing:
            reason += f". Missing: {missing}"
        return ScoreResult(name=self.name, value=ratio, reason=reason)


class DeviceStateCorrectness(base_metric.BaseMetric):
    """Scores the correctness of the final home state after the agent run.
    Scores 1.0 if all params match, 0.0 if none match
    Partial credit is given if the agent partially matches the expected state in multi-step tasks (e.g., command chaining)
    """

    def __init__(self, name="det:device_state_correctness"):
        super().__init__(name=name)

    def score(self, output, expected_output, home_state=None, **kwargs):
        if home_state is None:
            return ScoreResult(
                name=self.name, value=0.0, reason="No home_state provided."
            )

        expected_dict = _parse_expected(expected_output)
        correct, total, wrong = 0, 0, []

        for room, devices in expected_dict.items():
            room_state = home_state.get(room, {})
            for device, params in devices.items():
                device_state = room_state.get(device, {})
                for param, expected_value in params.items():
                    total += 1
                    actual = device_state.get(param)
                    if actual == expected_value:
                        correct += 1
                    else:
                        wrong.append(
                            f"{room}.{device}.{param}: expected {expected_value}, got {actual}"
                        )

        if total == 0:
            return ScoreResult(name=self.name, value=1.0, reason="No params to check.")

        score = round(correct / total, 2)
        reason = (
            "All params correct."
            if not wrong
            else f"{correct}/{total} correct. Wrong: {wrong}"
        )
        return ScoreResult(name=self.name, value=score, reason=reason)
