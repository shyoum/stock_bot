import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import google.generativeai as genai
import mplfinance as mpf
from PIL import Image
import io
import re
import time
import warnings
warnings.filterwarnings('ignore')

def main():
    st.title("종목 추천")
    st.info("전략 입력 또는 이미지 첨부 중 한 개 이상 입력해주세요.")
    st.info("이미지는 'png', 'jpg', 'jpeg'를 첨부할 수 있습니다.")

    # --- 통합 사용자 입력 ---
    st.subheader("1. 프롬프트 입력")
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    
    strategy_text = st.text_area("투자 전략을 '텍스트'로 입력하세요. (선택 사항)", 
                                 placeholder="예: 최근 꾸준히 우상향하며, 거래량이 증가하는 종목", height=100)
    
    strategy_image_files = st.file_uploader("참고용 차트 이미지를 업로드하세요. (최대 5개, 선택 사항)", 
                                           type=['png', 'jpg', 'jpeg'], 
                                           key="strategy_uploader",
                                           accept_multiple_files=True)

    if len(strategy_image_files) > 5:
        st.warning("최대 5개의 이미지만 업로드할 수 있습니다. 처음 5개의 이미지만 사용됩니다.")
        strategy_image_files = strategy_image_files[:5]

    min_score = st.slider("최소 점수 (유사도/일치도)", 1, 10, 7, 1)

    if not api_key:
        st.warning("API 키를 먼저 입력해 주세요.")
        return

    # API 설정
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-image")
    except Exception as e:
        st.error(f"API 키 설정에 실패했습니다: {e}")
        return

    # --- 분석 시작 버튼 ---
    st.markdown("---")
    if st.button("🚀 종목 찾기 시작!"):
        if not strategy_text and not strategy_image_files:
            st.error("분석을 시작하려면 '텍스트 전략'을 입력하거나 '참고용 차트 이미지'를 업로드해야 합니다.")
            return

        strategy_images = []
        if strategy_image_files:
            st.write(f"▼ 아래 {len(strategy_image_files)}개의 참고 이미지를 기준으로 분석합니다.")
            cols = st.columns(len(strategy_image_files))
            for idx, uploaded_file in enumerate(strategy_image_files):
                img = Image.open(uploaded_file)
                strategy_images.append(img)
                with cols[idx]:
                    st.image(img, caption=f"참고용 차트 {idx+1}", use_column_width=True)

        with st.spinner("S&P500 종목 리스트를 불러오는 중..."):
            # S&P500 전체 502개 종목 (2025년 10월 기준)
            sp500_tickers = [
                'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'GOOG', 'AMZN', 'META', 'AVGO', 'TSLA', 'BRK-B',
                'JPM', 'WMT', 'ORCL', 'V', 'LLY', 'MA', 'NFLX', 'XOM', 'COST', 'JNJ',
                'PLTR', 'HD', 'ABBV', 'PG', 'BAC', 'CVX', 'KO', 'AMD', 'TMUS', 'GE',
                'UNH', 'CSCO', 'PM', 'WFC', 'CRM', 'MS', 'ABT', 'LIN', 'IBM', 'MCD',
                'AXP', 'BX', 'GS', 'MRK', 'DIS', 'T', 'RTX', 'PEP', 'INTU', 'UBER',
                'CAT', 'VZ', 'TMO', 'NOW', 'BA', 'BKNG', 'BLK', 'TXN', 'SCHW', 'C',
                'ISRG', 'ANET', 'SPGI', 'QCOM', 'GEV', 'AMGN', 'ACN', 'NEE', 'BSX', 'DHR',
                'ADBE', 'TJX', 'GILD', 'SYK', 'PGR', 'PFE', 'LOW', 'COF', 'HON', 'ETN',
                'MU', 'APH', 'DE', 'UNP', 'AMAT', 'KKR', 'LRCX', 'CMCSA', 'ADP', 'COP',
                'MDT', 'PANW', 'KLAC', 'ADI', 'SNPS', 'NKE', 'MO', 'INTC', 'CB', 'WELL',
                'CRWD', 'DASH', 'ICE', 'SO', 'SBUX', 'LMT', 'MMC', 'VRTX', 'CEG', 'PLD',
                'CME', 'BMY', 'AMT', 'CDNS', 'DUK', 'TT', 'DELL', 'PH', 'MCO', 'HCA',
                'WM', 'SHW', 'CVS', 'CTAS', 'ORLY', 'RCL', 'GD', 'MCK', 'NOC', 'COIN',
                'MMM', 'MDLZ', 'CI', 'AON', 'ECL', 'APO', 'TDG', 'EQIX', 'ABNB', 'MSI',
                'NEM', 'ITW', 'PNC', 'AJG', 'UPS', 'EMR', 'FI', 'RSG', 'MAR', 'USB',
                'BK', 'WMB', 'ELV', 'HWM', 'CL', 'ZTS', 'JCI', 'CSX', 'AZO', 'VST',
                'PYPL', 'EOG', 'SPG', 'APD', 'HLT', 'MNST', 'NSC', 'ADSK', 'FCX', 'FTNT',
                'TEL', 'WDAY', 'TRV', 'AEP', 'REGN', 'AXON', 'KMI', 'URI', 'CMG', 'DLR',
                'TFC', 'NXPI', 'COR', 'PWR', 'ROP', 'AFL', 'BDX', 'FAST', 'GLW', 'CARR',
                'CMI', 'ALL', 'NDAQ', 'FDX', 'GM', 'O', 'SRE', 'IDXX', 'D', 'MET',
                'PCAR', 'LHX', 'PSX', 'PSA', 'PAYX', 'DHI', 'SLB', 'MPC', 'CTVA', 'ROST',
                'AMP', 'KDP', 'CBRE', 'OKE', 'TGT', 'GWW', 'XYZ', 'KR', 'EBAY', 'EW',
                'F', 'CPRT', 'EXC', 'GRMN', 'CCI', 'AIG', 'DDOG', 'KMB', 'OXY', 'EA',
                'MSCI', 'TTWO', 'BKR', 'PEG', 'XEL', 'VLO', 'AME', 'RMD', 'YUM', 'FANG',
                'CHTR', 'KVUE', 'ETR', 'MPWR', 'CCL', 'DAL', 'ROK', 'VMC', 'SYY', 'CSGP',
                'PRU', 'TKO', 'VRSK', 'LYV', 'FIS', 'LVS', 'HIG', 'MLM', 'ED', 'HSY',
                'CAH', 'MCHP', 'TRGP', 'HUM', 'VICI', 'LEN', 'WEC', 'XYL', 'OTIS', 'CTSH',
                'ACGL', 'A', 'GEHC', 'NUE', 'PCG', 'EQT', 'EL', 'STX', 'UAL', 'KHC',
                'IQV', 'RJF', 'WAB', 'WTW', 'FICO', 'ODFL', 'TSCO', 'DXCM', 'BRO', 'STT',
                'IR', 'VTR', 'DD', 'EFX', 'BR', 'EXR', 'MTB', 'STZ', 'WBD', 'AWK',
                'NRG', 'DTE', 'ADM', 'FITB', 'KEYS', 'K', 'ROL', 'HPE', 'AEE', 'MTD',
                'AVB', 'PPL', 'IRM', 'WRB', 'SMCI', 'ATO', 'VLTO', 'SYF', 'GIS', 'FOXA',
                'WDC', 'CBOE', 'EXPE', 'PHM', 'TTD', 'FOX', 'EQR', 'VRSN', 'TDY', 'PPG',
                'FE', 'HPQ', 'WSM', 'TYL', 'CNP', 'DG', 'PTC', 'IP', 'HBAN', 'DOV',
                'ES', 'STE', 'DRI', 'NTRS', 'LULU', 'CINF', 'SBAC', 'NVR', 'DLTR', 'TROW',
                'ULTA', 'JBL', 'RF', 'HUBB', 'EXE', 'LDOS', 'CHD', 'PODD', 'CPAY', 'LH',
                'SW', 'FSLR', 'NTAP', 'CMS', 'DVN', 'EIX', 'CDW', 'GPN', 'CFG', 'LII',
                'ON', 'TPR', 'TPL', 'GDDY', 'ZBH', 'BIIB', 'TSN', 'AMCR', 'DGX', 'KEY',
                'L', 'NI', 'TRMB', 'GEN', 'ERIE', 'GPC', 'STLD', 'MKC', 'WY', 'INVH',
                'CTRA', 'IT', 'HAL', 'FFIV', 'WST', 'NWS', 'J', 'RL', 'TER', 'WAT',
                'PKG', 'PFG', 'PNR', 'ESS', 'LYB', 'SNA', 'MAA', 'INCY', 'IFF', 'NWSA',
                'DOW', 'LNT', 'EVRG', 'LUV', 'BG', 'FTV', 'EXPD', 'APTV', 'ZBRA', 'HRL',
                'MAS', 'DECK', 'DPZ', 'BLDR', 'HOLX', 'BBY', 'CLX', 'OMC', 'COO', 'BALL',
                'KIM', 'ALLE', 'CHRW', 'BF-B', 'TXT', 'CNC', 'UDR', 'FDS', 'EG', 'CF',
                'JBHT', 'AVY', 'BEN', 'ARE', 'REG', 'SOLV', 'VTRS', 'IEX', 'BAX', 'DOC',
                'PAYC', 'NDSN', 'POOL', 'GNRC', 'SJM', 'JKHY', 'CPT', 'BXP', 'SWK', 'HAS',
                'WYNN', 'UHS', 'GL', 'HST', 'MRNA', 'SWKS', 'NCLH', 'PNW', 'AIZ', 'AKAM',
                'RVTY', 'HII', 'ALGN', 'WBA', 'MOS', 'TAP', 'AOS', 'MGM', 'CPB', 'ALB',
                'DVA', 'IPG', 'AES', 'IVZ', 'MTCH', 'CAG', 'MOH', 'EPAM', 'KMX', 'TECH',
                'DAY', 'HSIC', 'FRT', 'LKQ', 'MHK', 'CRL', 'LW', 'EMN', 'APA', 'MKTX',
                'CZR', 'ENPH'
            ]
            
            np.random.shuffle(sp500_tickers)
            valid_tickers = []
            progress_bar = st.progress(0, text="유효한 종목을 찾는 중...")
            max_valid_tickers = 50
            
            for i, t in enumerate(sp500_tickers):
                try:
                    stock = yf.Ticker(t)
                    df = stock.history(start='2025-01-01')
                    if not df.empty and len(df) > 50:
                        valid_tickers.append(t)
                        progress_text = f"유효한 종목 찾는 중... ({len(valid_tickers)}/{max_valid_tickers})"
                        progress_bar.progress(len(valid_tickers) / max_valid_tickers, text=progress_text)
                        if len(valid_tickers) >= max_valid_tickers: break
                except Exception: continue
            progress_bar.empty()
        
        if not valid_tickers:
             st.error("분석에 유효한 종목을 찾지 못했습니다. 다시 시도해주세요.")
             return

        selected_stocks, analyzed_count = [], 0
        analysis_progress = st.progress(0, text="분석 시작...")
        st.write("---")
        st.write(f"### 총 {len(valid_tickers)}개 종목 분석 시작")

        for ticker in valid_tickers:
            if len(selected_stocks) >= 5:
                st.info("최대 5개의 추천 종목을 찾았습니다. 분석을 중단합니다.")
                break
            
            analyzed_count += 1
            progress_text = f"분석 중: {ticker} ({analyzed_count}/{len(valid_tickers)})"
            analysis_progress.progress(analyzed_count / len(valid_tickers), text=progress_text)
            
            try:
                stock = yf.Ticker(ticker)
                chart_data = stock.history(start='2025-01-01')
                if chart_data.empty or len(chart_data) < 20:
                    st.warning(f"📈 {ticker}: 데이터가 부족하여 건너뜁니다.")
                    continue

                buf = io.BytesIO()
                mpf.plot(chart_data, type='candle', mav=(20), volume=True,
                         title=f"\n{ticker} 2025 YTD Chart", style='yahoo',
                         savefig=dict(fname=buf, dpi=150, format='png', bbox_inches='tight'))
                buf.seek(0)
                chart_image_bytes = buf.read()
                img_to_analyze = Image.open(io.BytesIO(chart_image_bytes))
                buf.close()

                # --- 입력 조건에 따라 동적으로 프롬프트 및 컨텐츠 생성 ---
                api_content = []
                prompt = "당신은 전문 차트 분석가입니다. "
                
                # 시나리오 1: 텍스트와 이미지 모두 사용
                if strategy_text and strategy_images:
                    prompt += f"""
                    첨부된 {len(strategy_images)}개의 '참고용 차트'와 '텍스트 전략'을 함께 고려하여 '분석 대상 차트'를 평가해주세요.
                    - 텍스트 전략: {strategy_text}
                    - 평가 기준: '참고용 차트'들과의 전반적인 시각적 유사성과 '텍스트 전략'과의 일치도를 모두 고려하여, 최종 점수를 0점에서 10점 사이에서 0.5점 단위로 매겨주세요.
                    - 가장 중요한 것은 두 조건 모두 만족하는지 여부입니다. 점수만 간결하게 숫자로 답변해주세요. (예: 8.5)
                    """
                    api_content = [prompt]
                    api_content.extend(strategy_images)
                    api_content.append(img_to_analyze)
                
                # 시나리오 2: 이미지만 사용
                elif strategy_images:
                    prompt += f"""
                    첨부된 {len(strategy_images)}개의 '참고용 차트'와 1개의 '분석 대상 차트'를 비교 분석해주세요.
                    '분석 대상 차트'가 '참고용 차트'들의 전반적인 패턴, 추세, 거래량 흐름 등과 얼마나 유사한지 시각적 유사성을 0점에서 10점 사이에서 0.5점 단위로 평가해주세요.
                    점수만 간결하게 숫자로 답변해주세요. (예: 8.5)
                    """
                    api_content = [prompt]
                    api_content.extend(strategy_images)
                    api_content.append(img_to_analyze)

                # 시나리오 3: 텍스트만 사용
                elif strategy_text:
                    chart_summary = f"종목: {ticker}, 현재가: ${chart_data['Close'].iloc[-1]:.2f}, 올해 변동률: {((chart_data['Close'].iloc[-1] / chart_data['Close'].iloc[0] - 1) * 100):.1f}%"
                    prompt += f"""
                    이 캔들차트('분석 대상 차트')를 보고 다음 '텍스트 전략'과 얼마나 일치하는지 0점에서 10점 사이에서 0.5점 단위로 평가해주세요.
                    - 텍스트 전략: {strategy_text}
                    - 종목 정보(참고용): {chart_summary}
                    - 첨부한 차트 이미지를 중점적으로 분석하여, 비판적이고 냉철하게 점수를 매겨주세요. 점수만 간결하게 숫자로 답변해주세요. (예: 8.5)
                    """
                    api_content = [prompt, img_to_analyze]
                
                response = model.generate_content(api_content)
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
