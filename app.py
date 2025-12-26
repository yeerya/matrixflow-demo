import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from PIL import Image
import requests
from bs4 import BeautifulSoup
import json
import re

# ==========================================
# 1. 配置与常量 (Configuration)
# ==========================================

st.set_page_config(page_title="MatrixFlow V4.1 - 修复版", layout="wide", page_icon="🛍️")

# 定义大师级提示词模板 (已修复括号冲突 Bug)
# 注意：JSON 部分的 { } 已改为 {{ }} 以避免 Python 格式化错误
MASTER_PROMPT_TEMPLATE = """
你是一位拥有20年经验的顶级电商美术指导(Art Director)和AI提示词专家。
你的任务是基于产品的【事实数据】和【视觉描述】，输出一套完整的、极简高端的旗舰店KV系统提示词。

请严格遵循以下 JSON 格式输出，不要包含 Markdown 格式之外的多余废话。

输出结构要求 (JSON):
{{
    "video_scripts": [
        {{ "title": "痛点切入版", "content": "脚本内容..." }},
        {{ "title": "利益诱惑版", "content": "脚本内容..." }}
    ],
    "image_prompts": {{
        "00_Logo": "基于品牌名的极简Logo提示词...",
        "01_Hero_KV": "主KV海报(9:16)，包含模特、产品、大标题...",
        "02_Lifestyle": "生活场景展示，自然光，氛围感...",
        "03_Detail_Texture": "微距细节，展示材质纹理...",
        "04_Detail_Feature": "功能细节特写...",
        "05_Info_Card": "极简排版的参数表/尺码表..."
    }},
    "video_prompts": {{
        "01_Hero_Video": "慢动作推镜头(Slow zoom in) + 模特互动...",
        "02_Detail_Video": "微距平移(Macro pan) + 材质光泽流动...",
        "03_Lifestyle_Video": "手持感镜头(Handheld) + 场景氛围..."
    }}
}}

设计原则 (Design Principles):
1.  **风格统一**: 所有提示词必须保持统一的色调(Color Palette)、光影(Lighting)和模特特征(Model consistency)。
2.  **PixMiller标准**:
    - 图片必须包含: Subject, Environment, Lighting, Composition, Color Palette, Aspect Ratio (--ar 9:16).
    - 必须包含负面词(Negative Prompts): cluttered, busy, low quality, watermark, distorted.
    - 视频必须包含: Camera Movement, Subject Action, Atmosphere.
3.  **语言**: 脚本用中文，提示词(Prompts)全部用英文。

输入信息:
- 商品: {product_name}
- 视觉特征: {visual_desc}
- 卖点数据: {scraped_data}
"""

# ==========================================
# 2. 核心功能函数 (Core Functions)
# ==========================================

def init_clients(deepseek_key, gemini_key):
    """初始化 AI 客户端"""
    ds_client = None
    if deepseek_key:
        ds_client = OpenAI(
            api_key=deepseek_key,
            base_url="https://api.deepseek.com"
        )
    
    if gemini_key:
        genai.configure(api_key=gemini_key)
    
    return ds_client

def analyze_image_with_gemini(image, prompt="请详细描述这个产品的外观、颜色、材质、风格，以及上面的文字信息。"):
    """使用 Gemini 进行视觉分析 (The Eye)"""
    try:
        # 尝试使用 flash 模型，如果失败会捕获异常
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        # 如果 Flash 失败，返回错误信息建议检查 Key
        return f"视觉分析暂不可用 (Error: {str(e)})。建议：请确保 API Key 正确且开通了 Gemini 1.5 Flash 权限。"

def scrape_product_info(url):
    """简单的网页抓取 (The Hand)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string.strip() if soup.title else "未知商品"
        return f"网页标题: {title} (已获取基础信息)"
    except Exception as e:
        return f"抓取失败: {str(e)}"

def generate_full_case(client, product_name, visual_desc, scraped_data):
    """DeepSeek 生成全案 (The Brain)"""
    
    # 填充 Prompt 模板
    # 这里的 .format() 现在安全了，因为 JSON 的括号已经被双写转义
    final_prompt = MASTER_PROMPT_TEMPLATE.format(
        product_name=product_name,
        visual_desc=visual_desc,
        scraped_data=scraped_data
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a creative director assistant. Output only valid JSON."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=1.1,
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"DeepSeek 生成失败: {str(e)}")
        return None

# ==========================================
# 3. 前端界面 (UI Layout)
# ==========================================

def main():
    with st.sidebar:
        st.header("⚙️ 核心配置")
        deepseek_api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
        gemini_api_key = st.text_input("Gemini API Key", type="password", placeholder="AIz...")
        st.markdown("---")
        st.info("💡 提示: 上传图片 + 填写链接，效果最佳！")
        img_model = st.selectbox("绘图模型偏好", ["Midjourney (默认)", "Flux", "Stable Diffusion"])

    st.title("🛍️ MatrixFlow V4.1 - 修复版")
    st.markdown("##### 事实(URL) + 视觉(Image) + 大脑(AI) = 爆款素材全案")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("1. 事实数据 (URL)")
        product_url = st.text_input("商品链接", placeholder="https://...")
        product_name_input = st.text_input("商品名称 (必填)", placeholder="例如: 京东京造湿厕纸")
        
    with col2:
        st.subheader("2. 视觉素材 (Image)")
        uploaded_file = st.file_uploader("上传参考图", type=['jpg', 'png', 'jpeg'])

    if st.button("🚀 启动全案生成引擎", type="primary"):
        if not deepseek_api_key or not gemini_api_key:
            st.error("请先填写 API Key！")
            return

        ds_client = init_clients(deepseek_api_key, gemini_api_key)
        status_text = st.empty()
        progress_bar = st.progress(0)

        # 视觉分析
        visual_info = "用户未上传图片"
        if uploaded_file:
            status_text.text("👁️ Gemini 正在分析图片...")
            progress_bar.progress(20)
            image = Image.open(uploaded_file)
            visual_info = analyze_image_with_gemini(image)
            # 即使视觉分析失败，也不要阻断流程，只显示警告
            if "Error" in visual_info:
                st.warning(visual_info)
            else:
                st.success(f"视觉提取完成: {visual_info[:30]}...")
        
        # 数据抓取
        scraped_info = "用户未提供链接"
        if product_url:
            status_text.text("🕷️ 正在抓取数据...")
            progress_bar.progress(40)
            scraped_info = scrape_product_info(product_url)
            st.success("链接数据提取完成")

        # 全案生成
        status_text.text("🧠 DeepSeek 正在构建全案...")
        progress_bar.progress(60)
        
        result = generate_full_case(ds_client, product_name_input, visual_info, scraped_info)
        
        progress_bar.progress(100)
        status_text.text("✅ 生成完毕！")

        if result:
            st.divider()
            tab1, tab2, tab3 = st.tabs(["🎥 短视频脚本", "🎨 绘图提示词", "🎬 运镜指令"])
            
            with tab1:
                for script in result.get('video_scripts', []):
                    with st.expander(f"📜 {script.get('title', '脚本')}", expanded=True):
                        st.write(script.get('content', ''))
            
            with tab2:
                st.markdown("#### PixMiller 风格 - 全案 KV 系统")
                img_prompts = result.get('image_prompts', {})
                for key, prompt in img_prompts.items():
                    # 自动根据选择的模型添加后缀
                    suffix = " --ar 9:16 --v 6.0" if img_model == "Midjourney (默认)" else ""
                    st.text_area(f"🖼️ {key}", value=str(prompt) + suffix, height=150)
            
            with tab3:
                st.markdown("#### 视频运镜指令")
                vid_prompts = result.get('video_prompts', {})
                for key, prompt in vid_prompts.items():
                    st.text_area(f"📹 {key}", value=str(prompt), height=100)

if __name__ == "__main__":
    main()
