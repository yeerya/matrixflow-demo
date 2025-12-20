import streamlit as st
import json
import os
from openai import OpenAI
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心逻辑库
# ==========================================

SYSTEM_PROMPT = """
你是一位拥有10年经验的短视频导演。
你将收到一份【商品视觉描述】（由视觉AI提取）和【卖点】。
请基于这些信息，生成一份严格的短视频全案。

【绝对原则】
1. **忠实于视觉描述**：如果视觉描述说是“红色日历”，脚本中绝不能出现“蓝色”。
2. **画面感**：将视觉特征融入到分镜描述中。
"""

# ==========================================
# 2. 界面布局
# ==========================================

st.set_page_config(page_title="MatrixFlow V3.2 (Hybrid)", layout="wide", page_icon="👁️")

with st.sidebar:
    st.title("🎛️ 双核引擎设置")
    
    st.markdown("### 🧠 大脑 (DeepSeek/OpenAI)")
    brain_api_key = st.text_input("DeepSeek API Key", type="password")
    brain_base_url = st.text_input("Base URL", value="https://api.deepseek.com")
    brain_model = st.text_input("Chat Model", value="deepseek-chat")
    
    st.markdown("---")
    
    st.markdown("### 👀 眼睛 (Google Gemini)")
    vision_api_key = st.text_input("Gemini API Key", type="password", help="去 aistudio.google.com 申请")
    
    st.markdown("---")
    image_tool = st.selectbox("绘图工具", ["Midjourney", "Flux", "Stable Diffusion"])
    video_duration = st.select_slider("视频时长", options=["15s", "30s", "60s"])

st.title("🎬 MatrixFlow V3.2 - 视觉增强版")
st.markdown("#### 📸 拖入图片，AI 自动提取特征，拒绝幻觉")

# ==========================================
# 3. 用户输入区 (支持图片)
# ==========================================

col1, col2 = st.columns([1, 1])

with col1:
    product_name = st.text_input("商品名称", value="2025故宫日历")
    uploaded_file = st.file_uploader("📸 上传商品参考图 (截图/实拍)", type=["jpg", "png", "jpeg"])

with col2:
    selling_points = st.text_area("补充卖点", value="送礼首选，每日一张国宝图，文化底蕴深厚", height=150)
    # 这里显示 AI 看到的描述，也允许用户手动修改
    visual_context = st.text_area("👀 视觉描述 (AI自动提取/手动填写)", placeholder="上传图片后，这里会自动填充...", height=150)

# ==========================================
# 4. 视觉分析逻辑 (Gemini)
# ==========================================

def analyze_image(image_file, api_key):
    """调用 Gemini 1.5 Flash 快速分析图片"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    img = Image.open(image_file)
    
    prompt = """
    请详细描述这张图片中的商品外观。
    重点关注：颜色、材质、纹理、文字内容、风格、光影氛围。
    请用一段简洁的中文描述，不要分点。
    例如：这是一个红色的日历，封面有烫金的蛇年图案，放在木质桌面上，光线柔和。
    """
    
    with st.spinner('👁️ Gemini 正在观察图片细节...'):
        try:
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            st.error(f"视觉分析失败: {e}")
            return None

# 自动触发视觉分析
if uploaded_file and vision_api_key and not visual_context:
    description = analyze_image(uploaded_file, vision_api_key)
    if description:
        # 使用 session_state 或者是直接 rerun 来更新 UI 比较麻烦，
        # 这里我们简单地提示用户复制，或者在下一步直接使用
        st.success("✅ 图片分析成功！")
        st.info(f"**AI 看到的:** {description}")
        # 这是一个小 trick，让用户确认
        if st.button("👇 使用这段描述"):
            visual_context = description # 仅在当前运行有效，Streamlit 刷新需用 session_state，简化版先这样

# ==========================================
# 5. 脚本生成逻辑 (DeepSeek)
# ==========================================

def generate_script(visual_desc):
    if not brain_api_key:
        st.error("缺 DeepSeek Key")
        return

    client = OpenAI(api_key=brain_api_key, base_url=brain_base_url)

    # 动态规则注入
    mj_rule = "Format: [Subject], [Environment], [Lighting] --ar 16:9"
    
    user_prompt = f"""
    商品: {product_name}
    视觉外观: {visual_desc} (这是核心，必须基于此生成画面)
    卖点: {selling_points}
    时长: {video_duration}
    
    请生成 JSON 格式的视频脚本：
    {{
        "title": "标题",
        "scenes": [
            {{
                "scene_index": 1,
                "script_cn": "旁白",
                "visual_cn": "画面描述",
                "image_prompt_en": "英文提示词 (包含视觉外观特征, {mj_rule})",
                "video_prompt_en": "运镜指令"
            }}
        ]
    }}
    """

    with st.spinner('🧠 DeepSeek 正在撰写脚本...'):
        try:
            response = client.chat.completions.create(
                model=brain_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            st.error(f"脚本生成失败: {e}")
            return None

# ==========================================
# 6. 执行按钮
# ==========================================

if st.button("✨ 生成全案 (Vision + Brain)", type="primary"):
    # 优先使用用户上传图片分析出的描述，如果没有，就看文本框
    final_visual = visual_context
    
    # 如果用户上传了图，但还没手动填描述，且刚才没点确认，我们在这里再跑一次分析（为了流程顺畅）
    if uploaded_file and not final_visual and vision_api_key:
        final_visual = analyze_image(uploaded_file, vision_api_key)
    
    if not final_visual:
        st.warning("⚠️ 请上传图片 或 手动填写外观描述！")
    else:
        result = generate_script(final_visual)
        if result:
            st.markdown("---")
            st.markdown(f"### 🎯 基于视觉描述：*{final_visual}*")
            st.json(result)
