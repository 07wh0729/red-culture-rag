"""
测验引擎 - 题目解析、作答、判分、错题解析
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Question:
    """题目数据结构"""
    id: int
    type: str  # single / multi / short
    stem: str  # 题干
    options: List[str] = field(default_factory=list)
    answer: str = ""  # 正确答案
    explanation: str = ""
    source: str = ""  # 来源文档

    @property
    def is_objective(self) -> bool:
        return self.type in ("single", "multi")


class QuizParser:
    """将 LLM 生成的题目文本解析为结构化 Question 对象"""

    @staticmethod
    def parse(quiz_text: str) -> List[Question]:
        questions = []
        blocks = quiz_text.split("---")
        for idx, block in enumerate(blocks):
            block = block.strip()
            if not block or len(block) < 10:
                continue

            q = Question(id=idx + 1, type="single")
            lines = block.strip().split("\n")

            options = []
            for line in lines:
                line = line.strip()
                if line.startswith("题目：") or line.startswith("题目:"):
                    q.stem = line.replace("题目：", "").replace("题目:", "").strip()
                elif re.match(r"^[A-D]\.", line) or re.match(r"^[A-D]\)", line):
                    options.append(line.strip())
                elif "正确答案" in line:
                    ans = line.split("：")[-1].split(":")[-1].strip()
                    q.answer = ans.upper().replace(" ", "")
                elif "解析" in line:
                    q.explanation = line.split("：", 1)[-1].split(":", 1)[-1].strip()
                elif "来源" in line:
                    q.source = line.split("：", 1)[-1].split(":", 1)[-1].strip()

            q.options = options

            # 判断题型
            if q.answer and "," in q.answer:
                q.type = "multi"
            elif not q.options:
                q.type = "short"

            if q.stem:
                questions.append(q)

        return questions


class QuizEngine:
    """测验引擎：生成、作答、判分、统计"""

    def __init__(self, generator=None):
        self._generator = generator
        self.current_questions: List[Question] = []
        self.user_answers: Dict[int, str] = {}

    @property
    def generator(self):
        if self._generator is None:
            from .generator import Generator
            self._generator = Generator()
        return self._generator

    def generate(
        self,
        context: str,
        num_questions: int = 5,
        question_type: str = "single",
    ) -> List[Question]:
        """生成题目并解析为结构化数据"""
        raw = self.generator.generate_quiz(context, num_questions, question_type)
        self.current_questions = QuizParser.parse(raw)
        self.user_answers = {}
        return self.current_questions

    def submit_answer(self, question_id: int, answer: str):
        """提交单题答案"""
        self.user_answers[question_id] = answer.strip().upper()

    def grade(self) -> dict:
        """自动判分"""
        total = len(self.current_questions)
        if total == 0:
            return {"total": 0, "correct": 0, "score": 0, "details": []}

        correct_count = 0
        details = []
        for q in self.current_questions:
            user_ans = self.user_answers.get(q.id, "")
            is_correct = False

            if q.type == "single":
                is_correct = user_ans == q.answer
            elif q.type == "multi":
                user_set = set(user_ans.replace(",", ""))
                ans_set = set(q.answer.replace(",", ""))
                is_correct = user_set == ans_set
            elif q.type == "short":
                # 简答题需要人工或 LLM 评判，此处标记为待评判
                is_correct = None

            if is_correct:
                correct_count += 1

            details.append({
                "id": q.id,
                "type": q.type,
                "stem": q.stem,
                "options": q.options,
                "user_answer": user_ans,
                "correct_answer": q.answer,
                "is_correct": is_correct,
                "explanation": q.explanation,
                "source": q.source,
            })

        # 只计算客观题得分
        objective_total = sum(1 for q in self.current_questions if q.is_objective)
        score = round(correct_count / objective_total * 100) if objective_total > 0 else 0

        return {
            "total": total,
            "objective_total": objective_total,
            "correct": correct_count,
            "score": score,
            "details": details,
        }

    def grade_short_answer(self, question_id: int, reference_context: str) -> str:
        """对简答题进行 AI 评判"""
        q = next((q for q in self.current_questions if q.id == question_id), None)
        if not q:
            return "题目不存在"

        user_ans = self.user_answers.get(question_id, "")
        prompt = f"""请评判以下简答题的回答质量。

【参考知识】
{reference_context}

【题目】
{q.stem}

【参考答案要点】
{q.answer}

【学生回答】
{user_ans}

请给出：
1. 评分（0-10分）
2. 评语（优点和不足）
3. 正确答案要点"""
        return self.generator.generate(prompt, context="")["answer"]

    def get_wrong_questions(self) -> List[dict]:
        """获取错题列表"""
        result = self.grade()
        return [d for d in result["details"] if d["is_correct"] is False]

    def reset(self):
        """重置测验状态"""
        self.current_questions = []
        self.user_answers = {}