# core/charts.py
from typing import Optional
import logging
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

def plot_price_with_indicators(
    df: pd.DataFrame,
    trades: Optional[pd.DataFrame],
    title: str,
    full_span: bool = False,
    sr_levels: Optional[pd.DataFrame] = None,
    show_bb: bool = True,
):
    """
    full_span=True  → 전체 df 그대로(자르지 않음, rangeslider 켜짐)
    full_span=False → 최근 일부만 표시
    """
    if full_span:
        plot_df = df.copy()
    else:
        if trades is None or trades.empty:
            plot_df = df.tail(400).copy()
        else:
            first = trades["Entry Time"].min()
            try:
                i0 = df.index[df["open_dt"] == first][0]
                start = max(0, i0 - 80)
            except IndexError:
                start = max(0, len(df) - 480)
            plot_df = df.iloc[start:].copy()
            if len(plot_df) > 800:
                plot_df = plot_df.tail(800)

    rsi_ob = df.attrs.get("RSI_OB", 70)
    rsi_os = df.attrs.get("RSI_OS", 30)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.68, 0.32],
        vertical_spacing=0.05,
        subplot_titles=(title, f"RSI(14): OB={rsi_ob} / OS={rsi_os}"),
    )

    # 캔들
    fig.add_trace(
        go.Candlestick(
            x=plot_df["open_dt"],
            open=plot_df["open"],
            high=plot_df["high"],
            low=plot_df["low"],
            close=plot_df["close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1,
        col=1,
    )

    # Main SMA + MA들
    if "SMA_main" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["SMA_main"],
                name=f"SMA {df.attrs.get('SMA_MAIN_LEN', 200)}",
                line=dict(color="yellow", width=1.2),
            ),
            row=1,
            col=1,
        )
    if "SMA_1" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["SMA_1"],
                name=f"MA {df.attrs.get('SMA1_LEN', 20)}",
                line=dict(color="deepskyblue", width=1),
            ),
            row=1,
            col=1,
        )
    if "SMA_2" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["SMA_2"],
                name=f"MA {df.attrs.get('SMA2_LEN', 60)}",
                line=dict(color="orange", width=1),
            ),
            row=1,
            col=1,
        )
    if "SMA_3" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["SMA_3"],
                name=f"MA {df.attrs.get('SMA3_LEN', 120)}",
                line=dict(color="violet", width=1),
            ),
            row=1,
            col=1,
        )

    # 🔹 볼린저 밴드: show_bb 가 True 일 때만 그리기
    if show_bb and "BB_Up" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["BB_Up"],
                name="BB Up",
                line=dict(color="gray", dash="dot"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["BB_Low"],
                name="BB Low",
                line=dict(color="gray", dash="dot"),
            ),
            row=1,
            col=1,
        )

    # RSI
    if "RSI" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["RSI"],
                name="RSI(14)",
                line=dict(color="#9fa8da"),
            ),
            row=2,
            col=1,
        )
        fig.add_hline(y=rsi_ob, line=dict(color="red", dash="dot"), row=2, col=1)
        fig.add_hline(y=rsi_os, line=dict(color="green", dash="dot"), row=2, col=1)

    # 매매 마커
    if (not full_span) and (trades is not None) and (not trades.empty):
        inside = trades[trades["Entry Time"].isin(plot_df["open_dt"])]
        if not inside.empty:
            long_e = inside[inside["Direction"] == "Long"]
            short_e = inside[inside["Direction"] == "Short"]
            if not long_e.empty:
                fig.add_trace(
                    go.Scatter(
                        x=long_e["Entry Time"],
                        y=long_e["Entry Price"],
                        mode="markers",
                        marker=dict(
                            symbol="triangle-up", color="deepskyblue", size=12
                        ),
                        name="Long Entry",
                    ),
                    row=1,
                    col=1,
                )
            if not short_e.empty:
                fig.add_trace(
                    go.Scatter(
                        x=short_e["Entry Time"],
                        y=short_e["Entry Price"],
                        mode="markers",
                        marker=dict(
                            symbol="triangle-down", color="violet", size=12
                        ),
                        name="Short Entry",
                    ),
                    row=1,
                    col=1,
                )

            wins = inside[inside["PnL"] > 0]
            loss = inside[inside["PnL"] <= 0]
            if not wins.empty:
                fig.add_trace(
                    go.Scatter(
                        x=wins["Exit Time"],
                        y=wins["Exit Price"],
                        mode="markers",
                        marker=dict(
                            symbol="diamond", color="#00e676", size=9
                        ),
                        name="Exit (Win)",
                    ),
                    row=1,
                    col=1,
                )
            if not loss.empty:
                fig.add_trace(
                    go.Scatter(
                        x=loss["Exit Time"],
                        y=loss["Exit Price"],
                        mode="markers",
                        marker=dict(symbol="x", color="#ff1744", size=9),
                        name="Exit (Loss)",
                    ),
                    row=1,
                    col=1,
                )

    # ───────── 지지/저항 / 피벗 수평선 ─────────
    if sr_levels is not None and not sr_levels.empty:
        tmp = sr_levels.copy()
        if "touches" in tmp.columns:
            tmp = tmp.sort_values("touches", ascending=False).head(20)
        for _, lvl in tmp.iterrows():
            y = float(lvl["price"])
            kind = str(lvl.get("kind", "level"))
            source = str(lvl.get("source", "swing"))
            label = str(lvl.get("label", "")) if "label" in lvl else ""
            tf = str(lvl.get("timeframe", ""))

            if kind == "support":
                color = "#4caf50"
            elif kind == "resistance":
                color = "#ef5350"
            elif kind == "pivot":
                color = "#ffb300"
            else:
                color = "#90a4ae"

            dash = "dot" if source == "swing" else "dash"
            fig.add_hline(
                y=y,
                line=dict(color=color, dash=dash, width=1),
                row=1,
                col=1,
            )

            if label or tf:
                fig.add_annotation(
                    x=plot_df["open_dt"].iloc[-1],
                    y=y,
                    xanchor="left",
                    text=f"{label or kind} {tf}",
                    showarrow=False,
                    font=dict(size=9, color=color),
                    align="left",
                    row=1,
                    col=1,
                )

    # ───────── 차트 우측 상단 인디케이터 미니 패널 ─────────
    try:
        last = df.iloc[-1]
        info_lines = []

        # 가격
        if "close" in df.columns:
            info_lines.append(f"Close: {last['close']:.2f}")

        # RSI(14)
        if "RSI" in df.columns:
            rsi_ob_attr = df.attrs.get("RSI_OB", 70)
            rsi_os_attr = df.attrs.get("RSI_OS", 100 - rsi_ob_attr)
            info_lines.append(
                f"RSI(14): {last['RSI']:.1f} (OB {rsi_ob_attr} / OS {int(rsi_os_attr)})"
            )

        # ADX
        if "ADX" in df.columns:
            info_lines.append(f"ADX: {last['ADX']:.1f}")

        # Regime
        if "Regime" in df.columns:
            info_lines.append(f"Regime: {last['Regime']}")

        # MACD
        if "MACD" in df.columns and "MACD_signal" in df.columns:
            info_lines.append(
                f"MACD: {last['MACD']:.1f} / Sig: {last['MACD_signal']:.1f}"
            )

        if info_lines:
            fig.add_annotation(
                xref="paper",
                yref="paper",
                x=0.99,
                y=0.98,
                xanchor="right",
                yanchor="top",
                showarrow=False,
                align="right",
                text="<br>".join(info_lines),
                font=dict(size=9, color="#BBBBBB"),
                bgcolor="rgba(0,0,0,0.4)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=0.5,
                borderpad=3,
            )
    except Exception as exc:
        logger.debug("Failed to render chart info annotation: %s", exc, exc_info=True)

    fig.update_layout(
        template="plotly_dark",
        dragmode="pan",
        height=760,
        xaxis_rangeslider_visible=bool(full_span),
        hovermode="x unified",
    )
    return fig
