from utils.memory import MemoryManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import json
import os


def generate_sd_prompt(mem: MemoryManager, model_name="llama3", output_path: str | None = None) -> dict:
    """
    根據 MemoryManager 中的 summary 與 fact_memory
    使用 LLaMA3 產生一份適用於 Stable Diffusion 的 prompt JSON。
    """

    # Step 1: 抓記憶
    summary = mem.summary
    facts = mem.fact_memory[-5:]  # 抓最後5筆就好（可依需求調整）
    fact_str = "\n".join([f"{item['type']}: {item['text']}" for item in facts])

    # Step 2: 建立 prompt template
    prompt_template = ChatPromptTemplate.from_template("""
Please use the following information to generate an image prompt suitable for Stable Diffusion. Please output in JSON format, including:
- prompt: 

Conversation summary:
{summary}

Extracted facts and inspiration:
{fact_list}
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
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"✅ 已將生成的 prompt 存至 {os.path.abspath(output_path)}")
        return result
    except json.JSONDecodeError:
        print("⚠️ 模型輸出不是合法 JSON: ")
        print(response)
        return {
            "prompt": "",
            "negative_prompt": "",
            "style": ""
        }
