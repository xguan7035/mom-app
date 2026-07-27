import streamlit as st
import urllib.request
import re
import yfinance as yf
import plotly.graph_objects as go

# 1. 页面配置
st.set_page_config(
    page_title="妈妈的美股资产看板", 
    page_icon="💵", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 自定义手机端样式
st.markdown("""
    <style>
    .big-font { font-size:26px !important; font-weight: bold; }
    .profit-up { color: #00ff66 !important; font-weight: bold; font-size: 18px !important; }
    .profit-down { color: #ff5555 !important; font-weight: bold; font-size: 18px !important; }
    
    .card {
        background-color: #181924;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid #3b3d54;
        border-left: 6px solid #00d2ff;
    }
    .highlight-text {
        color: #ffd700 !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }
    .label-text {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("❤️ 妈妈的专属美股看板")
st.caption("📱 手机大字走势图版 · 结算货币：美金 (USD)")

# 3. 新浪实时行情获取函数
def get_sina_price(symbol):
    sina_symbol = f"gb_{symbol.lower().strip()}"
    url = f"https://hq.sinajs.cn/list={sina_symbol}"
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_text = response.read().decode('gbk')
            data_match = re.search(r'"([^"]*)"', res_text)
            if data_match and data_match.group(1):
                data_list = data_match.group(1).split(',')
                if float(data_list[1]) > 0:
                    return float(data_list[1]), float(data_list[26])
    except:
        pass
    return None, None

# 4. 初始化持仓数据
if "records" not in st.session_state:
    st.session_state.records = {
        "GOOG": [
            {"price": 170.0, "shares": 10}
        ]
    }

# 5. ➕ 记一笔买入 / 加仓区域
with st.expander("➕ 记一笔买入 / 加仓（系统自动评估均价）", expanded=False):
    with st.form("add_buy_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("股票代码", value="NVDA").upper().strip()
        with col2:
            cst = st.number_input("本次买入价($)", value=100.0, min_value=0.01)
        with col3:
            shr = st.number_input("本次买入股数", value=10, min_value=1, step=1)
        
        submit = st.form_submit_button("确认记录本次买入")
        if submit and sym:
            if sym not in st.session_state.records:
                st.session_state.records[sym] = []
            st.session_state.records[sym].append({"price": cst, "shares": shr})
            st.success(f"成功记录 {sym} 本次买入！")
            st.rerun()

# 6. 核心计算逻辑
total_cost = 0.0
total_value = 0.0
total_daily_profit = 0.0
calculated_stocks = []

for sym, buy_list in list(st.session_state.records.items()):
    if not buy_list:
        continue
    
    stock_total_cost = sum(item["price"] * item["shares"] for item in buy_list)
    stock_total_shares = sum(item["shares"] for item in buy_list)
    avg_cost = stock_total_cost / stock_total_shares if stock_total_shares > 0 else 0.0
    
    price, prev_close = get_sina_price(sym)
    if price:
        current_value = price * stock_total_shares
        profit = current_value - stock_total_cost
        profit_ratio = (profit / stock_total_cost) * 100 if stock_total_cost > 0 else 0
        
        daily_change = price - prev_close
        daily_profit = daily_change * stock_total_shares
        daily_ratio = (daily_change / prev_close) * 100 if prev_close > 0 else 0
        
        total_cost += stock_total_cost
        total_value += current_value
        total_daily_profit += daily_profit
        
        calculated_stocks.append({
            "sym": sym,
            "price": price,
            "avg_cost": avg_cost,
            "shares": stock_total_shares,
            "buy_count": len(buy_list),
            "profit": profit,
            "profit_ratio": profit_ratio,
            "daily_profit": daily_profit,
            "daily_ratio": daily_ratio
        })

total_profit = total_value - total_cost
total_profit_ratio = (total_profit / total_cost) * 100 if total_cost > 0 else 0

# 🌟 7. 顶部仪表盘
st.write("### 📊 资产总览 (USD 美金)")
col_total1, col_total2 = st.columns(2)
with col_total1:
    color_class = "profit-up" if total_profit >= 0 else "profit-down"
    sign = "+" if total_profit >= 0 else ""
    st.markdown(f"历史总盈亏<br><span class='big-font {color_class}'>{sign}${total_profit:.2f} USD</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='label-text'>总盈亏比例：</span><span class='{color_class}'>{sign}{total_profit_ratio:.2f}%</span>", unsafe_allow_html=True)

with col_total2:
    color_class_d = "profit-up" if total_daily_profit >= 0 else "profit-down"
    sign_d = "+" if total_daily_profit >= 0 else ""
    st.markdown(f"今日总盈亏<br><span class='big-font {color_class_d}'>{sign_d}${total_daily_profit:.2f} USD</span>", unsafe_allow_html=True)

st.write("---")

# 📱 8. 持仓明细展示与走势图
st.write("### 📈 我的持仓明细与走势图")
if not calculated_stocks:
    st.info("💡 当前没有记录，请点击上方“➕”记一笔买入！")
else:
    for s in calculated_stocks:
        p_color = "profit-up" if s["profit"] >= 0 else "profit-down"
        p_sign = "+" if s["profit"] >= 0 else ""
        
        d_color = "profit-up" if s["daily_profit"] >= 0 else "profit-down"
        d_sign = "+" if s["daily_profit"] >= 0 else ""
        
        # 股票概览卡片
        st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 24px; font-weight: bold; color: #ffffff;">{s['sym']}</span>
                    <span style="font-size: 20px; font-weight: bold; color: #ffffff;">实时价: ${s['price']:.2f}</span>
                </div>
                <div style="margin-top: 8px; margin-bottom: 4px;">
                    <span class="highlight-text">📐 评估均价: ${s['avg_cost']:.2f} USD</span>
                    <span style="color: #ffffff; font-size: 16px; font-weight: bold; margin-left: 10px;">| 持仓: {s['shares']}股</span>
                </div>
                <hr style="margin: 10px 0; border-color: #555577;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div class="label-text">今日波动</div>
                        <div class="{d_color}">{d_sign}${s['daily_profit']:.2f}<br>({d_sign}{s['daily_ratio']:.2f}%)</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="label-text">累计盈亏</div>
                        <div class="{p_color}">{p_sign}${s['profit']:.2f}<br>({p_sign}{s['profit_ratio']:.2f}%)</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 📈 走势图展开折叠面板（带有 1M, 3M, 6M, 1Y 时间选择）
        with st.expander(f"📉 查看 {s['sym']} 历史价格走势图", expanded=True):
            period = st.radio(
                "选择显示区间：", 
                ["1个月", "3个月", "6个月", "1年"], 
                horizontal=True, 
                key=f"period_{s['sym']}"
            )
            
            period_map = {"1个月": "1mo", "3个月": "3mo", "6个月": "6mo", "1年": "1y"}
            
            try:
                # 获取历史数据
                ticker = yf.Ticker(s['sym'])
                df = ticker.history(period=period_map[period])
                
                if not df.empty:
                    # 绘制高清暗黑风格折线走势图
                    fig = go.Figure()
                    
                    # 决定线条颜色（根据首尾涨跌）
                    line_color = "#00ff66" if df['Close'].iloc[-1] >= df['Close'].iloc[0] else "#ff5555"
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, 
                        y=df['Close'], 
                        mode='lines',
                        name='收盘价',
                        line=dict(color=line_color, width=2.5),
                        fill='tozeroy',
                        fillcolor='rgba(0, 255, 102, 0.1)' if line_color == "#00ff66" else 'rgba(255, 85, 85, 0.1)'
                    ))
                    
                    fig.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=260,
                        xaxis=dict(showgrid=False, font=dict(color='white')),
                        yaxis=dict(showgrid=True, gridcolor='#333344', font=dict(color='white')),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("暂未获取到走势图数据。")
            except Exception as e:
                st.error("走势图加载失败，请检查网络或稍后再试。")

        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("🗑️ 清空", key=f"del_{s['sym']}"):
                del st.session_state.records[s['sym']]
                st.rerun()
        st.write("---")
