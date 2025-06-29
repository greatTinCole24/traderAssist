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
    if pattern == 'Doji':
        df = pd.DataFrame({
            'open': [1.0, 1.05, 1.02, 1.03],
            'high': [1.03, 1.08, 1.05, 1.06],
            'low': [0.97, 1.02, 1.00, 1.01],
            'close': [1.0, 1.05, 1.02, 1.03]
        })
    elif pattern == 'Bullish Engulfing':
        df = pd.DataFrame({
            'open': [1.1, 1.0],
            'high': [1.12, 1.15],
            'low': [1.08, 0.98],
            'close': [1.05, 1.13]
        })
    elif pattern == 'Bearish Engulfing':
        df = pd.DataFrame({
            'open': [1.0, 1.12],
            'high': [1.02, 1.14],
            'low': [0.98, 1.10],
            'close': [0.99, 1.08]
        })
    elif pattern == 'Hammer':
        df = pd.DataFrame({
            'open': [1.1],
            'high': [1.12],
            'low': [0.95],
            'close': [1.08]
        })
    elif pattern == 'Shooting Star':
        df = pd.DataFrame({
            'open': [1.0],
            'high': [1.2],
            'low': [0.98],
            'close': [1.02]
        })
    else:
        df = pd.DataFrame({'open': [], 'high': [], 'low': [], 'close': []})
    df.index = range(len(df))
    return df

# --- Tabs Setup ---
tab1, tab2, tab3 = st.tabs(["📚 Flashcards", "🧐 Candlestick Quiz", "📒 Journal & Quant Analysis"])

# --- Tab 1: Flashcards ---
with tab1:
    if 'fc_index' not in st.session_state:
        st.session_state.fc_index = 0
        st.session_state.show_definition = False

    def next_card():
        st.session_state.fc_index = (st.session_state.fc_index + 1) % len(flashcards)
        st.session_state.show_definition = False
    def prev_card():
        st.session_state.fc_index = (st.session_state.fc_index - 1) % len(flashcards)
        st.session_state.show_definition = False
    def reveal_def():
        st.session_state.show_definition = True

    card = flashcards[st.session_state.fc_index]
    st.header(card['term'])
    cols = st.columns([1,2,1])
    with cols[0]: st.button("Previous", on_click=prev_card)
    with cols[1]: st.button("Reveal Definition", on_click=reveal_def)
    with cols[2]: st.button("Next", on_click=next_card)

    if st.session_state.show_definition:
        st.write(f"**Definition:** {card['definition']}")
    else:
        st.write("*(Click 'Reveal Definition' to see the definition.)*")

# --- Tab 2: Candlestick Quiz ---
with tab2:
    if 'quiz_pattern' not in st.session_state:
        st.session_state.quiz_pattern = random.choice([c['term'] for c in flashcards])
        st.session_state.quiz_score = 0
        st.session_state.quiz_total = 0

    pattern = st.session_state.quiz_pattern
    df = make_pattern_df(pattern)
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(title_text="Identify the candlestick pattern", showlegend=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    options = [c['term'] for c in flashcards]
    random.shuffle(options)
    choice = st.radio("Which pattern is this?", options)
    if st.button("Submit Answer"):
        st.session_state.quiz_total += 1
        if choice == pattern:
            st.success("Correct! 🎉")
            st.session_state.quiz_score += 1
        else:
            st.error(f"Wrong — the correct answer was {pattern}.")
        st.session_state.quiz_pattern = random.choice([c['term'] for c in flashcards])
    st.write(f"Score: {st.session_state.quiz_score} / {st.session_state.quiz_total}")

# --- Tab 3: Journal & Quant Analysis ---
with tab3:
    st.subheader("📒 Upload Your Trades CSV for Quant Analysis")
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
    uploaded = st.file_uploader(
        "Upload CSV with columns: Ticker, Date, Entry Price, Exit Price, PnL, Volume, Trade Duration", type=["csv"]
    )

    trades = None
    if uploaded:
        trades = pd.read_csv(uploaded)
    elif show_example:
        trades = example_trades.copy()
        st.markdown("**Using Example Trade Data:**")

    if trades is not None:
        st.dataframe(trades)
        if 'PnL' in trades.columns:
            total_pnl = trades['PnL'].sum()
            win_rate = (trades['PnL'] > 0).mean() * 100
            avg_holding = trades['Trade Duration'].mean() if 'Trade Duration' in trades.columns else None
            st.metric("Total PnL", f"${total_pnl:.2f}")
            st.metric("Win Rate", f"{win_rate:.2f}%")
            if avg_holding is not None:
                st.metric("Avg Hold (min)", f"{avg_holding:.1f}")
            fig_pnl = px.histogram(trades, x="PnL", nbins=20, title="PnL Distribution")
            st.plotly_chart(fig_pnl, use_container_width=True)
        else:
            st.warning("Ensure your CSV has a 'PnL' column.")

                if all(col in trades.columns for col in ['Entry Price','Exit Price','PnL']):
        st.subheader("📝 Quant Entry/Exit Analysis")
        trades_json = trades.to_dict(orient='records')
        prompt = (
            f"You are a quantitative trading expert with a PhD in financial engineering. "
            f"Given these trade records: {trades_json}, provide a detailed analysis of entry timing, exit signals, slippage, risk-reward ratio, and Sharpe ratio implications. "
            f"Identify systematic biases or edge deterioration in the strategy."
        )
        # Retrieve API key
        api_key = st.secrets.get("general", {}).get("openai_api_key", st.secrets.get("openai_api_key", ""))
        if not api_key:
            st.error("🚨 OpenAI API key not found. Please add your key to Streamlit secrets.")
        else:
            try:
                client = OpenAI(api_key=api_key)
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

        st.subheader("💬 Ask Your Quant Coach")
        summary = f"Date: {date.today()}, Total PnL: {total_pnl:.2f}, Win Rate: {win_rate:.2f}%"
        user_q = st.text_area(
            "Ask your quant coach about your strategy's performance, risk-adjusted returns, or edge:"
        )
        if st.button("Submit Quant Query") and user_q:
            full_prompt = summary + "\n" + user_q
            api_key = st.secrets.get("general", {}).get("openai_api_key", st.secrets.get("openai_api_key", ""))
            if not api_key:
                st.error("🚨 OpenAI API key not found. Please add your key to Streamlit secrets.")
            else:
                try:
                    client = OpenAI(api_key=api_key)
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
        st.info(
            "Upload a richly-formatted CSV or select example data to perform quantitative trade analysis and get expert feedback."
        )
