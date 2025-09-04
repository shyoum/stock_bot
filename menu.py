import streamlit as st

from app import main as app_main

# 자동 생성된 페이지 메뉴
pages = {
    "종목 검색": app_main,
}

def show_menu():
    """사이드바에 메뉴 표시"""
    st.sidebar.title("📋 메뉴")
    
    if pages:
        selected_page = st.sidebar.selectbox(
            "페이지 선택",
            list(pages.keys())
        )
        
        if selected_page:
            pages[selected_page]()
    else:
        st.sidebar.write("등록된 페이지가 없습니다.")

if __name__ == "__main__":
    show_menu()
