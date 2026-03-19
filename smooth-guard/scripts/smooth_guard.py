import sys
import pathlib
import httpx
import re
import uuid
import time
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool


repo_root = str(pathlib.Path(__file__).resolve().parents[1])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from lib.defenses import smoothllm

app = FastAPI()

VLLM_URL = "http://127.0.0.1:8001/v1/chat/completions"  # 你正在运行 Qwen3 的后端
TARGET_MODEL_NAME = "local_vllm_Qwen3-1.7B"
DISGUISE_NAME = "smooth/local_vllm_Qwen3-1.7B"
BLOCK_MESSAGE = "⚠️ **[Smooth-Guard 拦截]** 您的请求疑似越狱攻击，已被防御层阻断。"

# 建立长连接池
timeout_settings = httpx.Timeout(10.0, read=300.0, connect=10.0)
client_pool = httpx.AsyncClient(timeout=timeout_settings)


def get_pure_user_text(payload):
    """
    提纯函数：从 OpenClaw 的复杂元数据中提取用户原话
    """
    try:
        if "messages" in payload and len(payload["messages"]) > 0:
            content = payload["messages"][-1].get("content", "")
            if isinstance(content, list):
                raw_text = next((item["text"] for item in content if item.get("type") == "text"), "")
            else:
                raw_text = content

            # 过滤时间戳
            clean_text = re.sub(r'\[.*?GMT\+8\]', '', raw_text).strip()
            # 过滤 JSON 块
            if "```json" in clean_text:
                clean_text = clean_text.split("```")[-1].strip()

            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
            return lines[-1] if lines else "Hi"
    except:
        return "Hi"
    return "Hi"


@app.post("/v1/chat/completions")
async def smooth_proxy(request: Request):
    payload = await request.json()
    is_stream = payload.get("stream", False)

    # 提纯用户输入
    pure_text = get_pure_user_text(payload)
    print(f"\n�� [提纯内容] 用户原话: '{pure_text}'")

    # smooth-guard 扰动防御审计
    print(f"��️ [防御层审计中] 运行随机扰动 + 多数投票...")

    try:
        defense_result = await run_in_threadpool(
            smoothllm,
            prompt=pure_text,
            pert_type="RandomInsertPerturbation",
            pert_pct=10,
            num_copies=3,
            vllm_endpoint=VLLM_URL,
            max_new_tokens=100  # 审计不需要太长
        )
        is_safe = defense_result.get("verdict") == "safe"

        if not is_safe:
            print(f"�� [拦截] Smooth-LLM 判定为越狱攻击！")
            return JSONResponse(content={
                "id": f"blk-{uuid.uuid4()}",
                "model": DISGUISE_NAME,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": BLOCK_MESSAGE},
                    "finish_reason": "stop"
                }]
            })
    except Exception as e:
        print(f"⚠️ 防御层异常: {e}, 自动放行...")

    # safe，转发原始请求给 vllm
    print(f"✅ [放行] 正在转发完整请求并执行流式伪装...")
    payload["model"] = TARGET_MODEL_NAME

    try:
        req = client_pool.build_request("POST", VLLM_URL, json=payload)
        target_resp = await client_pool.send(req, stream=is_stream)

        if is_stream:
            async def disguise_streamer():
                try:
                    async for chunk in target_resp.aiter_lines():
                        if not chunk: continue
                        if chunk.startswith("data: "):
                            if chunk == "data: [DONE]":
                                yield b"data: [DONE]\n\n"
                                break

                            chunk_str = chunk.replace(TARGET_MODEL_NAME, DISGUISE_NAME)
                            yield (chunk_str + "\n\n").encode('utf-8')
                except Exception as e:
                    print(f"⚠️ [流中断] {e}")
                finally:
                    await target_resp.aclose()
                    print("✨ [完成]")

            return StreamingResponse(disguise_streamer(), media_type="text/event-stream")
        else:
            rj = target_resp.json()
            if "model" in rj: rj["model"] = DISGUISE_NAME
            print("✨ [完成]")
            return JSONResponse(content=rj)

    except Exception as e:
        print(f"❌ 转发失败: {e}")
        return JSONResponse(content={"error": "Backend vLLM Offline"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 50)
    print("��️  Smooth-Guard for OpenClaw 已启动")
    print("=" * 50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")