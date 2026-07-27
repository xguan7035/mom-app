import streamlit as st
import streamlit.components.v1 as components
import urllib.request
import re

# 1. 页面配置
st.set_page_config(
    page_title="妈妈的尊享美股资产看板", 
    page_icon="👑", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 自定义高对比度、大字、尊享专业 CSS 样式
st.markdown("""
    <style>
    .big-font { font-size:26px !important; font-weight: bold; }
    .profit-up { color: #00ff66 !important; font-weight: bold; font-size: 18px !important; }
    .profit-down { color: #ff5555 !important; font-weight: bold; font-size: 18px !important; }
    
    .card {
        background-color: #181924;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid #3b3d54;
        border-left: 6px solid #00d2ff;
    }
    .ai-banner {
        background: linear-gradient(135deg, #2b1055, #7597de);
        padding: 12px 16px;
        border-radius: 10px;
        color: #ffffff;
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 15px;
    }
    .avg-price-title {
        color: #aaaaaa !important;
        font-size: 14px !important;
    }
    .avg-price-val {
        color: #ffd700 !important;
        font-size: 22px !important;
        font-weight: bold !important;
    }
    .label-text {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👑 妈妈尊享·美股智能看板")
st.caption("📱 自动评估均价 · 多次买入管理 · 双币种折算")

# 3. 新浪实时行情与汇率获取
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

# 获取美元对人民币大约汇率（默认 7.25，带容错）
def get_usd_cny_rate():
    try:
        url = "https://hq.sinajs.cn/list=fx_susdcny"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            res_text = response.read().decode('gbk')
            data_match = re.search(r'"([^"]*)"', res_text)
            if data_match and data_match.group(1):
                return float(data_match.group(1).split(',')[1])
    except:
        pass
    return 7.25

usd_rate = get_usd_cny_rate()

# 4. 初始化持仓数据
if "records" not in st.session_state:
    st.session_state.records = {
        "GOOG": [
            {"price": 160.0, "shares": 10},
            {"price": 175.0, "shares": 5}
        ]
    }

# 5. ➕ 建仓/添加新股票
with st.expander("➕ 添加新股票 / 建仓", expanded=False):
    with st.form("add_new_stock_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("股票代码", value="NVDA").upper().strip()
        with col2:
            cst = st.number_input("买入单价($)", value=100.0, min_value=0.01)
        with col3:
            shr = st.number_input("买入股数", value=10, min_value=1, step=1)
        
        submit = st.form_submit_button("确认建仓")
        if submit and sym:
            if sym not in st.session_state.records:
                st.session_state.records[sym] = []
            st.session_state.records[sym].append({"price": cst, "shares": shr})
            st.success(f"成功添加股票 {sym}！")
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
            "buy_list": buy_list,
            "profit": profit,
            "profit_ratio": profit_ratio,
            "daily_profit": daily_profit,
            "daily_ratio": daily_ratio
        })

total_profit = total_value - total_cost
total_profit_ratio = (total_profit / total_cost) * 100 if total_cost > 0 else 0

# 🌟 7. 智能温馨 AI 简报（专业体贴拉满）
rmb_profit = total_profit * usd_rate
if total_profit >= 0:
    ai_msg = f"☀️ 妈妈今天心情不错！当前累计盈利 ${total_profit:.2f} USD（约合人民币 ¥{rmb_profit:.2f} 元），继续保持！"
else:
    ai_msg = f"🌙 股市偶有波动，当前累计调整 ${abs(total_profit):.2f} USD（约合人民币 ¥{abs(rmb_profit):.2f} 元），保持好心态！"

st.markdown(f'<div class="ai-banner">{ai_msg}</div>', unsafe_allow_html=True)

# 📊 8. 顶部资产仪表盘（含人民币参考折算）
st.write("### 📊 资产大盘")
col_total1, col_total2 = st.columns(2)
with col_total1:
    color_class = "profit-up" if total_profit >= 0 else "profit-down"
    sign = "+" if total_profit >= 0 else ""
    st.markdown(f"历史总盈亏<br><span class='big-font {color_class}'>{sign}${total_profit:.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='label-text'>约合人民币：</span><span class='{color_class}'>{sign}¥{rmb_profit:.2f}</span>", unsafe_allow_html=True)

with col_total2:
    color_class_d = "profit-up" if total_daily_profit >= 0 else "profit-down"
    sign_d = "+" if total_daily_profit >= 0 else ""
    rmb_daily = total_daily_profit * usd_rate
    st.markdown(f"今日总波动<br><span class='big-font {color_class_d}'>{sign_d}${total_daily_profit:.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='label-text'>今日约合：</span><span class='{color_class_d}'>{sign_d}¥{rmb_daily:.2f}</span>", unsafe_allow_html=True)

st.caption(f"当前参考汇率: 1 USD ≈ {usd_rate:.2f} CNY")
st.write("---")

# 📱 9. 股票明细卡片
st.write("### 📈 我的持仓明细与买入管理")
if not calculated_stocks:
    st.info("💡 当前没有记录，请点击上方“➕”建仓添加股票！")
else:
    for s in calculated_stocks:
        p_color = "profit-up" if s["profit"] >= 0 else "profit-down"
        p_sign = "+" if s["profit"] >= 0 else ""
        
        d_color = "profit-up" if s["daily_profit"] >= 0 else "profit-down"
        d_sign = "+" if s["daily_profit"] >= 0 else ""
        
        # 卡片整体
        st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 26px; font-weight: bold; color: #ffffff;">{s['sym']}</span>
                    <span style="font-size: 20px; font-weight: bold; color: #ffffff;">实时价: ${s['price']:.2f}</span>
                </div>
                <div style="margin-top: 10px; background-color: #252836; padding: 10px; border-radius: 8px;">
                    <div class="avg-price-title">📐 系统加权评估均价 (分 {len(s['buy_list'])} 次买入)</div>
                    <div class="avg-price-val">${s['avg_cost']:.2f} USD <span style="font-size: 16px; color: #ffffff; font-weight: normal;">| 持仓: {s['shares']} 股</span></div>
                </div>
                <hr style="margin: 12px 0; border-color: #555577;">
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
        
        # 加仓与买入明细折叠菜单
        c1, c2 = st.columns([3, 1])
        with c1:
            with st.expander(f"➕ 加仓 {s['sym']} / 查看 {len(s['buy_list'])} 次买入明细"):
                st.write("**📝 历史分批买入记录：**")
                for idx, b in enumerate(s['buy_list']):
                    st.caption(f"第 {idx+1} 笔: ${b['price']:.2f} USD × {b['shares']} 股")
                
                st.write("**➕ 记录新一笔加仓：**")
                with st.form(f"buy_more_form_{s['sym']}"):
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        add_price = st.number_input("加仓买入价($)", value=s['price'], key=f"p_{s['sym']}")
                    with col_b2:
                        add_shares = st.number_input("加仓买入股数", value=10, min_value=1, key=f"s_{s['sym']}")
                    
                    if st.form_submit_button("确认加仓（自动评估最新均价）"):
                        st.session_state.records[s['sym']].append({"price": add_price, "shares": add_shares})
                        st.success(f"加仓成功！{s['sym']} 评估均价已更新。")
                        st.rerun()

        with c2:
            if st.button("🗑️ 清空", key=f"del_{s['sym']}"):
                del st.session_state.records[s['sym']]
                st.rerun()

        # 精简走势图
        tv_mini_html = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_mini_{s['sym']}"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%",
            "height": 200,
            "symbol": "{s['sym']}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "2",
            "locale": "zh_CN",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_top_toolbar": true,
            "hide_legend": true,
            "save_image": false,
            "container_id": "tradingview_mini_{s['sym']}"
          }});
          </script>
        </div>
        """
        components.html(tv_mini_html, height=205)
        st.write("---")
