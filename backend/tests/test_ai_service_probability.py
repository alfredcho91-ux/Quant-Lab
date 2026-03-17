"""AI service conditional probability tests."""

import pandas as pd
import pytest

from modules.ai_lab import service as ai_service


@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()


def test_infer_interval_from_prompt_distinguishes_month_and_minute():
    assert ai_service._infer_interval_from_prompt("BTC 1M 기준", "4h") == "1M"
    assert ai_service._infer_interval_from_prompt("BTC 1month 기준", "4h") == "1M"
    assert ai_service._infer_interval_from_prompt("BTC 1m 기준", "4h") == "1m"


def test_process_ai_research_probability_query_runs_by_default(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1, 1],
            "high": [2.1, 2.1, 2.1, 1.1, 2.1, 2.1, 1.1],
            "low": [0.9, 0.9, 0.9, 0.4, 0.9, 0.9, 0.4],
            "close": [2, 2, 2, 0.5, 2, 2, 0.5],
            "volume": [100, 100, 100, 100, 100, 100, 100],
            "MACD_hist": [600, 620, 610, 590, 700, 710, 680],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="macd히스토가 500이고, 2일연속 양봉이 나온경우 다음날 양봉이 나올 확률은?\n\n[UI_CONTEXT]\ncoin=BTC\ninterval=1d",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["backtest_params"] is None
    assert result["backtest_result"] is None
    assert result["analysis_result"] is not None
    assert "조건부 확률 분석" in result["answer"]
    assert "다음 봉 양봉 확률" in result["answer"]
    assert result["analysis_result"]["analysis_type"] == "conditional_probability"
    assert result["analysis_result"]["summary"]["sample_count"] > 0
    assert 0.0 <= result["analysis_result"]["summary"]["gati_index"] <= 100.0


def test_process_ai_research_probability_query_bypasses_api_key_validation(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1, 1],
            "high": [2.1, 2.1, 2.1, 1.1, 2.1, 2.1, 1.1],
            "low": [0.9, 0.9, 0.9, 0.4, 0.9, 0.9, 0.4],
            "close": [2, 2, 2, 0.5, 2, 2, 0.5],
            "volume": [100, 100, 100, 100, 100, 100, 100],
            "MACD_hist": [600, 620, 610, 590, 700, 710, 680],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="macd히스토가 500이고, 2일연속 양봉이 나온경우 다음날 양봉이 나올 확률은?",
        api_key="",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["execution_path"] == "conditional_probability"
    assert result["analysis_result"] is not None
    assert "조건부 확률 분석" in result["answer"]


def test_process_ai_research_probability_supports_rsi_and_stoch_cross(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1, 1],
            "high": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            "low": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "close": [1.5, 1.6, 1.7, 1.4, 1.8, 1.9, 1.7],
            "volume": [100, 100, 100, 100, 100, 100, 100],
            "RSI": [40, 42, 38, 36, 45, 47, 43],
            "stoch_rsi_5k": [20, 25, 30, 32, 45, 55, 48],
            "stoch_rsi_5d": [22, 24, 31, 34, 40, 50, 50],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="2일연속 양봉이고, rsi가 35이상이면서 스토캐스틱이 골든크로스가 나온 상황이야. 이런 경우 다음봉 양봉일 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["analysis_result"] is not None
    condition = result["analysis_result"]["condition"]
    assert "RSI >= 35" in condition["condition_text"]
    assert "골든크로스" in condition["condition_text"]
    components = condition["components"]
    component_types = {item["type"] for item in components}
    assert "streak" in component_types
    assert "numeric_indicator" in component_types
    assert "stochastic_cross" in component_types


def test_process_ai_research_probability_supports_3sto_abbreviation(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1, 1],
            "high": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            "low": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "close": [1.5, 1.6, 1.7, 1.4, 1.8, 1.9, 1.7],
            "volume": [100, 100, 100, 100, 100, 100, 100],
            "RSI": [40, 42, 38, 36, 45, 47, 43],
            "stoch_rsi_5k": [20, 25, 30, 32, 45, 55, 48],
            "stoch_rsi_5d": [22, 24, 31, 34, 40, 50, 50],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="2일연속 양봉이고, rsi가 35이상이면서 3스토 골크인 경우 다음봉 양봉 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    condition = result["analysis_result"]["condition"]
    assert "스토캐(5-3-3) 골든크로스" in condition["condition_text"]
    component_types = {item["type"] for item in condition["components"]}
    assert "stochastic_cross" in component_types


def test_process_ai_research_probability_accepts_korean_gold_cross_variant(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1],
            "high": [2, 2, 2, 2, 2, 2],
            "low": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "close": [1.2, 1.3, 1.4, 1.1, 1.5, 1.6],
            "volume": [100, 100, 100, 100, 100, 100],
            "RSI": [40, 42, 38, 36, 45, 47],
            "stoch_rsi_5k": [20, 25, 30, 32, 45, 55],
            "stoch_rsi_5d": [22, 24, 31, 34, 40, 50],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="2일연속 양봉이고, rsi가 35이상이면서 스토캐스틱이 골드크로스가 나온 상황이야. 이런 경우 다음봉 양봉일 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["analysis_result"] is not None
    condition_text = result["analysis_result"]["condition"]["condition_text"]
    assert "스토캐(5-3-3) 골든크로스" in condition_text


def test_process_ai_research_probability_supports_bollinger_upper_breakout(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [94, 95, 100, 101, 100, 101, 104, 101],
            "high": [96, 97, 103, 104, 101, 104, 106, 102],
            "low": [93, 94, 99, 100, 98, 100, 103, 99],
            "close": [95, 96, 101, 103, 99, 102, 105, 100],
            "volume": [100, 100, 100, 100, 100, 100, 100, 100],
            "BB_Up": [100, 100, 100, 100, 100, 100, 100, 100],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="일봉이 볼린저 밴드 상단을 뚫고 마감한 경우 다음날 양봉 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["analysis_result"] is not None
    condition = result["analysis_result"]["condition"]
    assert "볼린저 상단 종가 돌파" in condition["condition_text"]
    component_types = {item["type"] for item in condition["components"]}
    assert "bollinger_band" in component_types


def test_process_ai_research_probability_supports_korean_decade_ranges(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [10, 10, 10, 10, 10, 10, 10, 10],
            "high": [11, 11, 11, 11, 11, 11, 11, 11],
            "low": [9, 9, 9, 9, 9, 9, 9, 9],
            "close": [10.2, 10.3, 10.1, 10.4, 10.5, 10.2, 10.6, 10.7],
            "volume": [100, 100, 100, 100, 100, 100, 100, 100],
            "RSI": [52, 55, 49, 58, 57, 53, 61, 54],
            "ADX": [41, 44, 39, 47, 43, 48, 52, 45],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="rsi가 50대였고, adx가 40대면 다음날 양봉 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["analysis_result"] is not None
    condition_text = result["analysis_result"]["condition"]["condition_text"]
    assert "RSI >= 50" in condition_text
    assert "RSI < 60" in condition_text
    assert "ADX >= 40" in condition_text
    assert "ADX < 50" in condition_text


def test_process_ai_research_probability_reports_ignored_stoch_when_cross_missing(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1],
            "high": [2, 2, 2, 2, 2, 2],
            "low": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "close": [1.2, 1.3, 1.4, 1.1, 1.5, 1.6],
            "volume": [100, 100, 100, 100, 100, 100],
            "RSI": [40, 42, 38, 36, 45, 47],
            "stoch_rsi_5k": [20, 25, 30, 32, 45, 55],
            "stoch_rsi_5d": [22, 24, 31, 34, 40, 50],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="rsi가 35이상이면서 3스토 조건인 경우 다음봉 양봉 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert "주의: 일부 조건은 파싱/데이터 한계로 제외됨" in result["answer"]
    ignored = result["analysis_result"]["condition"]["ignored_conditions"]
    assert "스토캐 조건(크로스 타입 미인식)" in ignored


def test_process_ai_research_probability_supports_or_parentheses(monkeypatch):
    test_df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1, 1, 1, 1],
            "high": [2, 2, 2, 2, 2, 2, 2, 2],
            "low": [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "close": [1.2, 1.3, 1.4, 1.1, 1.5, 1.6, 1.7, 1.3],
            "volume": [100, 100, 100, 100, 100, 100, 100, 100],
            "RSI": [48, 50, 33, 31, 52, 54, 36, 34],
        }
    )

    def fake_call_gemini(*args, **kwargs):
        raise AssertionError("Probability query path should not call _call_gemini")

    def fake_load_data_for_analysis(coin, interval, use_csv, total_candles):
        return test_df.copy(), "csv"

    def fake_build_indicator_adapter(df, mode="backtest", prepare_kwargs=None):
        return df

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call_gemini)
    monkeypatch.setattr(ai_service, "load_data_for_analysis", fake_load_data_for_analysis)
    monkeypatch.setattr(ai_service, "build_indicator_adapter", fake_build_indicator_adapter)

    result = ai_service.process_ai_research(
        prompt="(rsi >= 45 또는 rsi <= 35) 그리고 2일연속 양봉인 경우 다음봉 양봉 확률은?",
        api_key="AIzaDummyKey",
        model="gemini-3-flash",
        provider="gemini",
    )

    assert result["error"] is None
    assert result["analysis_result"] is not None
    condition = result["analysis_result"]["condition"]
    assert "OR" in condition["condition_text"]
    assert "AND" in condition["condition_text"]
    assert "(" in condition["condition_text"]
    assert ")" in condition["condition_text"]
    tokens = condition.get("expression_tokens", [])
    assert "OR" in tokens
    assert "AND" in tokens
