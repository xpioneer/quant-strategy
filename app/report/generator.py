from typing import Any


class ReportGenerator:
    def generate_summary(self, backtest_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "strategy": backtest_result.get("strategy", "unknown"),
            "return_rate": backtest_result.get("return_rate", 0.0),
            "status": "ok",
        }
