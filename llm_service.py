import os
import json
import openai
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, REJECTION_PROMPT, generate_nutrition_context
from models import ChatRequest, UserProfile
from config import config

class LLMService:
    def __init__(self):
        # Use DeepSeek configuration from config.py
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_API_BASE
        self.model = config.DEEPSEEK_MODEL
        
        self.knowledge_base_dir = "dify_assets/knowledge"
        
        if self.api_key:
            # DeepSeek is OpenAI-compatible
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            print("Warning: DEEPSEEK_API_KEY not found in config. Using Mock LLM.")

    def _load_markdown_file(self, filename: str) -> str:
        """
        辅助函数：从知识库目录读取 Markdown 内容。
        """
        try:
            path = os.path.join(self.knowledge_base_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            return ""

    def _retrieve_knowledge(self, profile: UserProfile, query: str = "") -> list[str]:
        snippets = []
        
        # 1. 始终加载通用老年人指南
        general_guide = self._load_markdown_file("guide_general_elderly.md")
        if general_guide:
            snippets.append(f"【通用老年人膳食指南】\n{general_guide[:1000]}...") # 截断以避免上下文溢出

        # 2. 特定疾病指南
        condition_map = {
            "hypertension": "guide_hypertension.md",
            "diabetes": "guide_diabetes.md",
            "gout": "guide_gout.md",
            "kidney_disease": "guide_ckd.md",
            "osteoporosis": "guide_osteoporosis.md",
            "alzheimers": "guide_alzheimers.md",
            "cardiovascular": "guide_cardiovascular.md",
            "constipation": "guide_constipation.md",
            "sarcopenia": "guide_sarcopenia.md",
            "anemia": "guide_anemia.md",
            "dysphagia": "guide_dysphagia.md",
            "hydration": "guide_hydration.md",
            "respiratory": "guide_respiratory.md",
            "digestive": "guide_digestive.md",
            "immune": "guide_immune.md"
        }
        
        for condition in profile.health_conditions:
            if condition in condition_map:
                content = self._load_markdown_file(condition_map[condition])
                if content:
                    snippets.append(f"【针对{condition}的饮食建议】\n{content}")

        # 3. 基于查询的注入 (简单关键词匹配)
        query_lower = query.lower()
        
        # 食谱
        if any(k in query_lower for k in ["食谱", "菜单", "吃什么", "早饭", "午饭", "晚饭", "recipe", "menu"]):
            recipes = self._load_markdown_file("guide_recipes.md")
            if recipes:
                snippets.append(f"【推荐食谱参考】\n{recipes}")
        
        # 药物相互作用 (新增)
        if any(k in query_lower for k in ["药", "吃药", "副作用", "drug", "medicine", "medication"]):
            drug_guide = self._load_markdown_file("guide_drug_interactions.md")
            if drug_guide:
                snippets.append(f"【药物-食物相互作用警示】\n{drug_guide}")

        # 季节/时令
        if any(k in query_lower for k in ["春", "夏", "秋", "冬", "季节", "节气", "season"]):
            seasonal = self._load_markdown_file("guide_seasonal.md")
            if seasonal:
                snippets.append(f"【四季养生指南】\n{seasonal}")
                
        # 4. 基于症状/疾病的注入 (增强意图识别)
        # 疾病关键词映射
        disease_keywords = {
            "hypertension": ["高血压", "血压高", "头晕", "hypertension", "blood pressure"],
            "diabetes": ["糖尿病", "血糖", "消渴", "多饮", "diabetes", "blood sugar"],
            "gout": ["痛风", "尿酸", "关节痛", "海鲜", "gout", "uric acid"],
            "kidney_disease": ["肾病", "肌酐", "蛋白尿", "水肿", "浮肿", "kidney", "renal"],
            "osteoporosis": ["骨质疏松", "骨折", "缺钙", "腰酸背痛", "osteoporosis", "bone"],
            "alzheimers": ["老年痴呆", "记忆力", "阿尔茨海默", "忘事", "alzheimer", "dementia", "mind diet"],
            "cardiovascular": ["心脏病", "冠心病", "心绞痛", "血脂", "动脉硬化", "cardiovascular", "heart"],
            "constipation": ["便秘", "大便干", "排便困难", "通便", "constipation", "fiber"],
            "sarcopenia": ["肌少症", "肌肉萎缩", "没力气", "摔倒", "sarcopenia", "muscle"],
            "anemia": ["贫血", "头晕", "眼花", "面色苍白", "anemia", "iron"],
            "dysphagia": ["吞咽困难", "呛咳", "吃不下", "噎住", "dysphagia", "swallow"],
            "hydration": ["脱水", "口渴", "尿黄", "喝水", "hydration", "water"],
            "respiratory": ["气喘", "咳嗽", "慢阻肺", "哮喘", "呼吸困难", "copd", "asthma"],
            "digestive": ["胃痛", "反酸", "胃胀", "不消化", "胃炎", "gastritis", "stomach"],
            "immune": ["感冒", "免疫力", "体质差", "术后", "恢复期", "immune", "flu"]
        }
        
        for condition, keywords in disease_keywords.items():
            # 检查查询中是否存在关键词
            if any(k in query_lower for k in keywords):
                # 检查是否尚未通过画像加载
                if condition not in profile.health_conditions and condition in condition_map:
                    content = self._load_markdown_file(condition_map[condition])
                    if content:
                        snippets.append(f"【根据您的描述为您补充：针对{condition}的饮食建议】\n{content}")

        return snippets

    def get_response(self, request: ChatRequest, nutrition_targets: str) -> str:
        if not self.client:
            return self._mock_response(request)
            
        if not request.user_profile:
            return "Error: User profile information is missing. Please ensure your profile is set up correctly."

        try:
            profile_str = request.user_profile.model_dump_json(indent=2)
            
            # 增强检索：现在传递用户消息以进行关键词匹配
            knowledge_snippets = self._retrieve_knowledge(request.user_profile, request.message)
            
            context = generate_nutrition_context(profile_str, nutrition_targets, knowledge_snippets)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}, # 将上下文放入用户消息中，以避免某些模型过度使用系统提示
                {"role": "user", "content": request.message}
            ]
            
            # 添加历史记录
            for msg in request.history:
                messages.append(msg)
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": request.message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"

    def _mock_response(self, request: ChatRequest) -> str:
        """Fallback response when no API key is provided."""
        msg = request.message.lower()
        if "高血压" in msg:
            return "对于高血压患者，建议限制钠盐摄入（每日不超过5克食盐），多吃富含钾的食物如香蕉、菠菜。避免腌制食品。"
        elif "糖尿病" in msg:
            return "糖尿病饮食需控制总碳水化合物，优先选择低GI食物（如燕麦、全麦面包），避免精制糖和甜饮料。"
        elif "食谱" in msg or "吃什么" in msg:
            return "基于您的健康状况，我建议早餐：燕麦粥加一个鸡蛋；午餐：清蒸鱼、炒青菜和杂粮饭；晚餐：豆腐汤和少量瘦肉。记得少油少盐。"
        else:
            return "我是您的智能营养师助手。请告诉我您的健康状况或想咨询的饮食问题，我会为您提供个性化建议。"
