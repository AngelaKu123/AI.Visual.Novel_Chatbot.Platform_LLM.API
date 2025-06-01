# utils/prompt_generator.py

import os
import json
from pathlib import Path
from typing import Optional
from utils.memory import MemoryManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM


def generate_sd_prompt(
    mem: MemoryManager,
    model_name: str = "llama3",
    ch_name: str = "",
    ch_lora: str = "",
    output_dir: Optional[Path | str] = None,
    filename: str = "prompt.json"
) -> dict:
    """
    根據 MemoryManager 中的 summary 與 fact_memory
    使用 LLaMA3 產生一份適用於 Stable Diffusion 的 prompt JSON，
    並將結果儲存到磁碟上。路徑可由 `output_dir` 參數或環境變數 SD_PROMPT_DIR
    控制，否則預設寫入 <project_root>/sd/prompt.json。
    """

    # ── 1) 抓記憶 ────────────────────────────────────────────────────────
    summary = mem.summary
    facts = mem.fact_memory[-5:]
    fact_str = "\n".join(f"{item['type']}: {item['text']}" for item in facts)

    # ── 2) 建立 prompt template ─────────────────────────────────────────
    prompt_template = ChatPromptTemplate.from_template(f"""
You are a helpful assistant generating prompts for image generation via Stable Diffusion.

Your task:
- Output a JSON object with one key: "prompt".
- The "prompt" field must be a **comma-separated list of tags**.
- Tags should describe setting, lighting, emotion, style, etc.
- The output must be **valid JSON**. Do NOT include explanations.

Conversation summary:
{summary}

Extracted facts and inspiration:
{fact_str}
""")

    # ── 3) 呼叫 LLaMA3 模型 ───────────────────────────────────────────────
    chain = prompt_template | OllamaLLM(model=model_name)
    response = chain.invoke({
        # these keys won’t matter since we inlined summary & fact_str via f-string,
        # but kept here if you switch back to dynamic placeholders:
        "summary": summary,
        "fact_list": fact_str
    })

    # ── 4) 嘗試轉成 JSON 並後製 ─────────────────────────────────────────
    try:
        result = json.loads(response)

        # prepend character + LoRA tags
        ch_marker = f"((({ch_name})))" if ch_name else ""
        lora_tag = f"<lora:{ch_lora}:1>" if ch_lora else ""
        raw_prompt = result.get("prompt", "").strip()
        new_prompt = ", ".join(filter(None, [ch_tag, lora_tag, raw_prompt]))
        result["prompt"] = new_prompt

        # ── 5) 決定輸出路徑 ───────────────────────────────────────────────
        #  a) caller override
        if output_dir:
            sd_folder = Path(output_dir)
        else:
            # b) env var override
            env = os.environ.get("SD_PROMPT_DIR")
            if env:
                sd_folder = Path(env)
            else:
                # c) default: <project_root>/sd
                project_root = Path(__file__).resolve().parent.parent
                sd_folder = project_root / "sd"

        sd_folder.mkdir(parents=True, exist_ok=True)
        output_path = sd_folder / filename

        # ── 6) 寫檔 ────────────────────────────────────────────────────
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"✅ The generated prompt has been saved to -> {output_path.resolve()}")
        return result

    except json.JSONDecodeError:
        print("⚠️ The model output is not valid JSON:")
        print(response)
        return {"prompt": ""}
