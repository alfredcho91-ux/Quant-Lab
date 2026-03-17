"""AI service optimization flow tests."""

import pytest

from modules.ai_lab import service as ai_service


@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()


def test_looks_like_optimization_request_detects_ko_and_en():
    assert ai_service._looks_like_optimization_request("이 전략 파라미터 최적화해줘")
    assert ai_service._looks_like_optimization_request("please optimize this strategy")
    assert not ai_service._looks_like_optimization_request("RSI 확률 분석해줘")


def test_process_ai_research_runs_auto_optimization_when_requested(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "초기 파라미터를 만들었습니다.",
            "params": {
                "coin": "BTC",
                "interval": "4h",
                "strategy_id": "RSI",
                "direction": "Long",
                "tp_pct": 2.0,
                "sl_pct": 1.0,
            },
            "error": None,
        }

    captured = {}

    def fake_optimizer(bt_params, prompt):
        captured["params"] = bt_params
        captured["prompt"] = prompt
        return {
            "answer": "[자동 최적화 완료] 탐색 12회",
            "params": {
                "coin": "BTC",
                "interval": "4h",
                "strategy_id": "RSI",
                "direction": "Long",
                "tp_pct": 2.6,
                "sl_pct": 1.1,
                "max_bars": 48,
                "use_csv": True,
            },
            "backtest_result": {"success": True, "summary": {}, "trades": [], "chart_data": []},
            "analysis_result": {
                "analysis_type": "optimization_characteristics",
                "summary": {
                    "trial_count": 12,
                    "bucket_size": 3,
                    "top_avg_oos_pnl": 10.5,
                    "bottom_avg_oos_pnl": -2.1,
                    "top_avg_oos_win_rate": 63.3,
                    "bottom_avg_oos_win_rate": 41.2,
                },
                "highlights": [
                    {
                        "param": "tp_pct",
                        "label": "TP%",
                        "direction": "higher_better",
                        "top_mean": 2.8,
                        "bottom_mean": 1.1,
                        "effect_pct": 57.0,
                        "interpretation": "높을수록 성과 우세",
                    }
                ],
            },
            "error": None,
        }

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "_run_backtest_parameter_optimization", fake_optimizer)

    result = ai_service.process_ai_research(
        prompt="RSI 전략 최적화해줘\n\n[UI_CONTEXT]\ncoin=BTC\ninterval=4h",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["execution_path"] == "llm_backtest_optimized"
    assert result["backtest_result"] is not None
    assert "자동 최적화" in result["answer"]
    assert result["backtest_params"]["tp_pct"] == 2.6
    assert result["analysis_result"] is not None
    assert result["analysis_result"]["analysis_type"] == "optimization_characteristics"
    assert captured["params"].use_csv is True
    assert captured["prompt"] == "RSI 전략 최적화해줘"


def test_build_optimization_characteristics_extracts_prominent_parameter_signals():
    trial_rows = []
    for idx in range(12):
        trial_rows.append(
            {
                "score": float(idx),
                "params": {
                    "tp_pct": 1.0 + (idx * 0.2),
                    "sl_pct": 2.0 - (idx * 0.05),
                    "max_bars": 20 + idx,
                    "rsi_ob": 60 + idx,
                    "sma1_len": 10 + idx,
                    "sma2_len": 40 + idx,
                },
                "oos_total_pnl": -5.0 + (idx * 1.5),
                "oos_win_rate": 35.0 + (idx * 2.0),
                "oos_trades": 20 + idx,
            }
        )

    analysis = ai_service._build_optimization_characteristics(
        trial_rows=trial_rows,
        prompt="이 전략 파라미터 최적화해줘",
    )

    assert analysis is not None
    assert analysis["analysis_type"] == "optimization_characteristics"
    assert analysis["summary"]["trial_count"] == 12
    assert analysis["summary"]["bucket_size"] >= 2
    assert analysis["highlights"]
    top_highlight = analysis["highlights"][0]
    assert top_highlight["effect_pct"] >= 18.0
    assert top_highlight["direction"] in {"higher_better", "lower_better"}


def test_build_optimization_characteristics_uses_null_when_oos_stats_are_missing():
    trial_rows = []
    for idx in range(12):
        trial_rows.append(
            {
                "score": float(idx),
                "params": {
                    "tp_pct": 1.0 + (idx * 0.2),
                    "sl_pct": 2.0 - (idx * 0.05),
                    "max_bars": 20 + idx,
                    "rsi_ob": 60 + idx,
                    "sma1_len": 10 + idx,
                    "sma2_len": 40 + idx,
                },
                "oos_total_pnl": None,
                "oos_win_rate": None,
                "oos_trades": 0,
            }
        )

    analysis = ai_service._build_optimization_characteristics(
        trial_rows=trial_rows,
        prompt="이 전략 파라미터 최적화해줘",
    )

    assert analysis is not None
    assert analysis["summary"]["top_avg_oos_pnl"] is None
    assert analysis["summary"]["bottom_avg_oos_pnl"] is None
    assert analysis["summary"]["top_avg_oos_win_rate"] is None
    assert analysis["summary"]["bottom_avg_oos_win_rate"] is None


def test_optimization_summary_uses_base_params_as_baseline(monkeypatch):
    call_index = {"value": 0}

    def fake_run_backtest_advanced_service(params):
        call_index["value"] += 1
        if call_index["value"] == 1:
            return {
                "success": True,
                "out_of_sample": {
                    "summary": {
                        "n_trades": 20,
                        "win_rate": 50.0,
                        "total_pnl": 1.0,
                        "avg_pnl": 0.05,
                        "liq_count": 0,
                    }
                },
                "full": {"summary": {"n_trades": 20, "win_rate": 50.0, "total_pnl": 1.0, "avg_pnl": 0.05}},
                "trades": [],
                "chart_data": [],
            }
        return {
            "success": True,
            "out_of_sample": {
                "summary": {
                    "n_trades": 22,
                    "win_rate": 60.0,
                    "total_pnl": 10.0,
                    "avg_pnl": 0.2,
                    "liq_count": 0,
                }
            },
            "full": {"summary": {"n_trades": 22, "win_rate": 60.0, "total_pnl": 10.0, "avg_pnl": 0.2}},
            "trades": [],
            "chart_data": [],
        }

    def fake_run_backtest_service(params):
        return {
            "success": True,
            "summary": {"n_trades": 22, "win_rate": 60.0, "total_pnl": 10.0, "avg_pnl": 0.2, "liq_count": 0},
            "trades": [],
            "chart_data": [],
        }

    monkeypatch.setattr(ai_service, "OPTIMIZATION_TRIALS", 1)
    monkeypatch.setattr(ai_service, "run_backtest_advanced_service", fake_run_backtest_advanced_service)
    monkeypatch.setattr(ai_service, "run_backtest_service", fake_run_backtest_service)

    base_params = ai_service.BacktestParams(
        coin="BTC",
        interval="4h",
        strategy_id="RSI",
        direction="Long",
    )
    result = ai_service._run_backtest_parameter_optimization(base_params, "RSI 전략 최적화")

    assert result["error"] is None
    assert "기준(OOS): 수익률 1.00%" in result["answer"]
    assert "최적(OOS): 수익률 10.00%" in result["answer"]


def test_process_ai_research_optimization_without_params_returns_clarification(monkeypatch):
    def fake_call_gemini(*args, **kwargs):
        return {
            "thought": "파라미터를 명시하지 못했습니다.",
            "params": None,
            "error": None,
        }

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)

    result = ai_service.process_ai_research(
        prompt="최적화해줘\n\n[UI_CONTEXT]\ncoin=ETH\ninterval=1d",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["execution_path"] == "optimization_clarification"
    assert result["needs_clarification"] is True
    assert result["backtest_result"] is None
    assert result["clarifying_questions"] is not None
    assert len(result["clarifying_questions"]) >= 3


def test_process_ai_research_optimization_probability_prompt_returns_clarification():
    result = ai_service.process_ai_research(
        prompt="macd히스토가 500 이상이고 최적화해서 다음날 양봉 확률 알려줘",
        api_key="AIzaDummyKey",
        model=ai_service.GEMINI_DEFAULT_MODEL,
        provider="gemini",
    )

    assert result["error"] is None
    assert result["execution_path"] == "optimization_clarification"
    assert result["needs_clarification"] is True


def test_score_advanced_backtest_prefers_stable_oos_payload():
    unstable = {
        "in_sample": {"summary": {"n_trades": 80, "win_rate": 72.0, "total_pnl": 45.0, "avg_pnl": 0.56}},
        "out_of_sample": {"summary": {"n_trades": 10, "win_rate": 42.0, "total_pnl": 4.5, "avg_pnl": 0.12}},
        "full": {"summary": {"n_trades": 90, "win_rate": 68.0, "total_pnl": 49.5, "avg_pnl": 0.49}},
    }
    stable = {
        "in_sample": {"summary": {"n_trades": 60, "win_rate": 59.0, "total_pnl": 20.0, "avg_pnl": 0.33}},
        "out_of_sample": {"summary": {"n_trades": 32, "win_rate": 57.0, "total_pnl": 13.0, "avg_pnl": 0.40}},
        "full": {"summary": {"n_trades": 92, "win_rate": 58.0, "total_pnl": 33.0, "avg_pnl": 0.36}},
    }

    unstable_score = ai_service._score_advanced_backtest(unstable)
    stable_score = ai_service._score_advanced_backtest(stable)

    assert stable_score > unstable_score


def test_build_ui_result_from_advanced_payload_normalizes_required_summary_fields():
    advanced_result = {
        "chart_data": [{"open_dt": "2024-01-01 00:00", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}],
        "trades": [],
        "full": {"summary": {"n_trades": 3, "win_rate": 66.6, "total_pnl": 2.5, "avg_pnl": 0.8}},
    }
    ui_result = ai_service._build_ui_result_from_advanced_payload(advanced_result)

    assert ui_result["success"] is True
    assert ui_result["summary"]["n_trades"] == 3
    assert ui_result["summary"]["liq_count"] == 0
