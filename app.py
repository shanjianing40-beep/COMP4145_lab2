import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from trading_strategy import (
    calculate_moving_averages,
    get_stock_data,
    identify_golden_cross,
    implement_strategy,
)

STOCKS = {
    "Microsoft (MSFT)": "MSFT",
    "Apple (AAPL)": "AAPL",
    "NVIDIA (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Meta (META)": "META",
    "Advanced Micro Devices (AMD)": "AMD",
    "Adobe (ADBE)": "ADBE",
    "Berkshire Hathaway (BRK-B)": "BRK-B",
    "Broadcom (AVGO)": "AVGO",
    "Cisco (CSCO)": "CSCO",
    "Coca-Cola (KO)": "KO",
    "Costco (COST)": "COST",
    "Eli Lilly (LLY)": "LLY",
    "JPMorgan Chase (JPM)": "JPM",
    "Netflix (NFLX)": "NFLX",
    "Oracle (ORCL)": "ORCL",
    "Palantir (PLTR)": "PLTR",
    "Salesforce (CRM)": "CRM",
    "Shopify (SHOP)": "SHOP",
    "Taiwan Semiconductor (TSM)": "TSM",
    "Visa (V)": "V",
    "Walmart (WMT)": "WMT",
}


@st.cache_data(ttl=900)
def load_strategy_results(ticker):
    data = get_stock_data(ticker)
    if data.empty:
        return data, pd.DataFrame()

    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


def show_price_chart(ticker, data, positions):
    st.subheader(f"{ticker} price and moving averages")
    st.caption("Five years of daily closing prices with 50-day and 200-day moving averages.")

    figure, axis = plt.subplots(figsize=(13, 6))
    axis.plot(data.index, data["Close"], label="Closing price", color="#2563eb", linewidth=1.5)
    axis.plot(data.index, data["MA50"], label="50-day MA", color="#f59e0b", linewidth=1.2)
    axis.plot(data.index, data["MA200"], label="200-day MA", color="#8b5cf6", linewidth=1.2)

    if not positions.empty:
        axis.scatter(
            positions["BuyDate"],
            positions["BuyPrice"],
            label="Buy",
            color="#16a34a",
            marker="^",
            s=75,
            zorder=3,
        )
        completed_sales = positions.dropna(subset=["SellPrice"])
        if not completed_sales.empty:
            axis.scatter(
                completed_sales["SellDate"],
                completed_sales["SellPrice"],
                label="Sell",
                color="#dc2626",
                marker="v",
                s=75,
                zorder=3,
            )

    axis.set_ylabel("Price (USD)")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best")
    figure.tight_layout()
    st.pyplot(figure, width="stretch")
    plt.close(figure)
    st.caption("A sell marker is shown only when a sell price is available.")


def show_statistics(positions):
    st.subheader("Overall trade statistics")

    if positions.empty:
        st.info("No trading signals were detected for this period.")
        return

    resolved = positions.dropna(subset=["ProfitPct"])
    wins = int((resolved["ProfitPct"] > 0).sum())
    losses = int((resolved["ProfitPct"] <= 0).sum())
    unresolved = len(positions) - len(resolved)
    win_rate = wins / len(resolved) * 100 if not resolved.empty else 0
    average_profit = resolved["ProfitPct"].mean() if not resolved.empty else 0
    average_holding = positions["HoldingDays"].mean()

    first_row = st.columns(3)
    first_row[0].metric("Total trades", len(positions))
    first_row[1].metric("Winning trades", wins)
    first_row[2].metric("Losing trades", losses)

    second_row = st.columns(3)
    second_row[0].metric("Win rate (priced trades)", f"{win_rate:.2f}%")
    second_row[1].metric("Average profit (priced trades)", f"{average_profit:.2f}%")
    second_row[2].metric("Average holding period", f"{average_holding:.1f} days")

    if unresolved:
        st.info(
            f"{unresolved} trade(s) do not have a sell price yet and are excluded "
            "from win rate and average profit."
        )


def show_trade_details(positions):
    st.subheader("Detailed trade records")

    if positions.empty:
        st.info("No trading signals were detected for this period.")
        return

    display = positions.copy()
    for date_column in ("BuyDate", "SellDate"):
        display[date_column] = pd.to_datetime(display[date_column]).dt.strftime("%Y-%m-%d")

    display = display.rename(
        columns={
            "BuyDate": "Buy date",
            "BuyPrice": "Buy price (USD)",
            "SellDate": "Sell date",
            "SellPrice": "Sell price (USD)",
            "HoldingDays": "Holding days",
            "ProfitPct": "Profit (%)",
            "SellReason": "Sell reason",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)


def main():
    st.set_page_config(page_title="Golden Cross Backtest", page_icon="📈", layout="wide")
    st.sidebar.header("Stock selection")
    selected_stock = st.sidebar.selectbox("Choose a stock", options=STOCKS.keys())
    ticker = STOCKS[selected_stock]

    st.title(f"{ticker} Golden Cross Backtest")
    st.caption("Historical strategy results are for analysis only and are not investment advice.")

    with st.spinner(f"Loading {ticker} historical data and calculating trades..."):
        data, positions = load_strategy_results(ticker)

    if data.empty:
        st.error(f"No historical data was returned for ticker '{ticker}'. Check the symbol and try again.")
        return

    page = st.radio(
        "View",
        ("Price chart", "Trade statistics", "Detailed trades"),
        horizontal=True,
    )

    if page == "Price chart":
        show_price_chart(ticker, data, positions)
    elif page == "Trade statistics":
        show_statistics(positions)
    else:
        show_trade_details(positions)


if __name__ == "__main__":
    main()
