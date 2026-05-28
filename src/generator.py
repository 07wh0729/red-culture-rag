"""
生成器模块 v2 - 严格溯源、防幻觉、支持多媒体关联
"""
from typing import Optional, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

import config


SYSTEM_PROMPT = """你是一个红色文化教育助手，服务于校园红色文化育人平台。

【核心准则 - 必须严格遵守】
1. 绝对基于参考知识回答：你的回答必须100%来源于提供的【参考知识】。
2. 杜绝编造：如果参考知识不能完整回答问题，明确告知"根据现有知识库，该问题无法完整回答"，绝不自造内容。
3. 必须标注来源：每段回答末尾必须注明引用的来源文档名称。
4. 回答风格：庄重、生动、准确，适合校园师生阅读。适当融入红色精神与育人理念。
5. 引用原文：涉及关键史实、人物、时间时，优先引用知识库原文表述。
6. 不确定时：对于模糊或存疑之处，诚实说明，不强行作答。"""


class Generator:
    """LLM 生成器 v2"""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model = model or config.LLM_MODEL
        api_key = api_key or config.DEEPSEEK_API_KEY or config.OPENAI_API_KEY
        base_url = base_url or config.DEEPSEEK_BASE_URL or config.OPENAI_BASE_URL
        kwargs = {"model": self.model, "temperature": 0.1}
        if api_key:
            kwargs["openai_api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self._llm: Optional[ChatOpenAI] = None
        self._llm_kwargs = kwargs

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(**self._llm_kwargs)
        return self._llm

    def _build_user_prompt(self, query: str, context: str) -> str:
        """构建带强约束的用户提示"""
        return f"""请根据以下参考知识回答问题。如果参考知识不足以回答，请如实说明。

【参考知识】
{context}

【回答要求】
1. 所有关键信息必须来源于上述参考知识
2. 在回答末尾用"【来源】"标注引用了哪些文档
3. 如果参考知识不足以回答全部问题，在"【补充说明】"中注明

【用户问题】
{query}"""

    def generate(
        self,
        query: str,
        context: str = "",
        system_prompt: str = None,
    ) -> dict:
        """基于上下文生成回答，返回结构化结果"""
        system_prompt = system_prompt or SYSTEM_PROMPT
        messages = [SystemMessage(content=system_prompt)]
        if context:
            user_content = self._build_user_prompt(query, context)
        else:
            user_content = f"【注意：当前没有检索到相关知识库内容】\n\n{query}"
        messages.append(HumanMessage(content=user_content))
        response = self.llm.invoke(messages)

        return {
            "answer": response.content,
            "model": self.model,
            "has_context": bool(context),
        }

    def generate_quiz(
        self,
        context: str,
        num_questions: int = 5,
        question_type: str = "choice",
    ) -> str:
        """基于知识内容生成测验题目"""
        type_map = {
            "single": "单选题（4个选项，1个正确答案）",
            "multi": "多选题（4个选项，2-4个正确答案）",
            "short": "简答题（需用知识库内容作答）",
        }
        qtype = type_map.get(question_type, type_map["single"])

        prompt = f"""请根据以下知识内容，严格基于原文信息生成 {num_questions} 道{qtype}。

【知识内容】
{context}

【重要：输出格式】
每道题严格使用以下格式（以 --- 分隔）：

题目：<题目内容>
A. <选项A>
B. <选项B>
C. <选项C>
D. <选项D>
正确答案：<正确选项字母，多选用逗号分隔>
解析：<解析内容，必须引用知识库原文>
来源：<来源文档名>
---

要求：
- 题目必须100%基于原文信息，不可编造
- 错误选项要有一定迷惑性但明显不符合原文
- 解析中必须引用知识库原文语句"""
        messages = [
            SystemMessage(content="你是一个严谨的红色文化教育出题助手。题目必须100%基于给定知识内容，不可编造。"),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def explain_concept(self, concept: str, context: str = "") -> dict:
        """讲解知识点，返回结构化结果"""
        if context:
            prompt = self._build_user_prompt(
                f"请详细讲解以下红色文化知识点：{concept}",
                context
            )
        else:
            prompt = f"请详细讲解以下红色文化知识点：{concept}\n（注意：当前无相关知识库内容）"
        return self.generate(prompt, context=context)

    def generate_story_narration(self, story_text: str) -> str:
        """将故事文本转为适合语音播报的叙事文本"""
        prompt = f"""请将以下红色故事改写为适合语音播报的叙事文本。
要求：
1. 保持原文关键信息不变
2. 语言更口语化、适合朗读
3. 控制长度在500字以内
4. 添加适当的情感提示词

【原文】
{story_text}"""
        messages = [
            SystemMessage(content="你是红色故事播报文案撰写助手。"),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content