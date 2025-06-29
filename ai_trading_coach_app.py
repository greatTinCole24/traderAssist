import streamlit as st
import yfinance as yf
import pandas as pd
import random
import io
from PIL import Image
from datetime import datetime, date
from openai import OpenAI
import plotly.graph_objects as go
from streamlit_drawable_canvas import st_canvas
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

@st.cache_data
def load_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1h")
    return df.reset_index()

data = load_data(ticker)
if len(data) < step:
    st.warning("Step exceeds data length")
    st.stop()
subset = data.iloc[step - window_size:step]

# --- TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📈 Chart", "🎯 Quiz & Annotation", "💬 Chat & Journal"])

# --- TAB 1: TradingView Chart + Insight ---
with tab1:
    st.subheader(f"{ticker} TradingView Chart")
    st.components.v1.html(f"""
        <div class=\"tradingview-widget-container\">  
          <div id=\"tradingview_{ticker.lower()}\"></div>
          <script src=\"https://s3.tradingview.com/tv.js\"></script>
          <script>
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
    last = subset.iloc[-1]
    body = abs(float(last['Close']) - float(last['Open']))
    upper = float(last['High']) - max(float(last['Close']), float(last['Open']))
    lower = min(float(last['Close']), float(last['Open'])) - float(last['Low'])
    st.subheader("🔎 Candle Insight")
    if body < upper and body < lower:
        st.markdown("**Doji** - Market indecision, await clearer signal.")
    elif float(last['Close']) > float(last['Open']):
        st.markdown("**Bullish** - Buyers in control, watch for continuation.")
    else:
        st.markdown("**Bearish** - Sellers dominating, monitor support levels.")

# --- TAB 2: Quiz & Annotation ---
with tab2:
    st.subheader("🎯 Guess the Pattern Drill")
    idx = random.randint(window_size, len(data) - 1)
    demo = data.iloc[idx - window_size:idx]
    # Display Plotly candlestick with drawing tools
    fig_widget = go.FigureWidget(data=[go.Candlestick(
        x=demo['Datetime'], open=demo['Open'], high=demo['High'],
        low=demo['Low'], close=demo['Close']
    )])
    fig_widget.update_layout(height=400, template="plotly_dark",
                              dragmode='drawline',
                              newshape=dict(line=dict(color='cyan', width=2)),
                              modebar_add=['drawline','eraseshape'])
    st.plotly_chart(fig_widget, use_container_width=True)

    # Capture shapes and send to AI
    if st.button("Submit Drawings"):
        shapes = fig_widget.layout.shapes
        prompt = f"User drew these shapes on the chart: {shapes}. Please analyze support/resistance lines and highlighted regions."  
        try:
            client = OpenAI(api_key=st.secrets["general"]["openai_api_key"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a trading coach analyzing user-drawn chart annotations."},
                    {"role":"user","content":prompt}
                ]
            )
            st.markdown(f"**Annotation Coach:** {response.choices[0].message.content}")
        except Exception as e:
            if 'insufficient_quota' in str(e):
                st.warning("🚨 Quota exceeded; unable to provide annotation feedback.")
            else:
                st.error(f"❌ GPT error: {e}")

# --- TAB 3: Chat & Journal ---
with tab3:
    st.subheader("💬 Chat with Trading Coach")
    # Candle context
    if body < upper and body < lower:
        direction = "Doji"
    elif float(last['Close']) > float(last['Open']):
        direction = "Bullish"
    else:
        direction = "Bearish"
    prompt_ctx = f"Last candle is {direction} on {ticker}."
    user_q = st.chat_input("Ask coach...")
    if user_q:
        prompt = f"{prompt_ctx}\n{user_q}"
        try:
            client = OpenAI(api_key=st.secrets["general"]["openai_api_key"])
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a helpful trading coach."},
                    {"role":"user","content":prompt}
                ]
            )
            st.markdown(f"**Coach:** {res.choices[0].message.content}")
        except Exception as e:
            st.error(f"❌ GPT error: {e}")
    st.markdown("---")
    st.subheader("📝 Daily Trade Journal")
    journal = st.text_area("Your journal entry:")
    if st.button("Submit Entry"):
        if journal:
            try:
                client = OpenAI(api_key=st.secrets["general"]["openai_api_key"])
                res = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"Provide feedback on journal entry."},
                        {"role":"user","content":journal}
                    ]
                )
                st.markdown(f"**Feedback:** {res.choices[0].message.content}")
            except Exception as e:
                st.error(f"⚠️ Journal error: {e}")
        else:
            st.warning("✍️ Please write something first.")
