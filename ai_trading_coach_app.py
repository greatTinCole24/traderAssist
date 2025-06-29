import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
from datetime import date
from openai import OpenAI

# --- PAGE SETUP ---
st.set_page_config(page_title="Trading Flashcards, Candlestick Quiz & Journal Analysis", layout="wide")
st.title("🎴 Trading Flashcards & Candlestick Quiz & Quant Journal")

# --- Flashcards Data ---
flashcards = [
    {"term": "Doji", "definition": "A candle where open and close are almost the same, indicating market indecision."},
    {"term": "Bullish Engulfing", "definition": "A small bearish candle followed by a larger bullish candle that engulfs it, signaling potential reversal."},
    {"term": "Bearish Engulfing", "definition": "A small bullish candle followed by a larger bearish candle that engulfs it, signaling potential reversal."},
    {"term": "Hammer", "definition": "A candle with a small body and long lower wick, indicating rejection of lower prices."},
    {"term": "Shooting Star", "definition": "A candle with a small body and long upper wick, indicating rejection of higher prices."},
]

# --- Synthetic Pattern Data for Quiz ---
def make_pattern_df(pattern):
    # ... same as before ...
    return df

# --- Tabs Setup ---
tab1, tab2, tab3 = st.tabs(["📚 Flashcards", "🧐 Candlestick Quiz", "📒 Journal & Quant Analysis"])

# --- Tab 1: Flashcards ---
# ... same as before ...

# --- Tab 2: Candlestick Quiz ---
# ... same as before ...

# --- Tab 3: Journal & Quant Analysis ---
with tab3:
    st.subheader("📒 Upload Your Trades CSV for Quant Analysis")
    # Example data for demonstration
    example_dates = pd.date_range(end=date.today(), periods=7, freq='B')
    tickers = ['SPY','NVDA','TSLA']
    example_trades = pd.DataFrame({
        'Ticker': [random.choice(tickers) for _ in range(25)],
        'Date': [random.choice(example_dates).strftime('%Y-%m-%d') for _ in range(25)],
        'Entry Price': [round(random.uniform(100, 500),2) for _ in range(25)],
        'Exit Price': [round(random.uniform(100, 500),2) for _ in range(25)],
        'PnL': [round(random.uniform(-10,10),2) for _ in range(25)],
        'Volume': [random.randint(1,100) for _ in range(25)],
        'Trade Duration': [random.randint(1,120) for _ in range(25)]
    })
    show_example = st.checkbox("Use example data (25 trades over 7 days)")
    uploaded = st.file_uploader("Upload CSV with columns: Ticker, Date, Entry Price, Exit Price, PnL, Volume, Trade Duration", type=["csv"])
    if uploaded:
        trades = pd.read_csv(uploaded)
    elif show_example:
        trades = example_trades.copy()
        st.markdown("**Using Example Trade Data:**")
    else:
        trades = None("Upload CSV with columns: Ticker, Date, Entry Price, Exit Price, PnL, Volume, Trade Duration", type=["csv"])
    if uploaded:
        trades = pd.read_csv(uploaded)
        st.dataframe(trades)
        if 'PnL' in trades.columns:
            total_pnl = trades['PnL'].sum()
            win_rate = (trades['PnL'] > 0).mean() * 100
            avg_holding = trades['Trade Duration'].mean() if 'Trade Duration' in trades.columns else None
            st.metric("Total PnL", f"${total_pnl:.2f}")
            st.metric("Win Rate", f"{win_rate:.2f}%")
            if avg_holding:
                st.metric("Avg Hold (min)", f"{avg_holding:.1f}")
            fig_pnl = px.histogram(trades, x="PnL", nbins=20, title="PnL Distribution")
            st.plotly_chart(fig_pnl, use_container_width=True)
        else:
            st.warning("Ensure your CSV has a 'PnL' column.")

        # Quantitative Entry/Exit Analysis Prompt
        if all(col in trades.columns for col in ['Entry Price','Exit Price','PnL']):
            st.subheader("📝 Quant Entry/Exit Analysis")
            trades_json = trades.to_dict(orient='records')
            prompt = (
                "You are a quantitative trading expert with a PhD in financial engineering. "
                "Given these trade records: {trades_json}, provide a detailed analysis of entry timing, exit signals, slippage, risk-reward ratio, and Sharpe ratio implications. "
                "Identify systematic biases or edge deterioration in the strategy."
            )
            try:
                client = OpenAI(api_key=st.secrets["general"]["openai_api_key"])
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are a quantitative trading coach guiding professional traders."},
                        {"role":"user","content":prompt}
                    ]
                )
                st.markdown(f"**Quant Analysis:** {response.choices[0].message.content}")
            except Exception as e:
                st.error(f"⚠️ Analysis error: {e}")

        # Free-form quant discussion
        st.subheader("💬 Ask Your Quant Coach")
        summary = f"Date: {date.today()}, Total PnL: {total_pnl:.2f}, Win Rate: {win_rate:.2f}%"
        user_q = st.text_area("Ask your quant coach about your strategy's performance, risk-adjusted returns, or edge:")
        if st.button("Submit Quant Query") and user_q:
            full_prompt = summary + "\n" + user_q
            try:
                client = OpenAI(api_key=st.secrets["general"]["openai_api_key"])
                res = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are a quant trading coach for institutional-grade strategies."},
                        {"role":"user","content":full_prompt}
                    ]
                )
                st.markdown(f"**Quant Coach:** {res.choices[0].message.content}")
            except Exception as e:
                st.error(f"❌ GPT error: {e}")
    else:
        st.info("Upload a richly-formatted CSV to perform quantitative trade analysis and get expert feedback.")
