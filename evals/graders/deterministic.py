import json

from opik.evaluation.metrics import base_metric
from opik.evaluation.metrics.score_result import ScoreResult


def _parse_expected(expected_output):
    if isinstance(expected_output, str):
        return json.loads(expected_output)
    return expected_output


class DeviceStateCorrectness(base_metric.BaseMetric):
    """Scores the correctness of the final home state after the agent run.
    Scores 1.0 if all params match, 0.0 if none match
    Partial credit is given if the agent partially matches the expected state in multi-step tasks (e.g., command chaining)
    """

    def __init__(self, name="device_state_correctness"):
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
