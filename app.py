import streamlit as st
import time
import random

# --- 页面配置 ---
st.set_page_config(
    page_title="MatrixFlow 爆款脚本生成器",
    page_icon="🚀",
    layout="wide"
)

# --- 模拟后端核心逻辑 (实际部署时替换为真实模块 import) ---
def mock_process(url):
    """模拟全流程：爬取 -> 挖掘 -> 生成"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    # 1. 爬虫阶段
    status_text.text("🕷️ 正在爬取商品信息...")
    time.sleep(1) 
    progress_bar.progress(30)
    
    # 2. 挖掘阶段
    status_text.text("⛏️ 正在挖掘用户差评与痛点...")
    time.sleep(1)
    progress_bar.progress(60)
    
    # 3. AI生成阶段
    status_text.text("🧠 AI 正在构思爆款脚本...")
    time.sleep(1.5)
    progress_bar.progress(90)
    
    # 完成
    status_text.text("✅ 生成完毕！")
    progress_bar.progress(100)
    time.sleep(0.5)
    progress_bar.empty() # 隐藏进度条

    # 返回模拟数据
    return {
        "product": {
            "name": "京东京造 纯水湿厕纸",
            "price": "9.9",
            "features": ["EDI纯水", "可冲散", "加厚"]
        },
        "pain_points": ["干纸擦得疼", "怕堵马桶", "纸太薄容易破"],
        "scripts": [
            {
                "style": "🔥 痛点直击型",
                "hook": "还在用干纸硬擦？",
                "scenes": [
                    {"time": "0-3s", "visual": "砂纸打磨猕猴桃", "audio": "那种火辣辣的感觉，谁疼谁知道！"},
                    {"time": "3-8s", "visual": "展示湿厕纸", "audio": "试试这个！纯水配方，像SPA一样温柔！"},
                    {"time": "8-12s", "visual": "丢入水中搅拌即散", "audio": "原生木浆，用完直接冲，完全不堵！"}
                ]
            },
            {
                "style": "💰 性价比狂魔型",
                "hook": "几块钱的快乐",
                "scenes": [
                    {"time": "0-5s", "visual": "展示一大包纸", "audio": "9块9能买什么？买不到奶茶，但能买到80片超大湿厕纸！"},
                    {"time": "5-10s", "visual": "暴力撕扯测试", "audio": "看这韧性，怎么扯都不破！"}
                ]
            }
        ]
    }

# --- 前端 UI 布局 ---

# 侧边栏：控制区
with st.sidebar:
    st.title("🚀 MatrixFlow")
    st.markdown("---")
    st.write("**当前版本:** v0.1.0 (Alpha)")
    st.info("💡 使用说明：复制京东/淘宝商品链接，点击生成即可。")
    
    api_key = st.text_input("OpenAI API Key (选填)", type="password")
    model_select = st.selectbox("选择模型", ["GPT-4o", "GPT-3.5-Turbo", "Gemini Pro"])

# 主区域：内容区
st.title("🎬 爆款短视频脚本生成器")
st.markdown("#### *输入商品链接，一键生成带货脚本*")

# 输入框
url_input = st.text_input("在此粘贴商品链接:", placeholder="https://item.jd.com/...")

# 生成按钮
if st.button("🚀 开始生成脚本", type="primary"):
    if not url_input:
        st.warning("⚠️ 请先输入链接！")
    else:
        # 调用处理逻辑
        with st.spinner('AI 正在疯狂运转中...'):
            result = mock_process(url_input)
        
        # --- 结果展示区 ---
        st.success("🎉 脚本生成成功！")
        
        # 展示商品简报
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("商品价格", f"¥{result['product']['price']}")
        with col2:
            st.write(f"**商品:** {result['product']['name']}")
            st.write(f"**核心痛点:** {', '.join(result['pain_points'])}")

        st.markdown("---")
        
        # 展示脚本 (使用 Tabs 切换不同风格)
        tab1, tab2 = st.tabs(["脚本 A (痛点型)", "脚本 B (性价比型)"])
        
        with tab1:
            script = result['scripts'][0]
            st.subheader(f"{script['style']} - {script['hook']}")
            
            # 表格化展示分镜
            for scene in script['scenes']:
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 3])
                    c1.markdown(f"**{scene['time']}**")
                    c2.info(f"🖼️ {scene['visual']}")
                    c3.success(f"🗣️ \"{scene['audio']}\"")
            
            # 反馈按钮
            st.markdown("---")
            col_fb1, col_fb2 = st.columns(2)
            if col_fb1.button("👍 这个脚本很棒", key="like_a"):
                st.toast("感谢反馈！我们会保持这种风格。")
            if col_fb2.button("👎 感觉一般", key="dislike_a"):
                st.toast("收到，下次我们会调整 Prompt。")

        with tab2:
            script = result['scripts'][1]
            st.subheader(f"{script['style']} - {script['hook']}")
            for scene in script['scenes']:
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 3])
                    c1.markdown(f"**{scene['time']}**")
                    c2.info(f"🖼️ {scene['visual']}")
                    c3.success(f"🗣️ \"{scene['audio']}\"")
