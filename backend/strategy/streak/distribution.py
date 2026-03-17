"""Time-based distribution helpers for streak statistics."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    from config.settings import ANALYSIS_TIMEZONE
except Exception:  # pragma: no cover - fallback for non-standard import contexts
    ANALYSIS_TIMEZONE = "America/New_York"

from utils.stats import safe_float

logger = logging.getLogger(__name__)
WEEKDAY_NAMES_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@lru_cache(maxsize=1)
def _get_data_service_functions() -> Tuple[Any, Any]:
    """Resolve data-service functions without loading a duplicate module object."""
    try:
        module = import_module("utils.data_service")
    except ImportError:
        backend_path = Path(__file__).resolve().parents[2]
        backend_path_str = str(backend_path)
        if backend_path_str not in sys.path:
            sys.path.insert(0, backend_path_str)
        module = import_module("utils.data_service")
    return module.load_csv_data, module.fetch_live_data


def _get_normalize_datetime_index():
    """Lazy import to avoid circular imports with streak.common."""
    from strategy.streak.common import normalize_datetime_index

    return normalize_datetime_index


def calculate_intraday_distribution(
    pattern_result_dates: List[pd.Timestamp],
    interval: str,
    coin: str,
    timezone_offset: Optional[int] = None,
) -> Dict[str, Any]:
    """
    결과 도출일(패턴 매칭 후 반등일)의 4시간봉을 분석하여
    뉴욕 시간(EST/EDT) 기준 시간대별 저점/고점 발생 확률 계산

    Args:
        pattern_result_dates: 결과 도출일 리스트 (패턴 다음 날 또는 패턴 매칭 날짜)
        interval: 타임프레임 ('1d', '3d'만 지원)
        coin: 코인 심볼 (4시간봉 데이터 로드용)
        timezone_offset: 하위 호환성용 파라미터 (사용되지 않음)
                         ⚠️ Deprecated: pytz + ANALYSIS_TIMEZONE을 사용하므로 이 파라미터는 무시됩니다.
                         하위 호환성을 위해 유지되지만 실제로는 사용되지 않습니다.

    Returns:
        dict with low_window, avg_volatility, hourly_low_probability, hourly_high_probability
        시간대 라벨 형식: "HH:MM-HH:MM EST/EDT"
    """
    import pytz

    _ = timezone_offset  # Backward compatibility parameter (unused by design)

    # 일봉/3일봉만 지원
    if interval not in ["1d", "3d"]:
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": "시간대별 분석은 일봉(1d) 또는 3일봉(3d)에만 적용됩니다.",
        }

    if len(pattern_result_dates) == 0:
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": "분석할 날짜가 없습니다",
        }

    try:
        load_csv_data, fetch_live_data = _get_data_service_functions()
        # 4시간봉 데이터 로드
        df_4h, _ = load_csv_data(coin, "4h")
        if df_4h is None or df_4h.empty:
            df_4h = fetch_live_data(f"{coin}/USDT", "4h", total_candles=3000)

        if df_4h is None or df_4h.empty:
            logger.warning("[%s] 4시간봉 데이터 로드 실패", interval)
            return {
                "low_window": None,
                "avg_volatility": None,
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "4시간봉 데이터를 로드할 수 없습니다",
            }

        # 인덱스를 datetime으로 변환 및 UTC 타임존 통일
        if not isinstance(df_4h.index, pd.DatetimeIndex):
            # open_dt 컬럼이 있으면 우선 사용 (이미 datetime으로 변환됨)
            if "open_dt" in df_4h.columns:
                if not pd.api.types.is_datetime64_any_dtype(df_4h["open_dt"]):
                    df_4h["open_dt"] = pd.to_datetime(df_4h["open_dt"])
                df_4h.set_index("open_dt", inplace=True)
            elif "open_time" in df_4h.columns:
                # open_time이 밀리초 타임스탬프인 경우 처리
                if pd.api.types.is_numeric_dtype(df_4h["open_time"]):
                    df_4h["open_time"] = pd.to_datetime(df_4h["open_time"], unit="ms")
                else:
                    df_4h["open_time"] = pd.to_datetime(df_4h["open_time"])
                df_4h.set_index("open_time", inplace=True)
            else:
                df_4h.index = pd.to_datetime(df_4h.index)

        # ✅ 개선: 4시간봉 인덱스를 UTC로 통일 (타임존 일관성 보장)
        if df_4h.index.tzinfo is None:
            df_4h.index = df_4h.index.tz_localize("UTC")
        elif str(df_4h.index.tzinfo) != "UTC":
            df_4h.index = df_4h.index.tz_convert("UTC")

        # 날짜 중복 제거 및 정규화 (UTC로 통일)
        unique_dates = []
        seen_dates = set()
        for date in pattern_result_dates:
            if isinstance(date, str):
                date_ts = pd.to_datetime(date)
            elif isinstance(date, pd.Timestamp):
                date_ts = date
            else:
                try:
                    date_ts = pd.to_datetime(date)
                except Exception:
                    continue

            # ✅ 개선: UTC로 통일 후 날짜만 추출 (타임존 일관성 보장)
            if date_ts.tzinfo is None:
                date_ts = date_ts.tz_localize("UTC")
            elif str(date_ts.tzinfo) != "UTC":
                date_ts = date_ts.tz_convert("UTC")

            date_only = date_ts.normalize()  # 날짜만 추출 (시간 제거)
            if date_only not in seen_dates:
                unique_dates.append(date_only)
                seen_dates.add(date_only)

        if len(unique_dates) == 0:
            return {
                "low_window": None,
                "avg_volatility": None,
                "hourly_low_probability": {},
                "hourly_high_probability": {},
                "note": "유효한 날짜가 없습니다",
            }

        # 시간대별 저점/고점 발생 횟수 카운트 (뉴욕시간 기준)
        # 구간: 00:00-04:00, 04:00-08:00, 08:00-12:00, 12:00-16:00, 16:00-20:00, 20:00-24:00 (EST/EDT)
        low_hour_counts = {i: 0 for i in range(6)}  # 0~5: 뉴욕시간 4시간 구간 인덱스
        high_hour_counts = {i: 0 for i in range(6)}
        volatility_sum = 0.0
        volatility_count = 0
        valid_date_count = 0  # 최저가와 최고가가 다른 시간 구간에 있는 날짜 수

        # pytz 사용: 날짜별 DST 자동 반영
        ny_tz = pytz.timezone(ANALYSIS_TIMEZONE)

        def hour_to_interval_index(local_hour: int) -> int:
            """시간(0-23)을 4시간 구간 인덱스(0-5)로 변환"""
            return local_hour // 4

        def get_est_label(interval_idx: int) -> str:
            """뉴욕 시간 구간 라벨 생성"""
            start = interval_idx * 4
            end = (interval_idx + 1) * 4
            return f"{start:02d}:00-{end:02d}:00 EST/EDT"

        # 날짜별 통계를 미리 계산해 반복 스캔 비용 제거
        day_index = df_4h.index.normalize()
        grouped_by_day = df_4h.groupby(day_index, sort=False)
        low_idx_by_day = grouped_by_day["low"].idxmin().to_dict()
        high_idx_by_day = grouped_by_day["high"].idxmax().to_dict()

        valid_open_mask = df_4h["open"] > 0
        if valid_open_mask.any():
            day_volatility_series = (
                ((df_4h.loc[valid_open_mask, "high"] - df_4h.loc[valid_open_mask, "low"]) / df_4h.loc[valid_open_mask, "open"])
                * 100
            ).groupby(day_index[valid_open_mask]).mean()
            day_volatility_by_day = day_volatility_series.to_dict()
        else:
            day_volatility_by_day = {}

        for date in unique_dates:
            try:
                low_idx_original = low_idx_by_day.get(date)
                high_idx_original = high_idx_by_day.get(date)
                if low_idx_original is None or high_idx_original is None:
                    continue

                # 날짜별 DST를 반영해 뉴욕시간으로 변환 후 구간 인덱스 계산
                low_ts = pd.Timestamp(low_idx_original)
                high_ts = pd.Timestamp(high_idx_original)
                if low_ts.tzinfo is None:
                    low_ts = low_ts.tz_localize("UTC")
                if high_ts.tzinfo is None:
                    high_ts = high_ts.tz_localize("UTC")

                low_hour_ny = low_ts.tz_convert(ny_tz).hour
                high_hour_ny = high_ts.tz_convert(ny_tz).hour
                low_interval_idx = hour_to_interval_index(low_hour_ny)
                high_interval_idx = hour_to_interval_index(high_hour_ny)

                # 저점과 고점이 다른 시간 구간에 있는 경우만 valid_date_count 증가
                # (같은 구간에 있으면 확률 계산이 왜곡됨)
                if low_interval_idx != high_interval_idx:
                    valid_date_count += 1
                    low_hour_counts[low_interval_idx] += 1
                    high_hour_counts[high_interval_idx] += 1

                day_volatility = float(day_volatility_by_day.get(date, 0.0))
                volatility_sum += day_volatility
                volatility_count += 1
            except Exception as exc:
                logger.warning("날짜 %s 처리 중 에러: %s", date.date(), exc)
                continue

        # 확률 계산 (유효한 날짜 수로 나누기) - 뉴욕시간 기준 24시간 모두 표시
        # 최저가와 최고가가 다른 4시간봉에 있는 날짜만 유효한 데이터로 간주
        total_dates = len(unique_dates)
        hourly_low_prob = {}
        hourly_high_prob = {}

        # 뉴욕시간(EST/EDT) 기준 4시간 구간 라벨
        hour_labels = [get_est_label(i) for i in range(6)]

        if valid_date_count > 0:
            # 저점 확률 (모든 6개 구간 표시, 0%도 포함)
            for idx in range(6):
                count = low_hour_counts.get(idx, 0)
                prob = (count / valid_date_count) * 100
                safe_prob = safe_float(prob)
                hourly_low_prob[hour_labels[idx]] = round(safe_prob, 2) if safe_prob is not None else 0.0

            # 고점 확률 (모든 6개 구간 표시, 0%도 포함)
            for idx in range(6):
                count = high_hour_counts.get(idx, 0)
                prob = (count / valid_date_count) * 100
                safe_prob = safe_float(prob)
                hourly_high_prob[hour_labels[idx]] = round(safe_prob, 2) if safe_prob is not None else 0.0

            # ✅ 개선: 확률 합계 검증 (반올림 오차 감지)
            low_prob_sum = sum(hourly_low_prob.values())
            high_prob_sum = sum(hourly_high_prob.values())
            # 오차 확인 (반올림 오차 ±1% 허용)
            if abs(low_prob_sum - 100.0) > 1.0:
                logger.warning("[%s] 저점 확률 합계 이상: %.2f%% (기대: 100%%)", interval, low_prob_sum)
            if abs(high_prob_sum - 100.0) > 1.0:
                logger.warning("[%s] 고점 확률 합계 이상: %.2f%% (기대: 100%%)", interval, high_prob_sum)

            # 평균 변동성
            avg_volatility = safe_float(volatility_sum / volatility_count) if volatility_count > 0 else None
            if avg_volatility is not None:
                avg_volatility = round(avg_volatility, 2)

            # 저점 윈도우 찾기 (가장 많이 발생한 시간대 - 뉴욕시간 기준)
            max_low_count = max(low_hour_counts.values()) if low_hour_counts.values() else 0
            if max_low_count > 0:
                max_low_idx = max(low_hour_counts.items(), key=lambda x: x[1])[0]
                low_window_str = hour_labels[max_low_idx]
            else:
                low_window_str = None

            logger.info(
                "[%s] 시간대별 확률 계산 완료 (뉴욕시간 기준): total_dates=%s, valid_dates=%s, low_sum=%.2f%%, high_sum=%.2f%%",
                interval,
                total_dates,
                valid_date_count,
                low_prob_sum,
                high_prob_sum,
            )

            note_str = f"분석 대상 날짜: {total_dates}개 (유효: {valid_date_count}개) - 뉴욕시간(EST/EDT) 기준"
            if valid_date_count < total_dates:
                note_str += f" - 같은 4시간봉에 최저가/최고가가 발생한 {total_dates - valid_date_count}개 날짜 제외"

            return {
                "low_window": low_window_str,
                "avg_volatility": f"{avg_volatility}%" if avg_volatility else None,
                "hourly_low_probability": hourly_low_prob,
                "hourly_high_probability": hourly_high_prob,
                "note": note_str,
            }

        logger.warning("[%s] 시간대별 확률 계산 실패: total_dates=%s", interval, total_dates)
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": "분석할 날짜가 없습니다",
        }

    except Exception as exc:
        logger.error("시간대별 확률 계산 에러: %s", exc)
        logger.exception("Intraday distribution traceback")
        return {
            "low_window": None,
            "avg_volatility": None,
            "hourly_low_probability": {},
            "hourly_high_probability": {},
            "note": f"에러 발생: {str(exc)}",
        }


def calculate_weekly_distribution(
    df: pd.DataFrame,
    interval: str,
    timezone_offset: Optional[int] = None,
) -> Dict[str, Any]:
    """
    주봉 데이터에서 요일별 저점/고점 발생 확률 계산

    Args:
        df: 일봉 DataFrame (주봉 분석 시 일봉 데이터 사용)
        interval: 타임프레임
        timezone_offset: 하위 호환성용 파라미터 (사용되지 않음)

    Returns:
        {
            "daily_low_probability": {"Monday": 15.2, "Tuesday": 20.1, ...},
            "daily_high_probability": {"Monday": 18.5, "Tuesday": 22.3, ...},
            "note": "분석 정보"
        }
    """
    _ = interval
    _ = timezone_offset  # Backward compatibility parameter

    try:
        if df is None or df.empty:
            return {
                "daily_low_probability": {},
                "daily_high_probability": {},
                "note": "데이터 없음",
            }

        # 인덱스를 datetime으로 확보
        normalize_datetime_index = _get_normalize_datetime_index()
        if not isinstance(df.index, pd.DatetimeIndex):
            df = normalize_datetime_index(df)

        if not isinstance(df.index, pd.DatetimeIndex):
            return {
                "daily_low_probability": {},
                "daily_high_probability": {},
                "note": "DatetimeIndex 변환 실패",
            }

        # 주별로 그룹화하여 분석
        df_copy = df.copy()
        df_copy["week"] = df_copy.index.to_period("W")
        df_copy["weekday"] = df_copy.index.dayofweek  # 0=월요일, 6=일요일

        # 각 주에서 저점/고점이 발생한 요일 찾기
        low_day_counts = {i: 0 for i in range(7)}  # 월~일
        high_day_counts = {i: 0 for i in range(7)}
        valid_week_count = 0

        for _, week_df in df_copy.groupby("week"):
            if len(week_df) < 3:  # 최소 3일 이상의 데이터가 있는 주만 분석
                continue

            # 해당 주의 저점/고점 찾기
            low_idx = week_df["low"].idxmin()
            high_idx = week_df["high"].idxmax()

            if pd.isna(low_idx) or pd.isna(high_idx):
                continue

            low_weekday = week_df.loc[low_idx, "weekday"] if low_idx in week_df.index else None
            high_weekday = week_df.loc[high_idx, "weekday"] if high_idx in week_df.index else None

            if low_weekday is not None and high_weekday is not None:
                low_day_counts[low_weekday] += 1
                high_day_counts[high_weekday] += 1
                valid_week_count += 1

        # 확률 계산
        daily_low_prob = {}
        daily_high_prob = {}

        if valid_week_count > 0:
            for i in range(7):
                day_name = WEEKDAY_NAMES_EN[i]
                low_prob = safe_float(low_day_counts[i] / valid_week_count * 100)
                high_prob = safe_float(high_day_counts[i] / valid_week_count * 100)
                daily_low_prob[day_name] = round(low_prob, 1) if low_prob is not None else 0.0
                daily_high_prob[day_name] = round(high_prob, 1) if high_prob is not None else 0.0

            logger.info("[주봉] 요일별 확률 계산 완료: valid_weeks=%s", valid_week_count)

            return {
                "daily_low_probability": daily_low_prob,
                "daily_high_probability": daily_high_prob,
                "note": f"분석 대상 주: {valid_week_count}주",
            }

        return {
            "daily_low_probability": {},
            "daily_high_probability": {},
            "note": "분석할 주간 데이터 없음",
        }

    except Exception as exc:
        logger.error("요일별 확률 계산 에러: %s", exc)
        logger.exception("Weekly distribution traceback")
        return {
            "daily_low_probability": {},
            "daily_high_probability": {},
            "note": f"에러 발생: {str(exc)}",
        }
