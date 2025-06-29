import streamlit as st
import yfinance as yf
import pandas as pd
import random
from datetime import datetime, date
from openai import OpenAI
import matplotlib.pyplot as plt
import seaborn as sns

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

# --- TRADINGVIEW CHART EMBED ---
st.subheader(f"📈 {ticker} TradingView Chart")
st.components.v1.html(f"""
    <div class=\"tradingview-widget-container\">
      <div id=\"tradingview_{ticker.lower()}\"></div>
      <script type=\"text/javascript\" src=\"https://s3.tradingview.com/tv.js\"></script>
      <script type=\"text/javascript\">
      new TradingView.widget({{
          \"width\": \"100%\",
          \"height\": 600,
          \"symbol\": \"{ticker}\",
          \"interval\": \"60\",
          \"timezone\": \"Etc/UTC\",
          \"theme\": \"dark\",
          \"style\": \"1\",
          \"locale\": \"en\",
          \"toolbar_bg\": \"#f1f3f6\",
          \"enable_publishing\": false,
          \"hide_side_toolbar\": false,
          \"allow_symbol_change\": true,
          \"container_id\": \"tradingview_{ticker.lower()}\"
      }});
      </script>
    </div>
""", height=600)

# --- CANDLESTICK ANALYSIS ---
last_candle = subset.iloc[-1]
body = abs(float(last_candle['Close']) - float(last_candle['Open']))
upper_wick = float(last_candle['High']) - max(float(last_candle['Close']), float(last_candle['Open']))
lower_wick = min(float(last_candle['Close']), float(last_candle['Open'])) - float(last_candle['Low'])

st.subheader("🧠 AI Trading Coach Feedback")
if body < upper_wick and body < lower_wick:
    st.markdown("🔍 This looks like a **Doji** or indecision candle.")
elif float(last_candle['Close']) > float(last_candle['Open']):
    st.markdown("✅ Bullish candle. Consider if it's in trend continuation.")
else:
    st.markdown("⚠️ Bearish candle. Watch for potential reversals.")

# --- DRILL MODE: GUESS THE PATTERN ---
st.subheader("🎯 Guess the Pattern Drill")
random_idx = random.randint(window_size, len(data) - 1)
demo_subset = data.iloc[random_idx - window_size:random_idx]
demo_last = demo_subset.iloc[-1]
demo_body = abs(float(demo_last['Close']) - float(demo_last['Open']))
demo_upper = float(demo_last['High']) - max(float(demo_last['Close']), float(demo_last['Open']))
demo_lower = min(float(demo_last['Close']), float(demo_last['Open'])) - float(demo_last['Low'])

user_guess = st.radio("What pattern do you see in the last candle?", ["Bullish", "Bearish", "Doji"])
if st.button("Submit Guess"):
    if demo_body < demo_upper and demo_body < demo_lower:
        correct = "Doji"
    elif float(demo_last['Close']) > float(demo_last['Open']):
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

# --- AI CHAT COACH (with OpenAI GPT) ---
st.subheader("💬 Ask Your Trading Coach")
# Add context about the last candle
if body < upper_wick and body < lower_wick:
    direction = "Doji"
elif float(last_candle['Close']) > float(last_candle['Open']):
    direction = "Bullish"
else:
    direction = "Bearish"
candle_description = f"The most recent candle on the {ticker} chart is a {direction} candle."

user_input = st.chat_input("Ask your trading coach a question...")
if user_input:
    prompt = f"{candle_description}\n{user_input}"
    try:
        client = OpenAI(api_key=st.secrets["general"]["openai_api_key"]) 
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a trading coach that explains candlestick patterns, support/resistance levels, and trade journaling insights."},
                {"role": "user", "content": prompt}
            ]
        )
        st.markdown(f"**Coach:** {response.choices[0].message.content}")
    except Exception as e:
        # Handle insufficient quota specifically
        if 'insufficient_quota' in str(e):
            st.error("🚨 You have exceeded your OpenAI API quota. Please check your plan and billing details.")
        else:
            st.error(f"❌ GPT API call failed: {e}")

# --- JOURNALING SECTION ---
st.subheader("📝 Daily Trade Journal with Feedback")
st.markdown("Reflect on your trades or chart observations. The coach will give you feedback.")

example = """Example: Entered TSLA 5-min CALL after break of EMA9 with volume confirmation. Stop loss was set below last swing low. Took partial profits at 20% and final exit at 50%. Missed the breakout retest opportunity."""

journal_entry = st.text_area("Write your journal entry for today:", value=example)
if st.button("Submit Journal Entry"):
    if journal_entry:
        prompt = journal_entry
        try:
            client = OpenAI(api_key=st.secrets["general"]["openai_api_key"]) 
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a trading coach. Provide clear and concise feedback on this journal entry to help the user improve their trading psychology, chart reading, and execution."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.success("✅ Journal entry received. Here's your feedback:")
            st.markdown(f"**Coach Feedback:** {response.choices[0].message.content}")
        except Exception as e:
            # Handle insufficient quota specifically
            if 'insufficient_quota' in str(e):
                st.error("🚨 You have exceeded your OpenAI API quota. Please check your plan and billing details.")
            else:
                st.error(f"⚠️ Error processing journal entry: {e}")
    else:
        st.warning("✍️ Please write something before submitting.")

# --- EXAMPLE TRADE TABLE ---
st.subheader("📋 Sample Trade Log (SPY, NVDA, TSLA)")
sample_trades = pd.DataFrame({
    "Ticker": ["SPY", "TSLA", "NVDA", "SPY", "TSLA", "NVDA", "SPY", "TSLA", "NVDA", "SPY"],
    "Date": pd.date_range(end=pd.Timestamp.today(), periods=10).strftime("%Y-%m-%d"),
    "Time": ["10:00", "10:05", "09:45", "11:00", "10:30", "11:15", "13:00", "09:35", "14:00", "15:20"],
    "Trade Type": ["Call", "Put", "Call", "Put", "Call", "Put", "Call", "Call", "Put", "Call"],
    "Strategy": ["EMA Breakout", "VWAP Reversal", "Trend Follow", "Reversal", "EMA Breakout", "Overextension", "VWAP Bounce", "EMA Breakout", "Double Top", "Breakout Retest"],
    "Entry Price": [1.23, 2.15, 1.89, 2.00, 1.75, 2.05, 1.10, 1.50, 2.30, 1.65],
    "Exit Price": [1.65, 1.80, 2.10, 1.60, 2.25, 1.70, 1.55, 2.05, 1.90, 2.10],
    "Profit/Loss": [0.42, -0.35, 0.21, -0.40, 0.50, -0.35, 0.45, 0.55, -0.40, 0.45]
})
st.dataframe(sample_trades, use_container_width=True)

# --- PROFIT/LOSS AND STRATEGY VISUALIZATION ---
st.subheader("📊 Trade Performance Visualization")

# Profit/Loss Bar Chart by Date
fig1, ax1 = plt.subplots()
sns.barplot(data=sample_trades, x="Date", y="Profit/Loss", hue="Ticker", ax=ax1)
ax1.set_title("Profit/Loss per Trade")
ax1.set_ylabel("Profit/Loss")
ax1.set_xlabel("Date")
st.pyplot(fig1)

# Strategy Type Average P/L
fig2, ax2 = plt.subplots()
sns.barplot(data=sample_trades, x="Strategy", y="Profit/Loss", estimator=sum, ci=None, ax=ax2)
ax2.set_title("Total Profit/Loss by Strategy")
ax2.set_ylabel("Total P/L")
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
st.pyplot(fig2)
