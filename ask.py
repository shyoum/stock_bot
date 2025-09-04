import streamlit as st
import google.generativeai as genai

def main():
    st.title("🧠 전략 분석기")
    
    genai.configure(api_key="AIzaSyBdNmMTS_p19O7Vna5ldyAiFGDL1QVVMsg")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    strategy = st.text_area("전략을 입력하세요:", height=200)
    
    if st.button("분석하기") and strategy:
        with st.spinner("분석 중..."):
            try:
                response = model.generate_content(strategy)
                st.markdown("### 분석 결과")
                st.write(response.text)
            except Exception as e:
                st.error(f"오류: {e}")

if __name__ == "__main__":
    from menu import show_menu
    show_menu()