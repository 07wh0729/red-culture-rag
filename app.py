"""
红色文化智能学习平台 - RAG 框架入口
支持两种运行模式：
  1. API 服务:  python app.py serve
  2. 命令行交互: python app.py cli
  3. 构建索引:   python app.py build
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.api import app as api_app
from src.rag_pipeline import RAGPipeline
import config


def cmd_build():
    """构建知识库索引"""
    pipe = RAGPipeline()
    pipe.build_index(clear_first=True)


def cmd_cli():
    """命令行交互模式"""
    pipe = RAGPipeline()

    print("\n" + "=" * 60)
    print("  红色文化智能学习平台 - RAG 问答")
    print("  命令: ask <问题> | quiz [主题] | explain <概念>")
    print("       build | status | quit")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "quit" or cmd == "exit":
            print("再见！")
            break
        elif cmd == "build":
            pipe.build_index(clear_first=True)
        elif cmd == "status":
            s = pipe.status()
            for k, v in s.items():
                print(f"  {k}: {v}")
        elif cmd == "ask":
            if not arg:
                print("用法: ask <问题>")
                continue
            print("\n思考中...")
            result = pipe.ask(arg, include_sources=True)
            if isinstance(result, dict):
                print(f"\n【回答】\n{result['answer']}")
                print(f"\n【参考来源】")
                for src in result.get("sources", []):
                    print(f"  - {src['source']}: {src['content'][:80]}...")
            else:
                print(f"\n{result}")
        elif cmd == "quiz":
            topic = arg if arg else "红色文化"
            print(f"\n正在生成'{topic}'相关题目...")
            result = pipe.quiz(topic=topic)
            print(f"\n{result}")
        elif cmd == "explain":
            if not arg:
                print("用法: explain <知识点>")
                continue
            print(f"\n讲解中...")
            result = pipe.explain(arg)
            print(f"\n{result}")
        elif cmd == "search":
            if not arg:
                print("用法: search <关键词>")
                continue
            docs = pipe.search_docs(arg)
            for i, d in enumerate(docs, 1):
                print(f"\n[{i}] {d.metadata.get('source', '')}")
                print(d.page_content[:300])
        else:
            print(f"未知命令: {cmd}")
            print("可用: ask / quiz / explain / search / build / status / quit")


def cmd_serve():
    """启动 API 服务"""
    import uvicorn
    print(f"\n  红色文化智能学习平台 API 服务")
    print(f"  地址: http://{config.API_HOST}:{config.API_PORT}")
    print(f"  文档: http://{config.API_HOST}:{config.API_PORT}/docs\n")
    uvicorn.run(
        "src.api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )


if __name__ == "__main__":
    usage = """
用法:
  python app.py build    构建/重建知识库索引
  python app.py cli      命令行交互模式
  python app.py serve    启动 API 服务
"""
    if len(sys.argv) < 2:
        print(usage)
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "build":
        cmd_build()
    elif mode == "cli":
        cmd_cli()
    elif mode == "serve":
        cmd_serve()
    else:
        print(f"未知模式: {mode}")
        print(usage)
        sys.exit(1)