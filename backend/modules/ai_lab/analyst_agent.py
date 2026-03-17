"""Tool-using analyst agent flow for AI lab."""

from __future__ import annotations

from typing import Any, Callable, Dict


def run_data_analyst_agent(
    *,
    api_key: str,
    coin: str,
    interval: str,
    user_prompt: str,
    model: str,
    build_llm_client_fn: Callable[..., Any],
    execute_pandas_code_fn: Callable[..., Any],
) -> Dict[str, Any]:
    """Run the analyst-agent workflow with injected dependencies."""
    llm = build_llm_client_fn("gemini", api_key=api_key, model=model)

    system_prompt = f"""
    You are an expert Crypto Quant Data Analyst.
    You have access to a tool called `execute_pandas_code`.
    This tool allows you to run Python pandas code on the latest market data for {coin} ({interval}).

    The data is already loaded into a pandas DataFrame named `df`.
    The `df` has columns: ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']

    CRITICAL RULES FOR USING THE TOOL:
    1. You MUST assign your final answer to a variable named `result`.
    2. Do NOT use print() to return the final answer, use the `result` variable.
    3. You can use `pd` (pandas) and `np` (numpy).

    If the user asks a question that requires data analysis, write the python code, use the tool, and then explain the result to the user.
    """

    tools = [
        {
            "function_declarations": [
                {
                    "name": "execute_pandas_code",
                    "description": "Executes python pandas code on the market data dataframe 'df' and returns the string representation of the 'result' variable.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "code": {
                                "type": "STRING",
                                "description": "The python code to execute. Must assign the final output to a variable named 'result'.",
                            }
                        },
                        "required": ["code"],
                    },
                }
            ]
        }
    ]

    response = llm.generate(system_prompt=system_prompt, prompt=user_prompt, tools=tools)

    if response.get("error"):
        return {
            "success": False,
            "answer": "",
            "error": str(response["error"]),
            "execution_path": "llm_initial_error",
        }

    function_call = response.get("function_call")
    if function_call and function_call.get("name") == "execute_pandas_code":
        args = function_call.get("args", {})
        code = args.get("code", "")

        tool_result = execute_pandas_code_fn(coin, interval, code)
        if isinstance(tool_result, dict) and not tool_result.get("success"):
            return {
                "success": False,
                "answer": "",
                "error": tool_result.get("error", "Unknown error"),
                "execution_path": "tool_execution_error",
            }

        history = [
            {"role": "user", "content": user_prompt},
            {"role": "model", "content": f"I will run this code:\n```python\n{code}\n```"},
        ]
        follow_up_prompt = (
            f"The tool returned this result:\n{tool_result}\n\nPlease explain this result to the user."
        )

        final_response = llm.generate(
            system_prompt=system_prompt,
            prompt=follow_up_prompt,
            history=history,
        )
        if final_response.get("error"):
            return {
                "success": False,
                "answer": "",
                "error": str(final_response["error"]),
                "execution_path": "llm_followup_error",
            }

        final_text = str(final_response.get("text") or "").strip()
        if not final_text:
            return {
                "success": False,
                "answer": "",
                "error": "LLM returned empty analysis response.",
                "execution_path": "llm_followup_empty",
            }

        return {
            "success": True,
            "answer": final_text,
            "error": None,
            "execution_path": "tool_then_llm",
        }

    text = str(response.get("text") or "").strip()
    if text:
        return {
            "success": True,
            "answer": text,
            "error": None,
            "execution_path": "llm_text",
        }
    return {
        "success": False,
        "answer": "",
        "error": "No response generated.",
        "execution_path": "llm_empty",
    }
