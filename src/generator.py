"""
生成器模块 - LLM 调用封装，支持 OpenAI 及兼容 API
"""
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import config


SYSTEM_PROMPT = """你是一个红色文化教育助手，专注于党史、红色故事、英烈事迹和校史等知识领域的讲解与问答。

请遵循以下规则：
1. 优先基于提供的参考知识进行回答，确保内容准确、严谨。
2. 如果参考知识不足以回答问题，请诚实说明，不要编造。
3. 回答风格应庄重、生动，适合学习者理解。
4. 适当融入红色精神、育人理念。
5. 回答末尾可附加一句简短的激励语。"""


class Generator:
    """LLM 生成器"""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model = model or config.LLM_MODEL
        kwargs = {"model": self.model, "temperature": 0.3}
        api_key = api_key or config.OPENAI_API_KEY
        if api_key:
            kwargs["openai_api_key"] = api_key
        if base_url or config.OPENAI_BASE_URL:
            kwargs["openai_base_url"] = base_url or config.OPENAI_BASE_URL
        self._llm: Optional[ChatOpenAI] = None
        self._llm_kwargs = kwargs

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(**self._llm_kwargs)
        return self._llm

    def generate(
        self,
        query: str,
        context: str = "",
        system_prompt: str = None,
    ) -> str:
        """基于上下文生成回答"""
        system_prompt = system_prompt or SYSTEM_PROMPT
        messages = [SystemMessage(content=system_prompt)]
        if context:
            user_content = (
                f"请根据以下参考知识回答问题。\n\n"
                f"【参考知识】\n{context}\n\n"
                f"【用户问题】\n{query}"
            )
        else:
            user_content = query
        messages.append(HumanMessage(content=user_content))
        response = self.llm.invoke(messages)
        return response.content

    def generate_quiz(
        self,
        context: str,
        num_questions: int = 3,
        question_type: str = "choice",
    ) -> str:
        """基于知识内容生成测验题目"""
        type_desc = {
            "choice": "单选题（4个选项，附带正确答案和解析）",
            "judge": "判断题（附带正确答案和解析）",
            "fill": "填空题（附带正确答案和解析）",
        }
        qtype = type_desc.get(question_type, type_desc["choice"])
        prompt = f"""请根据以下知识内容，生成 {num_questions} 道{qtype}。

【知识内容】
{context}

请按以下格式输出每道题：
题目：<题目内容>
A. <选项A>
B. <选项B>
C. <选项C>
D. <选项D>
正确答案：<答案>
解析：<解析>
---"""
        messages = [
            SystemMessage(content="你是一个红色文化教育出题助手，根据给定知识生成高质量的测验题目。"),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def explain_concept(self, concept: str, context: str = "") -> str:
        """讲解知识点"""
        if context:
            prompt = (
                f"请详细讲解以下红色文化知识点：{concept}\n\n"
                f"【参考资料】\n{context}\n\n"
                f"请从背景、主要内容、历史意义等方面展开讲解。"
            )
        else:
            prompt = f"请详细讲解以下红色文化知识点：{concept}\n请从背景、主要内容、历史意义等方面展开讲解。"
        return self.generate(prompt, context="")