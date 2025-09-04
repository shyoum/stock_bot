import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.graph_objects as go
import random
import io
from PIL import Image

def main():
    st.title("🎲 랜덤 10개 종목 점수 매기기")
    
    genai.configure(api_key="AIzaSyBdNmMTS_p19O7Vna5ldyAiFGDL1QVVMsg")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    strategy = st.text_area("투자 전략을 입력하세요:", height=150)
    
    if st.button("랜덤 10개 종목 분석") and strategy:
        st.info("🎲 랜덤 10개 종목 선택 및 분석 중...")
        results = analyze_random_10(strategy, model)
        
        if results:
            st.success(f"✅ 10개 종목 분석 완료!")
            for i, (ticker, score, analysis) in enumerate(results, 1):
                with st.expander(f"{i}. {ticker} (점수: {score}/10)", expanded=False):
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
                st.write(f"{exchange} 종목 로딩 중...")
                df = fdr.StockListing(exchange)
                if 'Symbol' in df.columns:
                    exchange_tickers = df['Symbol'].dropna().tolist()
                    tickers.extend(exchange_tickers)
                    st.write(f"{exchange}: {len(exchange_tickers)}개 종목")
            except Exception as e:
                st.write(f"{exchange} 로딩 실패: {str(e)[:50]}")
                continue
        
        tickers = list(set([str(t).strip() for t in tickers if len(str(t).strip()) > 0]))[:3000]
        st.write(f"총 {len(tickers)}개 종목 준비 완료")
        return tickers
        
    except ImportError:
        st.error("FinanceDataReader가 설치되지 않았습니다: pip install FinanceDataReader")
        return []
    except Exception as e:
        st.error(f"종목 로딩 중 오류: {str(e)}")
        return []

def analyze_random_10(strategy, model):
    tickers = get_tickers()
    if not tickers: return []
    
    # 완전 랜덤하게 10개 선택
    random_10 = random.sample(tickers, min(10, len(tickers)))
    results = []
    
    progress = st.progress(0)
    status = st.empty()
    
    for i, ticker in enumerate(random_10):
        status.text(f"분석 중: {i+1}/10 - {ticker}")
        
        try:
            score, analysis = analyze_stock(ticker, strategy, model)
            results.append((ticker, score, analysis))
        except:
            results.append((ticker, 0, "분석 실패"))
        
        progress.progress((i + 1) / 10)
    
    # 점수순 정렬
    results.sort(key=lambda x: x[1], reverse=True)
    return results

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