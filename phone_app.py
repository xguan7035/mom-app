import streamlit as st
import streamlit.components.v1 as components
import urllib.request
import re
import json

# 1. 页面配置
st.set_page_config(page_title="妈妈尊享美股看板", page_icon="👑", layout="centered")

# ☁️ 云端数据库配置 (去 jsonbin.io 申请免费 API)
BIN_ID = "6a6e17b93919920ec48559ef"
API_KEY = "$2a$10$2Mr4re2G.zDW2REgzdTaheK8pNC0YWtcdBzBti4zunXqf6nySkqda"

# 云端读取
def load_from_cloud():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    req = urllib.request.Request(url, headers={"X-Master-Key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("record", {})
    except:
        return {}

# 云端保存
def save_to_cloud(data):
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": API_KEY
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='PUT')
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        st.error(f"云端同步失败: {e}")

# 初始化数据：优先从云端拉取
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_from_cloud()

# 样式定义
st.markdown("""
    <style>
    .big-font { font-size:26px !important; font-weight: bold; }
    .profit-up { color: #00ff66 !important; font-weight: bold; font-size: 20px !important; }
    .profit-down { color: #ff5555 !important; font-weight: bold; font-size: 20px !important; }
    .card { background-color: #181924; padding: 16px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #3b3d54; }
    </style>
""", unsafe_allow_html=True)

st.title("👑 妈妈尊享·美股智能看板")
st.caption("☁️ 云端实时同步版 · 退出后台数据永久保存")

# 行情获取函数
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

# 修改/保存持仓
with st.expander("📝 录入/更新持仓（修改后云端自动同步）"):
    with st.form("add_form"):
        sym = st.text_input("股票代码 (如 NVDA/AAPL)").upper().strip()
        cost = st.number_input("买入成本单价 ($)", min_value=0.01)
        shares = st.number_input("持有股数", min_value=1, step=1)
        
        if st.form_submit_button("💾 确认并同步到云端"):
            if sym and cost > 0 and shares > 0:
                st.session_state.portfolio[sym] = {"cost": cost, "shares": shares}
                save_to_cloud(st.session_state.portfolio) # 写入云端
                st.success(f"{sym} 已成功同步到云端！")
                st.rerun()

# 页面展示逻辑
if not st.session_state.portfolio:
    st.info("💡 当前云端暂无数据，请在上方录入股票！")
else:
    for sym, info in list(st.session_state.portfolio.items()):
        price, prev_close = get_sina_price(sym)
        if price:
            cost = info["cost"]
            shares = info["shares"]
            profit = (price - cost) * shares
            p_color = "profit-up" if profit >= 0 else "profit-down"
            
            st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:24px; font-weight:bold; color:#fff;">{sym}</span>
                        <span style="font-size:20px; color:#fff;">现价: ${price:.2f}</span>
                    </div>
                    <div style="color:#aaa; margin-top:5px;">成本: ${cost:.2f} | 持仓: {shares} 股</div>
                    <div class="{p_color}" style="margin-top:8px;">持仓盈亏: ${profit:.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗑️ 删除 {sym}", key=f"del_{sym}"):
                del st.session_state.portfolio[sym]
                save_to_cloud(st.session_state.portfolio)
                st.rerun()
