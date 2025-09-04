import streamlit as st
import requests
import json

def main():
    """투자전략 기반 종목추천 메인 함수"""
    st.title("🎯 투자전략 기반 종목추천")
    
    strategy = st.text_input("투자전략을 입력하세요", placeholder="예: 배당수익률이 높은 안정적인 대형주")
    
    if strategy and st.button("종목 추천 받기"):
        with st.spinner("AI가 종목을 분석하고 있습니다..."):
            try:
                result = get_stock_recommendations(strategy)
                if result:
                    st.success("추천 완료!")
                    st.json(result)
                else:
                    st.error("추천 결과를 받을 수 없습니다")
            except Exception as e:
                st.error(f"오류 발생: {e}")

def get_stock_recommendations(strategy):
    """제미나이 API로 종목 추천 받기"""
    api_key = "AIzaSyBdNmMTS_p19O7Vna5ldyAiFGDL1QVVMsg"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = strategy
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return None

if __name__ == "__main__":
    from menu import show_menu
    show_menu()