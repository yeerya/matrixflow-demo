import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json

# --- 页面配置 ---
st.set_page_config(page_title="MatrixFlow 爆款脚本生成器", page_icon="🚀", layout="wide")

# --- 初始化 Session State (关键修复：防止数据丢失) ---
if 'product_name' not in st.session_state:
    st.session_state.product_name = ""
if 'product_data' not in st.session_state:
    st.session_state.product_data = ""

# --- 核心功能函数 ---
def get_html_content(url):
    """简单的网页抓取"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.title.string.strip() if soup.title else "未找到标题"
            # 简单清洗文本，去除多余空格
            text = soup.get_text(separator="\n", strip=True)[:3000] 
            return {"title": title, "content": text, "success": True}
        else:
            return {"success": False, "error": f"状态码: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_script_with_ai(product_name, features, api_key, base_url, model_name):
    """调用 AI 生成脚本"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    prompt = f"""
    你是一个短视频带货脚本专家。请根据以下商品信息，创作2个不同风格的爆款脚本。

    【商品名称】：{product_name}
    【核心卖点/详情】：{features}

    【要求】：
    1. 输出格式必须是严格的 JSON 格式。
    2. 包含两个脚本：
       - 脚本A：痛点直击型 (强调不买的后果，通过恐惧/焦虑切入)
       - 脚本B：性价比/爽感型 (强调超值、演示效果、视觉冲击)
    3. 每个脚本包含 3-4 个分镜 (Scene)。
    4. 每个分镜包含：
       - time: 时间 (如 0-3s)
       - visual: 画面描述 (给摄影师看的)
       - audio: 台词/旁白 (口语化，有煽动性)

    【JSON输出模版】：
    {{
      "analysis": "这里简短分析一下商品的痛点和受众...",
      "scripts": [
        {{
          "style": "🔥 痛点直击型",
          "hook": "一句话吸引注意",
          "scenes": [
             {{"time": "0-3s", "visual": "...", "audio": "..."}}
          ]
        }},
        {{
          "style": "💰 性价比/爽感型",
          "hook": "...",
          "scenes": []
        }}
      ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的短视频编导，擅长通过JSON格式输出脚本。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.title("⚙️ 设置")
    st.markdown("### 1. AI 模型配置")
    api_key = st.text_input("API Key", type="password", placeholder="sk-...")
    
    base_url_option = st.selectbox(
        "API 厂商 (Base URL)",
        ["OpenAI 官方 (api.openai.com)", "DeepSeek (api.deepseek.com)", "自定义"]
    )
    
    if base_url_option == "OpenAI 官方 (api.openai.com)":
        base_url = "https://api.openai.com/v1"
        default_model = "gpt-4o"
    elif base_url_option == "DeepSeek (api.deepseek.com)":
        base_url = "https://api.deepseek.com"
        default_model = "deepseek-chat"
    else:
        base_url = st.text_input("输入自定义 Base URL", "https://api.openai.com/v1")
        default_model = "gpt-3.5-turbo"

    model_name = st.text_input("模型名称", default_model)

# --- 主界面 ---
st.title("🎬 MatrixFlow 脚本生成器 (正式版)")

# 1. 获取商品信息
st.markdown("### 第一步：输入商品")
input_method = st.radio("选择输入方式", ["🔗 粘贴链接 (尝试抓取)", "✍️ 手动输入 (最稳)"])

if input_method == "🔗 粘贴链接 (尝试抓取)":
    url = st.text_input("商品链接 (京东/淘宝/拼多多)")
    if st.button("尝试抓取"):
        if not url:
            st.warning("请先输入链接！")
        else:
            with st.spinner("🕷️ 正在尝试访问..."):
                res = get_html_content(url)
                if res['success']:
                    # 关键修改：把数据存入 session_state
                    st.session_state.product_name = res['title']
                    st.session_state.product_data = res['content']
                    st.success("抓取成功！数据已保存。")
                else:
                    st.error(f"抓取失败 ({res['error']})。请切换到'手动输入'模式。")
    
    # 显示当前已抓取的数据
    if st.session_state.product_name:
        st.info(f"✅ 已就绪商品：{st.session_state.product_name}")
        with st.expander("查看抓取到的详情内容"):
            st.text(st.session_state.product_data[:500] + "...")

else:
    # 手动输入模式也同步到 session_state
    st.session_state.product_name = st.text_input("商品名称", value=st.session_state.product_name)
    st.session_state.product_data = st.text_area("商品卖点/详情描述", value=st.session_state.product_data, height=150)

# 2. 生成脚本
st.markdown("### 第二步：生成脚本")

if st.button("🚀 开始生成", type="primary"):
    # 检查数据是否存在
    if not api_key:
        st.warning("⚠️ 请先在左侧侧边栏输入 API Key！")
    elif not st.session_state.product_data:
        st.warning("⚠️ 请提供商品信息！(请先点击'尝试抓取'或手动输入)")
    else:
        with st.spinner(f"🧠 AI ({model_name}) 正在疯狂构思中..."):
            result = generate_script_with_ai(
                st.session_state.product_name, 
                st.session_state.product_data, 
                api_key, 
                base_url, 
                model_name
            )
            
            if "error" in result:
                st.error(f"AI 调用失败: {result['error']}")
            else:
                st.success("🎉 生成成功！")
                
                with st.expander("🧐 查看 AI 的营销分析", expanded=True):
                    st.write(result.get("analysis", "暂无分析"))
                
                st.markdown("---")
                
                scripts = result.get("scripts", [])
                if scripts:
                    tabs = st.tabs([s['style'] for s in scripts])
                    for i, tab in enumerate(tabs):
                        with tab:
                            script = scripts[i]
                            st.subheader(script['hook'])
                            for scene in script['scenes']:
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    st.info(f"⏱️ {scene['time']}\n\n🖼️ **画面:** {scene['visual']}")
                                with col2:
                                    st.success(f"🗣️ **台词:** {scene['audio']}")
