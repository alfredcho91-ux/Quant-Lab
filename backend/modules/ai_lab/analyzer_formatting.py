"""Presentation helpers for AI lab conditional probability analysis."""

from __future__ import annotations

import re
from typing import List, Optional

from .stats_math import _p_value_reliability_label


def _format_probability_answer(
    *,
    coin: str,
    interval: str,
    source: str,
    target_side: str,
    condition_text: str,
    sample_count: int,
    success_count: int,
    probability_rate: Optional[float],
    ci_lower: Optional[float],
    ci_upper: Optional[float],
    p_value: Optional[float],
    reliability: str,
    gati_index: float,
    is_ko: bool,
) -> str:
    if sample_count == 0 or probability_rate is None:
        if is_ko:
            return f"분석 결과, {coin} {interval} 차트에서 '{condition_text}' 조건을 만족하는 과거 데이터가 없어 확률을 계산할 수 없습니다."
        return f"Based on the analysis, there is no historical data matching the condition '{condition_text}' on the {coin} {interval} chart, so the probability cannot be calculated."

    target_label_ko = "상승(양봉)" if target_side == "bull" else "하락(음봉)"
    probability_label_ko = "다음 봉 양봉 확률" if target_side == "bull" else "다음 봉 음봉 확률"
    target_label_en = "Green (Bull)" if target_side == "bull" else "Red (Bear)"

    ci_text = f"{ci_lower:.2f}% ~ {ci_upper:.2f}%" if ci_lower is not None and ci_upper is not None else "N/A"
    p_text = f"{p_value:.4f}" if p_value is not None else "N/A"
    p_reliability = _p_value_reliability_label(p_value)

    if is_ko:
        return (
            f"📊 **조건부 확률 분석 결과**\n\n"
            f"{coin} {interval} 차트에서 **{condition_text}** 조건이 발생했을 때, "
            f"**{probability_label_ko}**은 **{probability_rate:.2f}%** 입니다.\n"
            f"(다음 봉이 **{target_label_ko}**으로 마감될 확률)\n\n"
            f"• **분석 표본**: 총 {sample_count}번의 사례 중 {success_count}번 적중\n"
            f"• **통계적 신뢰도**: {p_reliability} (p-value: {p_text})\n"
            f"• **GATI 지수**: {gati_index:.2f} / 100\n"
            f"• **95% 신뢰구간**: {ci_text}"
        )

    return (
        f"📊 **Conditional Probability Analysis**\n\n"
        f"On the {coin} {interval} chart, when the condition **{condition_text}** is met, "
        f"the probability of the next candle being **{target_label_en}** is **{probability_rate:.2f}%**.\n\n"
        f"• **Sample Size**: Hit {success_count} out of {sample_count} historical cases\n"
        f"• **Statistical Reliability**: {p_reliability} (p-value: {p_text})\n"
        f"• **GATI Index**: {gati_index:.2f} / 100\n"
        f"• **95% Confidence Interval**: {ci_text}"
    )


def _append_ignored_conditions_note(answer: str, prompt: str, ignored_conditions: List[str]) -> str:
    unique_conditions = [item for item in dict.fromkeys(ignored_conditions) if item]
    if not unique_conditions:
        return answer

    detail = ", ".join(unique_conditions)
    if re.search(r"[가-힣]", prompt or ""):
        return f"{answer}\n주의: 일부 조건은 파싱/데이터 한계로 제외됨 -> {detail}"
    return f"{answer}\nNote: Some conditions were excluded due to parsing/data limits -> {detail}"


__all__ = [
    "_append_ignored_conditions_note",
    "_format_probability_answer",
]
