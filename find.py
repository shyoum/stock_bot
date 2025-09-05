import streamlit as st
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import google.generativeai as genai
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import io
import re
import time

def main():
    st.title("종목 추천")
    st.info("이 앱은 Plotly의 이미지 변환을 위해 'kaleido' 패키지가 필요할 수 있습니다. `pip install kaleido`")

    # 사용자 입력
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    strategy = st.text_area("원하는 투자 전략을 입력하세요 (예: 최근 6개월간 꾸준히 우상향하며, 거래량이 증가하는 종목)", height=100)
    min_score = st.slider("최소 점수", 1, 10, 7)

    if not api_key or not strategy:
        st.warning("API 키와 투자 전략을 입력해 주세요.")
        return

    # API 설정
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"API 키 설정에 실패했습니다: {e}")
        return

    if st.button("종목 분석 시작"):
        with st.spinner("NASDAQ 종목 리스트를 불러오는 중..."):
            # NASDAQ 종목 리스트 준비
            nasdaq_tickers = fdr.StockListing('NASDAQ')['Symbol'].tolist()
            np.random.shuffle(nasdaq_tickers)

            # 유효한 종목만 필터링
            valid_tickers = []
            progress_bar = st.progress(0, text="유효한 종목을 찾는 중...")
            max_valid_tickers = 50
            
            for i, t in enumerate(nasdaq_tickers[:300]): # 더 많은 종목을 탐색
                try:
                    df = fdr.DataReader(t, '2023-01-01')
                    if not df.empty and len(df) > 200:
                        valid_tickers.append(t)
                        progress_text = f"유효한 종목 찾는 중... ({len(valid_tickers)}/{max_valid_tickers})"
                        progress_bar.progress(len(valid_tickers) / max_valid_tickers, text=progress_text)
                        if len(valid_tickers) >= max_valid_tickers:
                            break
                except Exception:
                    continue
            progress_bar.empty()
        
        if len(valid_tickers) < 5:
             st.error("분석에 필요한 최소 5개의 유효한 종목을 찾지 못했습니다. 다시 시도해주세요.")
             return

        # 5개씩 그룹 생성
        groups = [valid_tickers[i:i+5] for i in range(0, len(valid_tickers), 5)]

        selected_stocks = []
        
        analysis_progress = st.progress(0, text="분석 시작...")
        total_tickers_to_analyze = len(valid_tickers)
        analyzed_count = 0

        for group_idx, group in enumerate(groups):
            if len(selected_stocks) >= 5:
                break

            st.write(f"---")
            st.write(f"### 그룹 {group_idx+1} 분석 중...")

            for ticker in group:
                if len(selected_stocks) >= 5:
                    break
                
                analyzed_count += 1
                progress_text = f"분석 중: {ticker} ({analyzed_count}/{total_tickers_to_analyze})"
                analysis_progress.progress(analyzed_count / total_tickers_to_analyze, text=progress_text)
                
                status_placeholder = st.empty()

                try:
                    # 1. 데이터 가져오기
                    status_placeholder.write(f"⏳ {ticker}: 6개월치 데이터를 가져오는 중...")
                    chart_data = fdr.DataReader(ticker, '2024-03-01')
                    if chart_data.empty or len(chart_data) < 20:
                        status_placeholder.warning(f"📈 {ticker}: 데이터가 부족하여 건너뜁니다.")
                        time.sleep(1)
                        status_placeholder.empty()
                        continue

                    # 2. 차트 객체 생성
                    status_placeholder.write(f"⏳ {ticker}: 차트 객체를 생성하는 중...")
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                      vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    # ... (차트 구성은 동일)
                    fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['Open'], high=chart_data['High'], low=chart_data['Low'], close=chart_data['Close'], increasing_line_color='red', decreasing_line_color='blue', name="Price"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['Close'].rolling(window=20).mean(), mode='lines', name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
                    fig.add_trace(go.Bar(x=chart_data.index, y=chart_data['Volume'], name="Volume"), row=2, col=1)
                    fig.update_layout(title=f"{ticker} 6개월 차트", xaxis_rangeslider_visible=False, width=800, height=500, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    
                    # 3. 차트를 이미지로 변환 (가장 문제가 될 수 있는 부분)
                    img = None
                    try:
                        status_placeholder.write(f"⏳ {ticker}: 차트를 이미지로 변환하는 중... (멈춤 현상 발생 시 'kaleido' 패키지 필요)")
                        img_bytes = fig.to_image(format="png")
                        img = Image.open(io.BytesIO(img_bytes))
                    except Exception as img_e:
                        status_placeholder.error(f"'{ticker}' 차트 이미지 변환 실패. 'kaleido' 패키지를 설치하세요. (pip install kaleido)")
                        st.error(f"상세 오류: {img_e}")
                        time.sleep(3)
                        status_placeholder.empty()
                        continue

                    # 4. Gemini API 호출
                    status_placeholder.write(f"⏳ {ticker}: Gemini API로 차트를 분석하는 중...")
                    chart_summary = f"""
                    종목: {ticker}, 현재가: ${chart_data['Close'].iloc[-1]:.2f}, 
                    6개월 변동률: {((chart_data['Close'].iloc[-1] / chart_data['Close'].iloc[0] - 1) * 100):.1f}%
                    """
                    prompt = f"""
                    당신은 전문 차트 분석가입니다. 이 캔들차트를 보고 다음 투자 전략과 얼마나 일치하는지 1점에서 10점 사이로 평가해주세요.
                    투자 전략: {strategy}
                    종목 정보: {chart_summary}
                    차트의 패턴, 추세, 이동평균선, 거래량 등을 종합적으로 분석하여 점수만 숫자로 답변해주세요. (예: 8)
                    """
                    response = model.generate_content([prompt, img])
                    
                    # 5. 결과 처리
                    status_placeholder.write(f"⏳ {ticker}: 분석 결과 처리 중...")
                    score = 0
                    try:
                        numbers = re.findall(r'\d+', response.text)
                        if numbers:
                            score = int(numbers[0])
                        else:
                            status_placeholder.warning(f"⚠️ {ticker}: 점수를 추출할 수 없습니다. (응답: {response.text.strip()})")
                            continue
                    except (ValueError, IndexError):
                        status_placeholder.warning(f"⚠️ {ticker}: 점수를 변환하는 데 실패했습니다. (응답: {response.text.strip()})")
                        continue

                    if score >= min_score:
                        selected_stocks.append((ticker, score, fig))
                        status_placeholder.success(f"✅ {ticker} 선발! (점수: {score})")
                    else:
                        status_placeholder.info(f"❌ {ticker} 탈락 (점수: {score})")
                    
                    time.sleep(1)
                    status_placeholder.empty()

                except Exception as e:
                    status_placeholder.error(f"{ticker} 분석 중 예상치 못한 오류 발생: {e}")
                    time.sleep(3)
                    status_placeholder.empty()
                    continue
        
        analysis_progress.empty()

        # 최종 결과
        st.write("---")
        st.write("## 🎯 최종 선발 종목")
        if selected_stocks:
            selected_stocks.sort(key=lambda x: x[1], reverse=True)
            for ticker, score, chart in selected_stocks:
                st.write(f"### **{ticker}**: {score}점")
                st.plotly_chart(chart, use_container_width=True, key=f"final_{ticker}")
        else:
            st.warning("기준 점수 이상인 종목이 없습니다.")

if __name__ == "__main__":
    main()

