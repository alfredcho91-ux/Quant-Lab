import ast
import multiprocessing as mp
import os
import sys
import traceback
from io import StringIO
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from utils.data_service import fetch_live_data


def _read_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


EXEC_TIMEOUT_SECONDS = _read_float_env("AI_ANALYST_EXEC_TIMEOUT_SECONDS", 6.0)
MAX_RESULT_CHARS = _read_int_env("AI_ANALYST_MAX_RESULT_CHARS", 12_000)

BLOCKED_CALL_NAMES = {
    "__import__",
    "open",
    "eval",
    "exec",
    "compile",
    "input",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "breakpoint",
}
BLOCKED_NAME_REFERENCES = {"os", "sys", "subprocess", "pathlib", "socket", "shutil"}
FORBIDDEN_NODE_TYPES = (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal)


def _validate_user_code(code: str) -> Optional[str]:
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        return f"Invalid Python syntax: {exc.msg}"

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODE_TYPES):
            return "Unsupported statement in analyst sandbox."
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "Dunder attribute access is blocked in analyst sandbox."
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAME_REFERENCES:
            return f"Reference '{node.id}' is not allowed in analyst sandbox."
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALL_NAMES:
                return f"Call '{node.func.id}(...)' is not allowed in analyst sandbox."

    return None


def _truncate_output(text: str) -> str:
    if len(text) <= MAX_RESULT_CHARS:
        return text
    return f"{text[:MAX_RESULT_CHARS]}\n\n... (truncated)"


def _execute_in_worker(queue: Any, coin: str, interval: str, code: str) -> None:
    try:
        symbol = coin if coin.endswith("USDT") else f"{coin}USDT"
        df = fetch_live_data(symbol, interval, limit=1000, total_candles=1000)
        if df is None or df.empty:
            queue.put({"ok": False, "output": f"Error: Could not load data for {symbol} {interval}"})
            return

        safe_builtins = {
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "bool": bool,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "any": any,
            "all": all,
            "Exception": Exception,
        }
        local_env: Dict[str, Any] = {
            "pd": pd,
            "np": np,
            "df": df,
        }

        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        try:
            compiled = compile(code, "<ai_analyst_sandbox>", "exec")
            exec(compiled, {"__builtins__": safe_builtins}, local_env)
        finally:
            sys.stdout = old_stdout

        if "result" in local_env:
            output = local_env["result"]
            if isinstance(output, (pd.DataFrame, pd.Series)):
                queue.put({"ok": True, "output": output.to_string()})
            else:
                queue.put({"ok": True, "output": str(output)})
            return

        printed = redirected_output.getvalue().strip()
        if printed:
            queue.put(
                {
                    "ok": True,
                    "output": (
                        "Code executed successfully, but 'result' variable was not set. "
                        f"Printed output:\n{printed}"
                    ),
                }
            )
            return

        queue.put(
            {
                "ok": False,
                "output": "Error: Code executed, but did not assign any value to 'result'.",
            }
        )
    except Exception:
        queue.put(
            {
                "ok": False,
                "output": f"Execution Error:\n{traceback.format_exc(limit=5)}",
            }
        )


def execute_pandas_code(coin: str, interval: str, code: str) -> str:
    """
    Execute analyst code in a separate sandbox process with timeout/AST guards.
    """
    source = (code or "").strip()
    if not source:
        return "Error: Empty code."

    validation_error = _validate_user_code(source)
    if validation_error:
        return f"Error: {validation_error}"

    ctx = mp.get_context("spawn")
    queue = ctx.Queue(maxsize=1)
    process = ctx.Process(
        target=_execute_in_worker,
        args=(queue, coin, interval, source),
        daemon=True,
    )
    process.start()
    process.join(timeout=10)

    if process.is_alive():
        process.terminate()
        process.join(1.0)
        return {"success": False, "error": "Timeout"}

    if queue.empty():
        return "Error: Code execution failed without output."

    payload = queue.get()
    output = str(payload.get("output") or "").strip()
    if not output:
        output = "Error: Code execution produced no output."
    return _truncate_output(output)
