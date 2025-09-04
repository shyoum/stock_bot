import streamlit as st
import google.generativeai as genai
from PIL import Image

def main():
    st.title("🧠 전략 분석기")
    
    genai.configure(api_key="AIzaSyBdNmMTS_p19O7Vna5ldyAiFGDL1QVVMsg")
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    strategy = st.text_area("전략을 입력하세요:", height=200)
    uploaded_image = st.file_uploader("이미지 업로드 (선택사항)", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_image:
        st.image(uploaded_image, width=300)
    
    if st.button("분석하기") and strategy:
        with st.spinner("분석 중..."):
            try:
                content = [strategy]
                if uploaded_image:
                    image = Image.open(uploaded_image)
                    content.append(image)
                
                response = model.generate_content(content)
                st.markdown("### 분석 결과")
                st.write(response.text)
            except Exception as e:
                st.error(f"오류: {e}")

if __name__ == "__main__":
    from menu import show_menu
    show_menu()