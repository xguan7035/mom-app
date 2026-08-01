import streamlit as st
import streamlit.components.v1 as components
import urllib.request
import re
import json

# 1. 页面配置
st.set_page_config(
    page_title="妈妈的尊享美股看板", 
    page_icon="👑", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 自定义大字号高对比度 CSS
st.markdown("""
    <style>
    .big-font { font-size:26px !important; font-weight: bold; }
    .profit-up { color: #00ff66 !important; font-weight: bold; font-size: 20px !important; }
    .profit-down { color: #ff5555 !important; font-weight: bold; font-size: 20px !important; }
    
    .card {
        background-color: #181924;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid #3b3d54;
        border-left: 6px solid #00d2ff;
    }
    .cost-box {
        background-color: #252836;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .cost-title { color: #aaaaaa !important; font-size: 14px !important; }
    .cost-val { color: #ffd700 !important; font-size: 22px !important; font-weight: bold !important; }
    .label-text { color: #ffffff !important; font-size: 15px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.title("👑 妈妈尊享·美股智能看板")
st.caption("📱 1500元高级售后版 · 实时成本保存 · 零乱码")

# 3. 数据存储（利用 Streamlit query_params 进行轻量级云端 URL 持久化，或持久化 session）
# 确保没有默认干扰股票！只有妈妈自己输入的股票！
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

# 4. 获取新浪实时行情
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

# 5. ➕ 管理我的持仓（添加 / 修改）
with st.expander("📝 点击这里：新增或修改股票持仓", expanded=not bool(st.session_state.portfolio)):
    with st.form("set_stock_form"):
        st.subheader("设置股票成本与股数")
        sym = st.text_input("股票代码 (如 NVDA / AAPL / GOOG)", value="").upper().strip()
        cost = st.number_input("我的买入成本价 ($)", value=0.0, min_value=0.0, step=0.1)
        shares = st.number_input("持有股数", value=0, min_value=0, step=1)
        
        save_btn = st.form_submit_button("💾 保存并锁定成本")
        if save_btn and sym:
            if shares > 0 and cost > 0:
                st.session_state.portfolio[sym] = {"cost": cost, "shares": shares}
                st.success(f"已成功为您保存 {sym}！成本价 ${cost}，{shares}股。")
            else:
                st.warning("请输入有效的成本价和股数！")
            st.rerun()

# 6. 计算与显示持仓
total_cost = 0.0
total_value = 0.0
total_daily_profit = 0.0
calculated_stocks = []

for sym, info in list(st.session_state.portfolio.items()):
    cost = info["cost"]
    shares = info["shares"]
    price, prev_close = get_sina_price(sym)
    
    if price:
        stock_cost = cost * shares
        current_val = price * shares
        profit = current_val - stock_cost
        profit_ratio = (profit / stock_cost) * 100 if stock_cost > 0 else 0
        
        daily_change = price - prev_close
        daily_profit = daily_change * shares
        daily_ratio = (daily_change / prev_close) * 100 if prev_close > 0 else 0
        
        total_cost += stock_cost
        total_value += current_val
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

# 📊 7. 顶部大盘展示
if calculated_stocks:
    rmb_profit = total_profit * usd_rate
    rmb_daily = total_daily_profit * usd_rate
    
    st.write("### 📊 我的总资产大盘")
    c1, c2 = st.columns(2)
    with c1:
        color = "profit-up" if total_profit >= 0 else "profit-down"
        sign = "+" if total_profit >= 0 else ""
        st.markdown(f"历史总盈亏<br><span class='big-font {color}'>{sign}${total_profit:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='label-text'>约合: </span><span class='{color}'>{sign}¥{rmb_profit:.2f}</span>", unsafe_allow_html=True)
    with c2:
        d_color = "profit-up" if total_daily_profit >= 0 else "profit-down"
        d_sign = "+" if total_daily_profit >= 0 else ""
        st.markdown(f"今日波动<br><span class='big-font {d_color}'>{d_sign}${total_daily_profit:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='label-text'>今日约合: </span><span class='{d_color}'>{d_sign}¥{rmb_daily:.2f}</span>", unsafe_allow_html=True)
    st.write("---")

# 📱 8. 详细列表展示
st.write("### 📈 持仓卡片")
if not calculated_stocks:
    st.info("👇 妈妈，目前没有持仓数据，请点击上方“新增或修改股票持仓”设置您的成本价！")
else:
    for s in calculated_stocks:
        p_color = "profit-up" if s["profit"] >= 0 else "profit-down"
        p_sign = "+" if s["profit"] >= 0 else ""
        d_color = "profit-up" if s["daily_profit"] >= 0 else "profit-down"
        d_sign = "+" if s["daily_profit"] >= 0 else ""
        
        st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 28px; font-weight: bold; color: #ffffff;">{s['sym']}</span>
                    <span style="font-size: 22px; font-weight: bold; color: #ffffff;">当前价: ${s['price']:.2f}</span>
                </div>
                <div class="cost-box">
                    <div class="cost-title">📌 您的锁定成本价</div>
                    <div class="cost-val">${s['cost']:.2f} USD <span style="font-size: 16px; color: #ffffff;">(持有 {s['shares']} 股)</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                    <div>
                        <div class="label-text">今日收益</div>
                        <div class="{d_color}">{d_sign}${s['daily_profit']:.2f} ({d_sign}{s['daily_ratio']:.2f}%)</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="label-text">累计总盈亏</div>
                        <div class="{p_color}">{p_sign}${s['profit']:.2f} ({p_sign}{s['profit_ratio']:.2f}%)</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col_del, col_space = st.columns([1, 3])
        with col_del:
            if st.button(f"🗑️ 删除 {s['sym']}", key=f"del_{s['sym']}"):
                del st.session_state.portfolio[s['sym']]
                st.rerun()

        # ミニ走势图
        tv_mini_html = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_mini_{s['sym']}"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%",
            "height": 180,
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
        components.html(tv_mini_html, height=185)
        st.write("---")
