import streamlit as st
import urllib.request
import re

# 1. 页面配置
st.set_page_config(
    page_title="妈妈的美股资产看板", 
    page_icon="💵", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 自定义手机端样式：针对高对比度、大字体优化
st.markdown("""
    <style>
    .big-font { font-size:26px !important; font-weight: bold; }
    .profit-up { color: #00ff66; font-weight: bold; font-size: 16px; }
    .profit-down { color: #ff4d4d; font-weight: bold; font-size: 16px; }
    .card {
        background-color: #1e1e2e;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid #313244;
        border-left: 6px solid #00d2ff;
    }
    .highlight-text {
        color: #ffd700 !important; /* 亮金色高亮 */
        font-size: 16px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("❤️ 妈妈的专属美股看板")
st.caption("📱 手机大字清晰版 · 结算货币：美金 (USD)")

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
    st.markdown(f"总盈亏比例：<span class='{color_class}'>{sign}{total_profit_ratio:.2f}%</span>", unsafe_allow_html=True)

with col_total2:
    color_class_d = "profit-up" if total_daily_profit >= 0 else "profit-down"
    sign_d = "+" if total_daily_profit >= 0 else ""
    st.markdown(f"今日总盈亏<br><span class='big-font {color_class_d}'>{sign_d}${total_daily_profit:.2f} USD</span>", unsafe_allow_html=True)

st.write("---")

# 📱 8. 单只股票卡片（大字高对比度版本）
st.write("### 📈 我的持仓明细")
if not calculated_stocks:
    st.info("💡 当前没有记录，请点击上方“➕”记一笔买入！")
else:
    for s in calculated_stocks:
        p_color = "profit-up" if s["profit"] >= 0 else "profit-down"
        p_sign = "+" if s["profit"] >= 0 else ""
        
        d_color = "profit-up" if s["daily_profit"] >= 0 else "profit-down"
        d_sign = "+" if s["daily_profit"] >= 0 else ""
        
        # 渲染大字卡片
        st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 22px; font-weight: bold; color: #ffffff;">{s['sym']}</span>
                    <span style="font-size: 19px; font-weight: bold; color: #ffffff;">实时价: ${s['price']:.2f}</span>
                </div>
                <div style="margin-top: 8px; margin-bottom: 4px;">
                    <span class="highlight-text">📐 评估均价: ${s['avg_cost']:.2f} USD</span>
                    <span style="color: #ffffff; font-size: 15px; font-weight: bold; margin-left: 10px;">| 持仓: {s['shares']}股</span>
                </div>
                <hr style="margin: 10px 0; border-color: #444466;">
                <div style="display: flex; justify-content: space-between;">
                    <div>今日波动:<br><span class="{d_color}">{d_sign}${s['daily_profit']:.2f} ({d_sign}{s['daily_ratio']:.2f}%)</span></div>
                    <div>累计盈亏:<br><span class="{p_color}">{p_sign}${s['profit']:.2f} ({p_sign}{s['profit_ratio']:.2f}%)</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("🗑️ 清空", key=f"del_{s['sym']}"):
                del st.session_state.records[s['sym']]
                st.rerun()
