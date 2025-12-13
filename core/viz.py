import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def plot_trades_on_chart(df: pd.DataFrame, trades: pd.DataFrame, strategy_name: str = "") -> go.Figure:
    """
    캔들 차트 + 진입/청산 마커 그리기
    - df : 전체 OHLC 데이터
    - trades : run_backtest() 결과 데이터프레임
    """

    if trades is None or trades.empty or df is None or df.empty:
        # 데이터 없으면 빈 Figure
        fig = go.Figure()
        fig.update_layout(
            title="No trades to display",
            template="plotly_dark",
            xaxis_rangeslider_visible=True,
            height=500,
        )
        return fig

    # 최근 구간 위주로 (성능 때문에 300개 정도만)
    last_time = trades["Entry Time"].max()
    mask = df["open_dt"] <= last_time
    if mask.any():
        end_idx = df[mask].index[-1]
    else:
        end_idx = len(df) - 1
    start_idx = max(0, end_idx - 300)
    plot_df = df.iloc[start_idx : end_idx + 1].copy()

    fig = go.Figure()

    # 1) 캔들 차트
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
        )
    )

    # 2) EMA 200 같이 장기 추세선 있으면 같이 그림
    if "EMA_200" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["open_dt"],
                y=plot_df["EMA_200"],
                name="EMA 200",
                line=dict(color="orange", width=1),
            )
        )

    # 3) 진입/청산 마커
    #   - Entry : 노란 삼각형
    #   - 이익 청산 : 초록 동그라미
    #   - 손절/청산 : 빨간 X
    inside = trades[trades["Entry Time"].isin(plot_df["open_dt"])].copy()

    if not inside.empty:
        # Entry
        fig.add_trace(
            go.Scatter(
                x=inside["Entry Time"],
                y=inside["Entry Price"],
                mode="markers",
                marker=dict(symbol="triangle-up", color="yellow", size=10),
                name="Entry",
            )
        )

        # Win / Loss 나누기
        wins = inside[inside["PnL"] > 0]
        losses = inside[inside["PnL"] <= 0]

        if not wins.empty:
            fig.add_trace(
                go.Scatter(
                    x=wins["Exit Time"],
                    y=wins["Exit Price"],
                    mode="markers",
                    marker=dict(symbol="circle", color="#00e676", size=8),
                    name="Exit Win",
                )
            )

        if not losses.empty:
            fig.add_trace(
                go.Scatter(
                    x=losses["Exit Time"],
                    y=losses["Exit Price"],
                    mode="markers",
                    marker=dict(symbol="x", color="#ff1744", size=8),
                    name="Exit Loss",
                )
            )

    fig.update_layout(
        title=f"{strategy_name} Trades" if strategy_name else "Trades",
        template="plotly_dark",
        height=550,
        xaxis_rangeslider_visible=True,  # 👈 확대/축소용 슬라이더 ON
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
        ),
    )

    return fig


def plot_equity_curve(trades: pd.DataFrame, title: str = "Equity Curve") -> go.Figure:
    """
    누적 수익(복리) 곡선 그리기
    - 초기자본 100 기준
    """

    fig = go.Figure()

    if trades is None or trades.empty:
        fig.update_layout(
            title="No trades to display",
            template="plotly_dark",
            height=400,
        )
        return fig

    equity = (1 + trades["PnL"]).cumprod() * 100

    fig = px.line(
        x=trades["Entry Time"],
        y=equity,
        labels={"x": "Time", "y": "Equity (Start = 100)"},
        title=title,
    )
    fig.update_traces(line_color="#00CC96")
    fig.update_layout(template="plotly_dark", height=400)

    return fig

