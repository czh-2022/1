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
        Helper to read markdown content from knowledge directory.
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
        
        # 1. Always load General Elderly Guide
        general_guide = self._load_markdown_file("guide_general_elderly.md")
        if general_guide:
            snippets.append(f"【通用老年人膳食指南】\n{general_guide[:1000]}...") # Truncate to avoid context overflow if needed

        # 2. Condition-specific guides
        condition_map = {
            "hypertension": "guide_hypertension.md",
            "diabetes": "guide_diabetes.md",
            "gout": "guide_gout.md",
            "kidney_disease": "guide_ckd.md"
        }
        
        for condition in profile.health_conditions:
            if condition in condition_map:
                content = self._load_markdown_file(condition_map[condition])
                if content:
                    snippets.append(f"【针对{condition}的饮食建议】\n{content}")

        # 3. Query-based injection (Simple Keyword Matching)
        query_lower = query.lower()
        
        # Recipes
        if any(k in query_lower for k in ["食谱", "菜单", "吃什么", "早饭", "午饭", "晚饭", "recipe", "menu"]):
            recipes = self._load_markdown_file("guide_recipes.md")
            if recipes:
                snippets.append(f"【推荐食谱参考】\n{recipes}")

        # Seasonal
        if any(k in query_lower for k in ["春", "夏", "秋", "冬", "季节", "节气", "season"]):
            seasonal = self._load_markdown_file("guide_seasonal.md")
            if seasonal:
                snippets.append(f"【四季养生指南】\n{seasonal}")
                
        # Drug Interactions
        if any(k in query_lower for k in ["药", "副作用", "drug", "medicine"]):
            drugs = self._load_markdown_file("guide_drug_interactions.md")
            if drugs:
                snippets.append(f"【药物食物相互作用警示】\n{drugs}")

        return snippets

    def get_response(self, request: ChatRequest, nutrition_targets: str) -> str:
        if not self.client:
            return self._mock_response(request)
            
        if not request.user_profile:
            return "Error: User profile information is missing. Please ensure your profile is set up correctly."

        try:
            profile_str = request.user_profile.model_dump_json(indent=2)
            
            # Enhanced retrieval: Now passes user message for keyword matching
            knowledge_snippets = self._retrieve_knowledge(request.user_profile, request.message)
            
            context = generate_nutrition_context(profile_str, nutrition_targets, knowledge_snippets)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}, # Put context in user message to avoid system prompt overuse issues with some models
                {"role": "user", "content": request.message}
            ]
            
            # Add history
            for msg in request.history:
                messages.append(msg)
            
            # Add current user message
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
