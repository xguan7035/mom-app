import streamlit as st
import urllib.request
import re

# 1. 网页配置：手机专属美金看板
st.set_page_config(
    page_title="妈妈的美股资产看板(美金版)", 
    page_icon="💵", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自定义手机端样式
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .profit-up { color: #00cc66; font-weight: bold; }
    .profit-down { color: #ff3333; font-weight: bold; }
    .card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 5px;
        border-left: 5px solid #1E90FF;
    }
    </style>
""", unsafe_allow_html=True)

st.title("❤️ 妈妈的专属美股看板")
st.caption("📱 手机专用版 · 结算货币：美金 (USD)")

# 2. 获取实时股价的函数（新浪美股接口）
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

# 3. 初始化持仓数据（初始只有 GOOG，没有 AAPL）
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {
        "GOOG": {"cost": 170.0, "shares": 10}
    }

# 4. ➕ 动态添加/修改持仓区域
with st.expander("➕ 点击添加或修改股票持仓", expanded=False):
    with st.form("add_stock_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("股票代码", value="NVDA").upper().strip()
        with col2:
            cst = st.number_input("成本价(USD $)", value=120.0, min_value=0.01)
        with col3:
            shr = st.number_input("持股数量", value=10, min_value=1, step=1)
        
        submit = st.form_submit_button("确认保存")
        if submit and sym:
            st.session_state.portfolio[sym] = {"cost": cst, "shares": shr}
            st.success(f"成功更新 {sym}！")
            st.rerun()

# 5. 核心计算逻辑
total_cost = 0.0
total_value = 0.0
total_daily_profit = 0.0
calculated_stocks = []

for sym, info in list(st.session_state.portfolio.items()):
    price, prev_close = get_sina_price(sym)
    if price:
        cost = info["cost"]
        shares = info["shares"]
        
        current_value = price * shares
        buy_cost = cost * shares
        
        profit = current_value - buy_cost
        profit_ratio = (profit / buy_cost) * 100 if buy_cost > 0 else 0
        
        daily_change = price - prev_close
        daily_profit = daily_change * shares
        daily_ratio = (daily_change / prev_close) * 100 if prev_close > 0 else 0
        
        total_cost += buy_cost
        total_value += current_value
        total_daily_profit += daily_profit
        
        calculated_stocks.append({
            "sym": sym,
            "price": price,
            "cost": cost,
            "shares": shares,
            "profit": profit,
            "profit_ratio": profit_ratio,
            "daily_profit": daily_profit,
            "daily_ratio": daily_ratio
        })

total_profit = total_value - total_cost
total_profit_ratio = (total_profit / total_cost) * 100 if total_cost > 0 else 0

# 🌟 6. 顶部资产仪表盘
st.write("### 📊 资产总览 (USD 美金)")
col_total1, col_total2 = st.columns(2)
with col_total1:
    color_class = "profit-up" if total_profit >= 0 else "profit-down"
    sign = "+" if total_profit >= 0 else ""
    st.markdown(f"历史总盈亏<br><span class='big-font {color_class}'>{sign}${total_profit:.2f} USD</span>", unsafe_allow_html=True)
    st.markdown(f"总盈亏比例：<span class='{color_class}'>{sign}{total_profit_ratio:.2f}%</span>", unsafe_allow_html=True)

with col_total2:
    color_class_d = "profit-up" if total_daily_profit >= 0 else "profit-down"
    sign_d = "+" if total_daily_profit >= 0 else ""
    st.markdown(f"今日总盈亏<br><span class='big-font {color_class_d}'>{sign_d}${total_daily_profit:.2f} USD</span>", unsafe_allow_html=True)

st.write("---")

# 📱 7. 单只股票卡片及🗑️删除功能
st.write("### 📈 我的持仓明细")
if not calculated_stocks:
    st.info("💡 当前列表中没有股票，请点击上方“➕”添加妈妈购买的股票！")
else:
    for s in calculated_stocks:
        p_color = "profit-up" if s["profit"] >= 0 else "profit-down"
        p_sign = "+" if s["profit"] >= 0 else ""
        
        d_color = "profit-up" if s["daily_profit"] >= 0 else "profit-down"
        d_sign = "+" if s["daily_profit"] >= 0 else ""
        
        # 渲染卡片内容
        st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 20px; font-weight: bold; color: #ffffff;">{s['sym']}</span>
                    <span style="font-size: 18px; font-weight: bold; color: #ffffff;">实时价: ${s['price']:.2f} USD</span>
                </div>
                <div style="margin-top: 5px; color: #aaaaaa; font-size: 14px;">
                    持仓: {s['shares']}股 | 成本价: ${s['cost']:.2f} USD
                </div>
                <hr style="margin: 8px 0; border-color: #555;">
                <div style="display: flex; justify-content: space-between; font-size: 14px;">
                    <div>今日波动: <span class="{d_color}">{d_sign}${s['daily_profit']:.2f} ({d_sign}{s['daily_ratio']:.2f}%)</span></div>
                    <div>累计盈亏: <span class="{p_color}">{p_sign}${s['profit']:.2f} ({p_sign}{s['profit_ratio']:.2f}%)</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 🗑️ 每只股票下方的专属删除按钮
        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("🗑️ 删除", key=f"del_{s['sym']}"):
                del st.session_state.portfolio[s['sym']]
                st.rerun()
