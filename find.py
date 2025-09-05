import streamlit as st
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import google.generativeai as genai
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import io

def main():
    st.title("종목 추천")
    
    # 사용자 입력
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    strategy = st.text_area("원하는 전략", height=100)
    min_score = st.slider("최소 점수", 1, 10, 7)
    
    if not api_key or not strategy:
        st.warning("API 키와 전략을 입력하세요.")
        return
    
    # API 설정
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    if st.button("종목 분석 시작"):
        with st.spinner("NASDAQ 종목 준비 중..."):
            # NASDAQ 종목 리스트 준비
            nasdaq_tickers = fdr.StockListing('NASDAQ')['Symbol'].tolist()
            np.random.shuffle(nasdaq_tickers)
            
            # 유효한 종목만 필터링
            valid_tickers = []
            for t in nasdaq_tickers[:200]:
                try:
                    df = fdr.DataReader(t, '2025-01-01')
                    if not df.empty and len(df) > 100:
                        valid_tickers.append(t)
                        if len(valid_tickers) >= 50:
                            break
                except:
                    continue
            
            # 5개씩 10개 그룹 생성
            groups = [valid_tickers[i:i+5] for i in range(0, min(50, len(valid_tickers)), 5)]
        
        selected_stocks = []
        
        for group_idx, group in enumerate(groups):
            if len(selected_stocks) >= 5:
                break
                
            st.write(f"### 그룹 {group_idx+1} 분석 중...")
            
            for ticker in group:
                if len(selected_stocks) >= 5:
                    break
                    
                try:
                    # 6개월 데이터 가져오기
                    chart_data = fdr.DataReader(ticker, '2024-03-01')
                    if chart_data.empty:
                        continue
                    
                    # 캔들차트 생성
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                       vertical_spacing=0.02, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Candlestick(
                        x=chart_data.index,
                        open=chart_data['Open'],
                        high=chart_data['High'],
                        low=chart_data['Low'],
                        close=chart_data['Close'],
                        increasing_line_color='red',
                        decreasing_line_color='blue',
                        name="Price"
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Bar(
                        x=chart_data.index, 
                        y=chart_data['Volume'],
                        name="Volume"
                    ), row=2, col=1)
                    
                    fig.update_layout(
                        title=f"{ticker} 6개월 차트",
                        xaxis_rangeslider_visible=False,
                        width=800,
                        height=600
                    )
                    
                    # 차트 표시
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}")
                    
                    # 차트를 이미지로 변환
                    img_bytes = fig.to_image(format="png")
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # 기본 정보
                    chart_summary = f"""
                    종목: {ticker}
                    현재가: ${chart_data['Close'].iloc[-1]:.2f}
                    6개월 변동률: {((chart_data['Close'].iloc[-1] / chart_data['Close'].iloc[0] - 1) * 100):.1f}%
                    """
                    
                    # Gemini로 차트 이미지와 함께 분석
                    prompt = f"""
                    이 캔들차트를 보고 다음 투자 전략과 얼마나 일치하는지 1-10점으로 평가해주세요.
                    
                    투자 전략: {strategy}
                    
                    종목 정보: {chart_summary}
                    
                    차트의 패턴, 추세, 거래량 등을 종합적으로 분석하여 점수만 숫자로 답변해주세요. (예: 8)
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    try:
                        score = int(response.text.strip())
                    except:
                        # 숫자 추출 시도
                        import re
                        numbers = re.findall(r'\d+', response.text)
                        score = int(numbers[0]) if numbers else 0
                    
                    st.write(f"**{ticker}**: {score}점")
                    
                    if score >= min_score:
                        selected_stocks.append((ticker, score))
                        st.success(f"✅ {ticker} 선발! (점수: {score})")
                    else:
                        st.info(f"❌ {ticker} 탈락 (점수: {score})")
                    
                except Exception as e:
                    st.error(f"{ticker} 분석 실패: {e}")
                    continue
        
        # 최종 결과
        st.write("## 🎯 최종 선발 종목")
        if selected_stocks:
            for ticker, score in selected_stocks:
                st.write(f"• **{ticker}**: {score}점")
        else:
            st.warning("기준 점수 이상인 종목이 없습니다.")

if __name__ == "__main__":
    from menu import show_menu
    show_menu()