import os
from utils.memory import MemoryManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import json


def generate_sd_prompt(mem: MemoryManager, model_name="llama3", ch_name: str = "") -> dict:
    """
    根據 MemoryManager 中的 summary 與 fact_memory
    使用 LLaMA3 產生一份適用於 Stable Diffusion 的 prompt JSON。
    """

    # Step 1: 抓記憶
    summary = mem.summary
    facts = mem.fact_memory[-5:]  # 抓最後5筆就好（可依需求調整）
    fact_str = "\n".join([f"{item['type']}: {item['text']}" for item in facts])

    # Step 2: 建立 prompt template
    ch_marker = f"((({ch_name})))" if ch_name else ""
    prompt_template = ChatPromptTemplate.from_template(f"""
You are a helpful assistant generating prompts for image generation via Stable Diffusion.

Your task:
- Output a JSON object with three keys: "prompt", "negative_prompt", and "style".
- The "prompt" field must be a **comma-separated list of tags** (Stable Diffusion format). Do NOT use full sentences.
- Tags should describe the setting, lighting, emotion, style, etc.
- The output must be **valid JSON**. Do NOT include explanations or greetings.

Conversation summary:
{summary}

Extracted facts and inspiration:
{fact_str}
""")

    # Step 3: 呼叫 LLaMA3 模型
    chain = prompt_template | OllamaLLM(model=model_name)
    response = chain.invoke({
        "summary": summary,
        "fact_list": fact_str
    })

    # Step 4: 嘗試轉成 JSON 格式
    try:
        result = json.loads(response)
        # === STEP 4-1: 後製加工 Stable Diffusion Prompt ===
        # 插入角色名 + LoRA tag，格式如： "((([洛埕]))), <lora:洛埕:1>, ..." 
        ch_tag = f"((({ch_name})))" if ch_name else ""
        lora_tag = f"<lora:{ch_name}:1>" if ch_name else ""

        # 取出原本的模型回傳 prompt（仍為逗號分隔），再手動 prepend
        raw_prompt = result.get("prompt", "")
        new_prompt = ", ".join(filter(None, [ch_tag, lora_tag, raw_prompt.strip()]))

        result["prompt"] = new_prompt

        output_path = r"C:\Users\USER\Project\chatbot\sd\prompt.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ The generated prompt has been saved to -> {os.path.abspath(output_path)}")
        return result
    except json.JSONDecodeError:
        print("⚠️ The model output is not valid JSON: ")
        print(response)
        return {
            "prompt": "",
            "negative_prompt": "",
            "style": ""
        }