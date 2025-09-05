import streamlit as st
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import google.generativeai as genai
import mplfinance as mpf
from PIL import Image
import io
import re
import time

def main():
    st.title("AI 차트 분석 기반 종목 추천")

    # 사용자 입력
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    strategy = st.text_area("원하는 투자 전략을 입력하세요 (예: 최근 꾸준히 우상향하며, 거래량이 증가하는 종목)", height=100)
    min_score = st.slider("최소 점수 (자동 분석용)", 1.0, 10.0, 7.0, 0.5)

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

    # 옵션 1: 이미지 업로드하여 분석
    st.markdown("---")
    st.subheader("옵션 1: 차트 이미지 직접 분석")
    uploaded_file = st.file_uploader("분석할 차트 이미지를 업로드하세요.", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="업로드된 차트 이미지", use_container_width=True)
        if st.button("업로드 이미지 분석하기"):
            with st.spinner("이미지를 분석 중입니다..."):
                try:
                    img = Image.open(uploaded_file)
                    prompt = f"""
                    당신은 전문 차트 분석가입니다. 이 캔들차트 이미지를 보고 다음 투자 전략과 얼마나 일치하는지 최소 0점, 최대 10점 범위에서 0.5점 단위로 평가해주세요.
                    투자 전략: {strategy}
                    첨부한 캔들차트 이미지를 중점적으로 분석하여서, 비판적이고 냉철하게 점수를 매겨주세요. 점수만 간결하게 숫자로 답변해주세요. (예: 8.5)
                    """
                    response = model.generate_content([prompt, img])
                    
                    # 결과 처리
                    numbers = re.findall(r'[0-9]+\.?[0-9]*', response.text)
                    if numbers:
                        score = float(numbers[0])
                        st.success(f"## 분석 점수: {score}점")
                    else:
                        st.warning(f"⚠️ 점수를 추출할 수 없습니다. (AI 응답: {response.text.strip()})")

                except Exception as e:
                    st.error(f"이미지 분석 중 오류가 발생했습니다: {e}")

    # 옵션 2: NASDAQ 종목 자동 분석
    st.markdown("---")
    st.subheader("옵션 2: NASDAQ 종목 자동 분석")
    if st.button("자동 종목 분석 시작"):
        with st.spinner("NASDAQ 종목 리스트를 불러오는 중..."):
            nasdaq_tickers = fdr.StockListing('NASDAQ')['Symbol'].tolist()
            np.random.shuffle(nasdaq_tickers)

            valid_tickers = []
            progress_bar = st.progress(0, text="유효한 종목을 찾는 중...")
            max_valid_tickers = 50
            
            for i, t in enumerate(nasdaq_tickers[:300]):
                try:
                    df = fdr.DataReader(t, '2025-01-01') # 날짜 수정
                    if not df.empty and len(df) > 50: # 기간에 맞춰 조건 수정
                        valid_tickers.append(t)
                        progress_text = f"유효한 종목 찾는 중... ({len(valid_tickers)}/{max_valid_tickers})"
                        progress_bar.progress(len(valid_tickers) / max_valid_tickers, text=progress_text)
                        if len(valid_tickers) >= max_valid_tickers:
                            break
                except Exception:
                    continue
            progress_bar.empty()
        
        if len(valid_tickers) < 1:
             st.error("분석에 유효한 종목을 찾지 못했습니다. 다시 시도해주세요.")
             return

        selected_stocks = []
        analysis_progress = st.progress(0, text="분석 시작...")
        total_tickers_to_analyze = len(valid_tickers)
        analyzed_count = 0
        
        st.write("---")
        st.write(f"### 총 {total_tickers_to_analyze}개 종목 분석 시작")

        for ticker in valid_tickers:
            if len(selected_stocks) >= 5:
                st.info("최대 5개의 추천 종목을 찾았습니다. 분석을 중단합니다.")
                break
            
            analyzed_count += 1
            progress_text = f"분석 중: {ticker} ({analyzed_count}/{total_tickers_to_analyze})"
            analysis_progress.progress(analyzed_count / total_tickers_to_analyze, text=progress_text)
            
            try:
                # 1. 데이터 가져오기
                st.write(f"⏳ {ticker}: 2025년 데이터를 가져오는 중...") # 메시지 수정
                chart_data = fdr.DataReader(ticker, '2025-01-01') # 날짜 수정
                if chart_data.empty or len(chart_data) < 20:
                    st.warning(f"📈 {ticker}: 데이터가 부족하여 건너뜁니다.")
                    continue

                # 2. 차트 이미지 생성
                st.write(f"⏳ {ticker}: 차트 이미지를 생성하는 중...")
                buf = io.BytesIO()
                mpf.plot(chart_data, type='candle', mav=(20), volume=True,
                         title=f"\n{ticker} 2025 YTD Chart", style='yahoo', # 제목 수정
                         savefig=dict(fname=buf, dpi=150, format='png', bbox_inches='tight'))
                buf.seek(0)
                chart_image_bytes = buf.read()
                img = Image.open(io.BytesIO(chart_image_bytes))
                buf.close()

                # 3. Gemini API 호출
                st.write(f"⏳ {ticker}: Gemini API로 차트를 분석하는 중...")
                chart_summary = f"""
                종목: {ticker}, 현재가: ${chart_data['Close'].iloc[-1]:.2f}, 
                올해 변동률: {((chart_data['Close'].iloc[-1] / chart_data['Close'].iloc[0] - 1) * 100):.1f}% 
                """ # 텍스트 수정
                prompt = f"""
                이 캔들차트를 보고 다음 투자 전략과 얼마나 일치하는지 최소 0점, 최대 10점 범위에서 0.5점 단위로 평가해주세요.
                투자 전략: {strategy}
                종목 정보: {chart_summary}
                종목 정보보다는 첨부한 캔들차트 이미지를 중점적으로 분석하여서, 비판적이고 냉철하게 점수를 매겨주세요. 점수만 간결하게 숫자로 답변해주세요. (예: 8.5)
                """
                response = model.generate_content([prompt, img])
                
                # 4. 결과 처리
                numbers = re.findall(r'[0-9]+\.?[0-9]*', response.text)
                if numbers:
                    score = float(numbers[0])
                    if score >= min_score:
                        selected_stocks.append((ticker, score, chart_image_bytes))
                        st.success(f"✅ {ticker} 선발! (점수: {score})")
                    else:
                        st.info(f"❌ {ticker} 탈락 (점수: {score})")
                else:
                    st.warning(f"⚠️ {ticker}: 점수를 추출할 수 없습니다. (응답: {response.text.strip()})")

            except Exception as e:
                st.error(f"{ticker} 분석 중 예상치 못한 오류 발생: {e}")
                continue
        
        analysis_progress.empty()

        # 최종 결과
        st.write("---")
        st.write("## 🎯 최종 선발 종목")
        if selected_stocks:
            selected_stocks.sort(key=lambda x: x[1], reverse=True)
            for ticker, score, chart_image in selected_stocks:
                st.write(f"### **{ticker}**: {score}점")
                st.image(chart_image, use_container_width=True, caption=f"{ticker} Chart")
        else:
            st.warning("기준 점수 이상인 종목이 없습니다.")

if __name__ == "__main__":
    main()

