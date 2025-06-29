import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import uuid
import json
import random
from datetime import datetime, date
from openai import OpenAI

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Trading Coach", layout="wide")
st.title("🧠 AI Trading Coach & Journal")

# --- SESSION STATE FOR STREAK TRACKER ---
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "total_attempts" not in st.session_state:
    st.session_state.total_attempts = 0
if "correct_answers" not in st.session_state:
    st.session_state.correct_answers = 0

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Choose a Ticker", ["NVDA", "TSLA"])
window_size = st.sidebar.slider("Window Size (candles)", 20, 100, 50)
step = st.sidebar.slider("Current Candle Index", 50, 500, 100)

# --- LOAD DATA ---
@st.cache_data
def load_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1h")
    return df.reset_index()

data = load_data(ticker)
if len(data) < step:
    st.warning("Step exceeds data length")
    st.stop()
subset = data.iloc[step - window_size:step]

# --- CANDLESTICK CHART ---
st.subheader(f"{ticker} Candlestick Chart")
fig = go.Figure(data=[go.Candlestick(
    x=subset['Datetime'],
    open=subset['Open'],
    high=subset['High'],
    low=subset['Low'],
    close=subset['Close']
)])
fig.update_layout(xaxis_title="Time", yaxis_title="Price")

# Draw support/resistance if user provides them
st.sidebar.markdown("---")
st.sidebar.subheader("Draw Chart Levels")
support_level = st.sidebar.number_input("Support Level", value=0.0)
resistance_level = st.sidebar.number_input("Resistance Level", value=0.0)

if support_level > 0:
    fig.add_hline(y=support_level, line_dash="dot", annotation_text="Support", line_color="green")
if resistance_level > 0:
    fig.add_hline(y=resistance_level, line_dash="dot", annotation_text="Resistance", line_color="red")

st.plotly_chart(fig, use_container_width=True)

# --- CANDLESTICK ANALYSIS ---
last_candle = subset.iloc[-1]
body = abs(last_candle['Close'] - last_candle['Open'])
upper_wick = last_candle['High'] - max(last_candle['Close'], last_candle['Open'])
lower_wick = min(last_candle['Close'], last_candle['Open']) - last_candle['Low']

st.subheader("🧠 AI Trading Coach Feedback")
if body < upper_wick and body < lower_wick:
    st.markdown("🔍 This looks like a **Doji** or indecision candle.")
elif last_candle['Close'] > last_candle['Open']:
    st.markdown("✅ Bullish candle. Consider if it's in trend continuation.")
else:
    st.markdown("⚠️ Bearish candle. Watch for potential reversals.")

# --- DRILL MODE: GUESS THE PATTERN ---
st.subheader("🎯 Guess the Pattern Drill")
random_idx = random.randint(window_size, len(data) - 1)
demo_subset = data.iloc[random_idx - window_size:random_idx]
demo_last = demo_subset.iloc[-1]
demo_body = abs(demo_last['Close'] - demo_last['Open'])
demo_upper = demo_last['High'] - max(demo_last['Close'], demo_last['Open'])
demo_lower = min(demo_last['Close'], demo_last['Open']) - demo_last['Low']

fig_demo = go.Figure(data=[go.Candlestick(
    x=demo_subset['Datetime'],
    open=demo_subset['Open'],
    high=demo_subset['High'],
    low=demo_subset['Low'],
    close=demo_subset['Close']
)])
st.plotly_chart(fig_demo, use_container_width=True)

user_guess = st.radio("What pattern do you see in the last candle?", ["Bullish", "Bearish", "Doji"])
if st.button("Submit Guess"):
    if demo_body < demo_upper and demo_body < demo_lower:
        correct = "Doji"
    elif demo_last['Close'] > demo_last['Open']:
        correct = "Bullish"
    else:
        correct = "Bearish"

    st.session_state.total_attempts += 1

    if user_guess == correct:
        st.success("✅ Correct! Great job identifying the pattern.")
        st.session_state.correct_answers += 1
        st.session_state.streak += 1
    else:
        st.error(f"❌ Incorrect. The correct answer was {correct}.")
        st.session_state.streak = 0

    st.info(f"🔥 Current Streak: {st.session_state.streak}")
    st.info(f"📊 Total Accuracy: {st.session_state.correct_answers}/{st.session_state.total_attempts} ({(st.session_state.correct_answers / st.session_state.total_attempts) * 100:.2f}%)")

# --- DAILY JOURNALING PROMPT ---
st.subheader("📝 Daily Journaling Prompt")
journal_prompt = "Reflect on your best and worst trades today. What went right, what went wrong, and what would you do differently tomorrow?"
st.markdown(f"> {journal_prompt}")

user_journal = st.text_area("Write your journal entry below:")
if st.button("Submit Journal Entry") and user_journal:
    journal_id = str(uuid.uuid4())
    journal_path = f"journal_entry_{date.today()}_{journal_id}.json"
    with open(journal_path, "w") as f:
        json.dump({"date": str(date.today()), "entry": user_journal}, f)
    st.success(f"✅ Journal entry saved to {journal_path}")

    try:
        client = OpenAI(api_key=st.secrets["openai_api_key"])
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a trading coach that provides feedback on trading journal entries."},
                {"role": "user", "content": user_journal}
            ]
        )
        st.markdown(f"**Coach Feedback:** {response.choices[0].message.content}")
    except Exception as e:
        st.error(f"GPT feedback failed: {e}")

# --- AI CHAT COACH (with OpenAI GPT) ---
st.subheader("💬 Ask Your Trading Coach")
user_input = st.chat_input("Ask your trading coach a question...")
if user_input:
    try:
        client = OpenAI(api_key=st.secrets["openai_api_key"])
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a trading coach that explains candlestick patterns, support/resistance levels, and trade journaling insights."},
                {"role": "user", "content": user_input}
            ]
        )
        st.markdown(f"**Coach:** {response.choices[0].message.content}")
    except Exception as e:
        st.error(f"GPT API call failed: {e}")

# --- TRADE JOURNAL UPLOAD ---
st.subheader("📒 Upload Your Options Trades CSV")
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    trades_df = pd.read_csv(uploaded_file)

    # Add strategy classification dropdown
    st.markdown("### 🧠 Classify Trades by Strategy")
    if 'Strategy' not in trades_df.columns:
        trades_df['Strategy'] = st.selectbox("Select default strategy for all trades", ["Breakout", "Reversal", "Scalp", "Trend Follow"])
    else:
        for i in range(len(trades_df)):
            trades_df.at[i, 'Strategy'] = st.selectbox(f"Strategy for trade {i+1} ({trades_df.at[i, 'Ticker']})", ["Breakout", "Reversal", "Scalp", "Trend Follow"], index=0, key=f"strategy_{i}")

    st.dataframe(trades_df)

    st.markdown("### 📊 Trade Summary")
    if 'PnL' in trades_df.columns:
        st.metric("Total PnL", f"${trades_df['PnL'].sum():,.2f}")
        win_rate = (trades_df['PnL'] > 0).mean()
        st.metric("Win Rate", f"{win_rate * 100:.2f}%")

        strategy_summary = trades_df.groupby('Strategy')['PnL'].agg(['count', 'sum', 'mean'])
        st.markdown("#### 📈 Strategy Performance")
        st.dataframe(strategy_summary)
    else:
        st.warning("Couldn't find 'PnL' column for summary. Please make sure your CSV has appropriate headers like 'PnL', 'Ticker', 'Strike', 'Direction', 'Entry', 'Exit'.")

    session_id = str(uuid.uuid4())
    history_path = f"trading_journal_{session_id}.json"
    with open(history_path, "w") as f:
        f.write(trades_df.to_json(orient="records"))

    st.success(f"Trades saved locally to {history_path}")

    st.markdown("### 🧠 Coach Notes:")
    st.markdown("*Review how your entries align with market structure. Were entries near support/resistance? Were exits rushed or optimal?*")
    st.markdown("*How did the broader market (SPY/QQQ) behave during your trades?*")
