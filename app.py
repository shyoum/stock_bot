import streamlit as st
import yfinance as yf

def main():
    st.title("📈 종목 검색")
    ticker = st.text_input("티커(종목코드) 입력", placeholder="AAPL, TSLA, 005930 등")

    if ticker:
        try:
            ticker = ticker.upper()
            if ticker.isdigit():
                ticker = f"{ticker}.KS"
            
            stock = yf.Ticker(ticker)
            recent_data = stock.history(period="1mo").tail(7)
            chart_data = stock.history(period="6mo")
            
            if not recent_data.empty and not chart_data.empty:
                st.dataframe(recent_data[['Open', 'High', 'Low', 'Close', 'Volume']])
                
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.02, row_heights=[0.7, 0.3])
                
                fig.add_trace(go.Candlestick(x=chart_data.index,
                                            open=chart_data['Open'],
                                            high=chart_data['High'],
                                            low=chart_data['Low'],
                                            close=chart_data['Close'],
                                            increasing_line_color='red',
                                            decreasing_line_color='blue',
                                            increasing_fillcolor='red',
                                            decreasing_fillcolor='blue',
                                            name="Price"), row=1, col=1)
                
                volume_colors = []
                for i in range(len(chart_data)):
                    if i == 0:
                        volume_colors.append('gray')
                    else:
                        if chart_data['Volume'].iloc[i] >= chart_data['Volume'].iloc[i-1]:
                            volume_colors.append('red')
                        else:
                            volume_colors.append('blue')
                            
                fig.add_trace(go.Bar(x=chart_data.index, y=chart_data['Volume'],
                                    name="Volume", marker_color=volume_colors), row=2, col=1)
                
                x_labels = []
                x_vals = []
                seen_months = set()
                
                for date in chart_data.index:
                    month = date.month
                    if month not in seen_months:
                        if date.day <= 15:
                            x_labels.append(str(month))
                            x_vals.append(date)
                        seen_months.add(month)
                
                fig.update_layout(title=f"{ticker} 6개월 캔들차트", 
                                 xaxis_rangeslider_visible=False,
                                 hovermode='x unified')
                fig.update_xaxes(type='category', ticktext=x_labels, tickvals=x_vals)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("데이터를 찾을 수 없습니다")
        except Exception as e:
            st.error(f"에러: {e}")

if __name__ == "__main__":
    from menu import show_menu
    show_menu()