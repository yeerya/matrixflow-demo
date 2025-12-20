import streamlit as st
import json
import os
from openai import OpenAI

# ==========================================
# 1. 核心逻辑库 (The Brain & Expert Knowledge)
# ==========================================

# 定义“专家人设” - 这是我们的核心壁垒
SYSTEM_PROMPT = """
你是一位拥有10年经验的短视频导演和顶级AI提示词工程师(Prompt Engineer)。
你的任务是将用户的商品信息，转化为可以直接落地的“爆款视频拍摄全案”。

你必须遵循以下【核心原则】：
1. **视觉优先**：脚本必须有画面感，拒绝空洞的口号。
2. **参数化输出**：将“好看”转化为具体的光影、材质、镜头参数。
3. **视听一致**：画面描述必须严格对应旁白内容。
4. **平台适应性**：根据用户选择的绘图工具，输出对应的提示词格式。
"""

# 定义不同绘图工具的“翻译规则”
IMAGE_MODEL_RULES = {
    "Midjourney (艺术/电影感)": """
    - 格式要求: 英文, 逗号分隔, 包含参数后缀。
    - 结构: [Subject], [Environment], [Lighting], [Angle/Lens], [Style/Render] --ar 16:9 --v 6.0
    - 重点: 使用 cinematic lighting, hyper-realistic, 8k, detailed texture, depth of field 等词汇。
    """,
    "Flux / Google / DALL-E (自然写实)": """
    - 格式要求: 自然流畅的英文长句 (Natural Language)。
    - 结构: A detailed, photorealistic image of [Subject] doing [Action] in [Environment]. The lighting is [Lighting].
    - 重点: 描述越具体越好，强调文字渲染(Text Rendering)和构图逻辑。
    """,
    "Stable Diffusion (极客/精准控制)": """
    - 格式要求: 英文单词/短语 (Tags), 强调权重。
    - 结构: (best quality:1.2), (masterpiece), [Subject], [Tags], [Lighting], [Style]
    - 必须包含 Negative Prompt: nsfw, low quality, worst quality, bad anatomy, text, watermark.
    """
}

# 定义视频运镜的“黄金公式”
VIDEO_PROMPT_RULES = """
- 必须遵循公式: [Camera Movement] + [Subject Action] + [Atmosphere]
- 常用运镜词: Slow zoom in, Pan left, Static shot, Rack focus, Tracking shot.
- 常用动作词: Pages flipping, Water flowing, Smoke rising, Smiling naturally.
"""

# ==========================================
# 2. 界面布局 (Frontend)
# ==========================================

st.set_page_config(page_title="MatrixFlow V3.0", layout="wide", page_icon="🎬")

# 侧边栏设置
with st.sidebar:
    st.title("🎛️ 控制台")
    
    st.markdown("### 🔌 模型设置 (DeepSeek)")
    # 默认预设好 DeepSeek 的配置
    api_key = st.text_input("DeepSeek API Key", type="password", help="在此输入你的 DeepSeek API Key")
    base_url = st.text_input("Base URL", value="https://api.deepseek.com", disabled=False)
    model_name = st.text_input("Model Name", value="deepseek-chat", disabled=False)
    
    st.markdown("---")
    st.header("🎨 素材偏好")
    
    # 核心功能：选择绘图工具
    image_tool = st.selectbox(
        "绘图工具 (Image Gen)",
        ["Midjourney (艺术/电影感)", "Flux / Google / DALL-E (自然写实)", "Stable Diffusion (极客/精准控制)"],
        index=0,
        help="选择你打算使用的生图工具，AI 会生成对应的提示词格式。"
    )
    
    video_duration = st.select_slider("视频时长", options=["15s", "30s", "60s"])
    script_style = st.selectbox("脚本风格", ["幽默反转 (TikTok风)", "痛点直击 (带货风)", "情绪共鸣 (品牌风)"])

# 主界面
st.title("🎬 MatrixFlow - AI 视频全案生成器")
st.markdown("#### 🚀 你的 AI 导演 + 提示词专家")

col1, col2 = st.columns([2, 1])
with col1:
    product_url = st.text_input("商品链接 (URL)", placeholder="粘贴淘宝/亚马逊/TikTok链接...")
with col2:
    product_name = st.text_input("商品名称", placeholder="例如：2026故宫日历")

selling_points = st.text_area("补充卖点 (可选)", placeholder="例如：纸张手感好、送礼有面子、限量发售...", height=100)

# ==========================================
# 3. 后端逻辑 (Backend Brain)
# ==========================================

def generate_script():
    if not api_key:
        st.error("⚠️ 请先在左侧侧边栏输入 DeepSeek API Key")
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 动态构建 Prompt (The Dynamic Injection)
    # 这里我们将用户的选择和我们的“专家规则”混合在一起
    user_prompt = f"""
    请为商品【{product_name}】生成一个 {video_duration} 的短视频全案。
    
    【输入信息】
    - 卖点: {selling_points}
    - 风格: {script_style}
    - 目标绘图工具: {image_tool}
    
    【输出要求】
    请严格按照以下 JSON 格式输出，不要包含 markdown 格式标记（如 ```json ... ```）：
    {{
        "title": "视频标题",
        "scenes": [
            {{
                "scene_index": 1,
                "duration": "3s",
                "script_cn": "中文旁白/台词 (口语化)",
                "visual_cn": "中文画面描述 (详细)",
                "image_prompt_en": "英文绘图提示词 (必须严格遵守 {image_tool} 的规则: {IMAGE_MODEL_RULES[image_tool]})",
                "video_prompt_en": "英文视频运镜提示词 (必须严格遵守规则: {VIDEO_PROMPT_RULES})"
            }}
        ]
    }}
    """

    with st.spinner('🧠 DeepSeek 正在拆解分镜、计算光影参数...'):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2500,
                stream=False
            )
            
            content = response.choices[0].message.content
            # 清洗数据，防止 DeepSeek 有时候会带 markdown 符号
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
            
        except json.JSONDecodeError:
            st.error("❌ 生成格式错误，请重试 (JSON Parsing Error)")
            st.expander("查看原始返回").write(content)
            return None
        except Exception as e:
            st.error(f"❌ API 调用失败: {e}")
            return None

# ==========================================
# 4. 结果渲染 (Result Display)
# ==========================================

if st.button("✨ 生成全案 (Generate Matrix)", type="primary"):
    if not product_name:
        st.warning("请至少输入商品名称")
    else:
        result = generate_script()
        
        if result:
            st.success("🎉 全案生成完毕！")
            st.markdown(f"### 📹 标题：{result.get('title', '未命名视频')}")
            
            # 遍历展示分镜
            scenes = result.get('scenes', [])
            for scene in scenes:
                with st.expander(f"🎬 第 {scene['scene_index']} 镜 ({scene['duration']}) - {scene['visual_cn'][:20]}...", expanded=True):
                    
                    c1, c2 = st.columns([1, 1])
                    
                    # 左侧：给人看的内容
                    with c1:
                        st.markdown("#### 🇨🇳 脚本与画面")
                        st.info(f"**🗣️ 旁白:** {scene['script_cn']}")
                        st.write(f"**🖼️ 画面:** {scene['visual_cn']}")
                    
                    # 右侧：给机器看的内容 (核心价值)
                    with c2:
                        st.markdown(f"#### 🤖 AI 指令 ({image_tool.split()[0]})")
                        
                        # 绘图提示词
                        st.caption("🎨 绘图提示词 (Image Prompt) - [点击右上角复制]")
                        st.code(scene['image_prompt_en'], language="bash")
                        
                        # 视频提示词
                        st.caption("🎥 运镜提示词 (Video Prompt) - [点击右上角复制]")
                        st.code(scene['video_prompt_en'], language="bash")
            
            # 底部导出
            st.markdown("---")
            st.download_button(
                label="📥 导出完整 JSON 配置单",
                data=json.dumps(result, indent=4, ensure_ascii=False),
                file_name="matrixflow_script.json",
                mime="application/json"
            )
