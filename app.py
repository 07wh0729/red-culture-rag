"""
红色文化智能学习平台 v2 - 入口
模式: python app.py serve | build | cli
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import config


def cmd_build():
    from src.rag_pipeline import RAGPipeline
    pipe = RAGPipeline()
    pipe.build_index(clear_first=True)


def cmd_cli():
    from src.rag_pipeline import RAGPipeline
    pipe = RAGPipeline()
    print("\n" + "=" * 60)
    print("  红色文化智能学习平台 v2 - 命令行")
    print("  命令: ask <问题> | quiz [主题] | explain <概念>")
    print("       media | build | status | quit")
    print("=" * 60 + "\n")
    while True:
        try:
            user_input = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not user_input: continue
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        if cmd in ("quit", "exit"):
            print("再见！"); break
        elif cmd == "build":
            pipe.build_index(clear_first=True)
        elif cmd == "status":
            s = pipe.status()
            for k, v in s.items(): print(f"  {k}: {v}")
        elif cmd == "ask":
            if not arg: print("用法: ask <问题>"); continue
            print("\n思考中...")
            result = pipe.ask(arg)
            print(f"\n【回答】\n{result['answer']}")
            print(f"\n【来源】")
            for src in result.get("sources", []):
                print(f"  - {src['source']}")
        elif cmd == "quiz":
            topic = arg if arg else "红色文化"
            print(f"\n生成'{topic}'题目...")
            r = pipe.quiz_generate(topic)
            print(f"生成了 {r['total']} 道题")
        elif cmd == "explain":
            if not arg: print("用法: explain <知识点>"); continue
            r = pipe.explain(arg)
            print(f"\n{r['explanation']}")
        elif cmd == "media":
            items = pipe.media_list()
            for m in items[:10]:
                print(f"  [{m['type']}] {m['title']} ({m['id']})")
        elif cmd == "search":
            if not arg: print("用法: search <关键词>"); continue
            docs = pipe.search_docs(arg)
            for i, d in enumerate(docs, 1):
                print(f"\n[{i}] {d['source']}\n{d['content'][:300]}")
        else:
            print(f"未知命令: {cmd}")


def cmd_serve():
    import uvicorn
    print(f"\n  🚩 红色文化智能学习平台 v2.0")
    print(f"  学习中心: http://{config.API_HOST}:{config.API_PORT}")
    print(f"  后台管理: http://{config.API_HOST}:{config.API_PORT}/admin")
    print(f"  API 文档: http://{config.API_HOST}:{config.API_PORT}/docs\n")
    uvicorn.run("src.api:app", host=config.API_HOST, port=config.API_PORT, reload=False)


if __name__ == "__main__":
    usage = """
红色文化智能学习平台 v2
用法: python app.py serve  |  build  |  cli
"""
    if len(sys.argv) < 2:
        print(usage); sys.exit(1)
    mode = sys.argv[1].lower()
    {"build": cmd_build, "cli": cmd_cli, "serve": cmd_serve}.get(mode, lambda: (print(f"未知: {mode}"), print(usage)))()