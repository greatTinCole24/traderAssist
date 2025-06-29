import streamlit as st
import yfinance as yf
import pandas as pd
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

# --- TRADINGVIEW CHART EMBED ---
st.subheader(f"📈 {ticker} TradingView Chart")
st.components.v1.html(f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_{ticker.lower()}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
          "width": "100%",
          "height": 600,
          "symbol": "{ticker}",
          "interval": "60",
          "timezone": "Etc/UTC",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tradingview_{ticker.lower()}"
      }});
      </script>
    </div>
""", height=600)

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
        st.error("❌ GPT API call failed. Please check your OpenAI API key in Streamlit secrets.")

# --- JOURNALING SECTION ---
st.subheader("📝 Daily Trade Journal with Feedback")
st.markdown("Reflect on your trades or chart observations. The coach will give you feedback.")

journal_entry = st.text_area("Write your journal entry for today:")
if st.button("Submit Journal Entry"):
    if journal_entry:
        try:
            client = OpenAI(api_key=st.secrets["openai_api_key"])
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a trading coach. Provide clear and concise feedback on this journal entry to help the user improve their trading psychology, chart reading, and execution."},
                    {"role": "user", "content": journal_entry}
                ]
            )
            st.success("✅ Journal entry received. Here's your feedback:")
            st.markdown(f"**Coach Feedback:** {response.choices[0].message.content}")
        except Exception as e:
            st.error("⚠️ Error processing journal entry. Check your API key or try again.")
    else:
        st.warning("✍️ Please write something before submitting.")
