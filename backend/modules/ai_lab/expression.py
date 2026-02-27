"""AST and Pandas evaluation functions for AI lab expressions."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .parser import _normalize_expression_text


def _resolve_indicator_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _apply_comparator(series: pd.Series, operator: str, threshold: float) -> pd.Series:
    if operator == ">":
        return series > threshold
    if operator == ">=":
        return series >= threshold
    if operator == "<":
        return series < threshold
    if operator == "<=":
        return series <= threshold
    return series == threshold


def _coerce_mask(mask: pd.Series) -> pd.Series:
    return mask.fillna(False).astype(bool)


def _sorted_condition_specs(condition_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _key(spec: Dict[str, Any]) -> tuple[int, int]:
        span = spec.get("span")
        if isinstance(span, tuple) and len(span) == 2:
            return int(span[0]), int(span[1])
        order = int(spec.get("order", 0))
        return 10**9 + order, 10**9 + order

    return sorted(condition_specs, key=_key)


def _build_expression_tokens(prompt: str, condition_specs: List[Dict[str, Any]]) -> tuple[List[str], Dict[str, Dict[str, Any]]]:
    if not condition_specs:
        return [], {}

    ordered_specs = _sorted_condition_specs(condition_specs)
    token_map: Dict[str, Dict[str, Any]] = {}
    for idx, spec in enumerate(ordered_specs, start=1):
        token = f"C{idx}"
        spec["token"] = token
        token_map[token] = spec

    replaced = prompt
    span_specs = [spec for spec in ordered_specs if isinstance(spec.get("span"), tuple)]
    span_specs.sort(key=lambda item: item["span"][0], reverse=True)
    for spec in span_specs:
        start, end = spec["span"]
        if start < 0 or end <= start or end > len(replaced):
            continue
        replaced = replaced[:start] + f" {spec['token']} " + replaced[end:]

    normalized = _normalize_expression_text(replaced).upper()
    tokens = re.findall(r"C\d+|AND|OR|NOT|\(|\)", normalized)

    existing_tokens = set(tokens)
    for spec in ordered_specs:
        token = spec["token"]
        if token not in existing_tokens:
            if tokens:
                tokens.extend(["AND", token])
            else:
                tokens.append(token)
            existing_tokens.add(token)

    return tokens, token_map


def _insert_implicit_and(tokens: List[str]) -> List[str]:
    if not tokens:
        return []

    def _is_operand(tok: str) -> bool:
        return tok.startswith("C")

    output: List[str] = []
    prev: Optional[str] = None
    for tok in tokens:
        if prev is not None:
            if (_is_operand(prev) or prev == ")") and (_is_operand(tok) or tok in {"(", "NOT"}):
                output.append("AND")
        output.append(tok)
        prev = tok
    return output


def _infix_to_postfix(tokens: List[str]) -> List[str]:
    precedence = {"OR": 1, "AND": 2, "NOT": 3}
    right_assoc = {"NOT"}
    output: List[str] = []
    stack: List[str] = []

    for tok in tokens:
        if tok.startswith("C"):
            output.append(tok)
            continue
        if tok in {"AND", "OR", "NOT"}:
            while stack and stack[-1] in precedence:
                top = stack[-1]
                if (tok in right_assoc and precedence[tok] < precedence[top]) or (
                    tok not in right_assoc and precedence[tok] <= precedence[top]
                ):
                    output.append(stack.pop())
                else:
                    break
            stack.append(tok)
            continue
        if tok == "(":
            stack.append(tok)
            continue
        if tok == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()
            continue

    while stack:
        top = stack.pop()
        if top in {"(", ")"}:
            raise ValueError("Mismatched parentheses")
        output.append(top)
    return output


def _eval_postfix_mask(postfix: List[str], token_map: Dict[str, Dict[str, Any]], index: pd.Index) -> pd.Series:
    stack: List[pd.Series] = []
    for tok in postfix:
        if tok.startswith("C"):
            spec = token_map.get(tok)
            if spec is None:
                raise ValueError(f"Unknown token: {tok}")
            stack.append(_coerce_mask(spec["mask"]))
            continue

        if tok == "NOT":
            if not stack:
                raise ValueError("Invalid NOT expression")
            val = stack.pop()
            stack.append(_coerce_mask(~val))
            continue

        if tok in {"AND", "OR"}:
            if len(stack) < 2:
                raise ValueError(f"Invalid binary expression for {tok}")
            right = _coerce_mask(stack.pop())
            left = _coerce_mask(stack.pop())
            merged = left & right if tok == "AND" else left | right
            stack.append(_coerce_mask(merged))
            continue

    if len(stack) != 1:
        raise ValueError("Invalid expression stack state")
    final_mask = _coerce_mask(stack[0])
    if not final_mask.index.equals(index):
        final_mask = final_mask.reindex(index, fill_value=False)
    return final_mask


def _format_expression_tokens(tokens: List[str], token_map: Dict[str, Dict[str, Any]]) -> str:
    parts: List[str] = []
    for tok in tokens:
        if tok in {"AND", "OR", "NOT", "(", ")"}:
            parts.append(tok)
            continue
        spec = token_map.get(tok)
        parts.append(spec["label"] if spec else tok)
    return " ".join(parts).strip()


def _evaluate_condition_expression(
    prompt: str,
    condition_specs: List[Dict[str, Any]],
    index: pd.Index,
) -> tuple[pd.Series, List[str], str]:
    if not condition_specs:
        return pd.Series(True, index=index), [], "조건 없음(전체 구간)"

    raw_tokens, token_map = _build_expression_tokens(prompt, condition_specs)
    infix_tokens = _insert_implicit_and(raw_tokens)
    try:
        postfix = _infix_to_postfix(infix_tokens)
        mask = _eval_postfix_mask(postfix, token_map, index)
    except Exception:
        mask = pd.Series(True, index=index)
        infix_tokens = []
        for spec in _sorted_condition_specs(condition_specs):
            mask &= _coerce_mask(spec["mask"])
            if infix_tokens:
                infix_tokens.append("AND")
            token = spec.get("token")
            if not token:
                token = f"C{len(infix_tokens) + 1}"
            infix_tokens.append(token)
            token_map[token] = spec
        mask = _coerce_mask(mask)

    condition_text = _format_expression_tokens(infix_tokens, token_map)
    return mask, infix_tokens, condition_text
