import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.graph_objects as go
import time
import random
import io
from PIL import Image

def main():
    st.title("🎯 전략 기반 종목 추천")
    
    genai.configure(api_key="AIzaSyBdNmMTS_p19O7Vna5ldyAiFGDL1QVVMsg")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    strategy = st.text_area("투자 전략을 입력하세요:", height=150)
    
    if st.button("전략 분석 및 종목 추천") and strategy:
        st.info("🔍 종목 탐색 중... (최대 100개)")
        recommendations = find_recommendations(strategy, model)
        
        if recommendations:
            st.success(f"✅ {len(recommendations)}개 추천!")
            for i, (ticker, score, analysis) in enumerate(recommendations, 1):
                with st.expander(f"{i}. {ticker} (점수: {score}/10)", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        chart = create_chart(ticker)
                        if chart: st.plotly_chart(chart, use_container_width=True)
                    with col2:
                        st.write(analysis)

def get_tickers():
    """거래소별 전체 상장 종목 가져오기"""
    try:
        import FinanceDataReader as fdr
        tickers = []
        
        for exchange in ['NASDAQ', 'NYSE', 'AMEX', 'KRX']:
            try:
                df = fdr.StockListing(exchange)
                if 'Symbol' in df.columns:
                    tickers.extend(df['Symbol'].dropna().tolist())
            except: continue
        
        return list(set([str(t).strip() for t in tickers if len(str(t).strip()) > 0]))[:3000]
    except:
        return []

def find_recommendations(strategy, model):
    tickers = get_tickers()
    if not tickers: return []
    
    recommendations = []
    searched = 0
    
    progress = st.progress(0)
    status = st.empty()
    
    while len(recommendations) < 10 and searched < 100:
        batch = random.sample(tickers, min(10, len(tickers)))
        
        for ticker in batch:
            searched += 1
            status.text(f"탐색: {searched}/100 | 발견: {len(recommendations)}/10")
            
            try:
                score, analysis = analyze_stock(ticker, strategy, model)
                if score >= 9:
                    recommendations.append((ticker, score, analysis))
                    if len(recommendations) >= 10: break
            except: pass
            
            progress.progress(searched / 100)
            time.sleep(0.1)
    
    return recommendations

def analyze_stock(ticker, strategy, model):
    data = yf.Ticker(ticker).history(period="3mo")
    if data.empty or len(data) < 10: raise Exception()
    
    img = create_chart_image(ticker, data)
    prompt = f"전략: {strategy}\n종목: {ticker}\n차트 분석 후 1-10점과 이유를 제공하세요.\n형식: 점수: X/10\n분석: ..."
    
    response = model.generate_content([prompt, img])
    score = extract_score(response.text)
    return score, response.text

def create_chart_image(ticker, data):
    fig = go.Figure(data=go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], 
        low=data['Low'], close=data['Close']
    ))
    fig.update_layout(title=ticker, width=600, height=400, showlegend=False)
    return Image.open(io.BytesIO(fig.to_image(format="png")))

def create_chart(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1mo")
        if data.empty: return None
        fig = go.Figure(go.Scatter(x=data.index, y=data['Close'], mode='lines'))
        fig.update_layout(height=300, showlegend=False, margin=dict(l=20,r=20,t=30,b=20))
        return fig
    except: return None

def extract_score(text):
    import re
    for pattern in [r'(\d+)/10', r'(\d+)점', r'점수:\s*(\d+)']:
        matches = re.findall(pattern, text)
        if matches: return int(matches[0])
    return 5

if __name__ == "__main__":
    from menu import show_menu
    show_menu()