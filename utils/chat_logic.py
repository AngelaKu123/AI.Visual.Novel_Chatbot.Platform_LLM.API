from typing import List, Tuple, Dict
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from utils.memory import MemoryManager

# ── instantiate a single MemoryManager ────────────────────────────────────────
memory = MemoryManager(model_name="llama3.2")


# ── Character Logic ──────────────────────────────────────────────────────────
def build_character_chain(ch: dict):
    """
    Returns an LLMChain that plays the character.
    """
    model = OllamaLLM(model="llama3")

    # static fields are f-stringed; {context} and {user_input} remain as ChatPromptTemplate slots
    prompt_text = f"""You are a character in a visual novel. You may respond in any style, but it must align with your character’s personality.

Character name: {ch['name']}
Character background: {ch.get('background', '')}
Persona: {ch['style']['description']}
Speaking style: {ch['style']['type']}

Context:
{{context}}
User: {{user_input}}
{ch['name']}: """

    prompt = ChatPromptTemplate.from_template(prompt_text)
    return prompt | model


def stream_character_reply(chain, context: str, user_input: str):
    """
    Stream tokens for the character’s reply.
    """
    return chain.stream({"context": context, "user_input": user_input})


# ── Narrator Logic ───────────────────────────────────────────────────────────
def build_narrator_chain(ch: dict):
    """
    Returns an LLMChain that plays the uncensored narrator.
    """
    model = OllamaLLM(model="llama3")  # or your uncensored model

    prompt_text = f"""
You are a narrator in a visual novel.

Your role is to describe the physical scene and the character's emotional actions.
Focus on body language, subtle changes in behavior, or shifts in tone.
Only describe; do NOT include any spoken dialogue.
Return output wrapped in asterisks, e.g. *She smiles and looks away.*

Character:
- Name: {ch['name']}
- Style: {ch['style']['type']}
- Description: {ch['style']['description']}

Conversation so far:
{{context}}

User just said:
{{user_input}}

Narrator:"""

    prompt = ChatPromptTemplate.from_template(prompt_text)
    return prompt | model


def stream_narration(chain, context: str, user_input: str):
    """
    Stream tokens for the narrator’s description.
    """
    return chain.stream({"context": context, "user_input": user_input})


# ── Context + Memory Helpers ─────────────────────────────────────────────────
def get_extended_context(raw_context: str, user_input: str) -> str:
    """
    Prefix the raw dialogue with the current rolling summary and
    the top-5 most relevant extracted facts.
    """
    # 1) Rolling summary
    mem_sum = memory.summary or "(no summary yet)"

    # 2) Top-5 relevant facts
    hits = memory.get_relevant_facts(user_input, top_k=5)
    if hits:
        facts_str = "\n".join(f"{f['type'].capitalize()}: {f['text']}" for f in hits)
    else:
        facts_str = "(no relevant facts)"

    prefix = (
        f"Memories summary:\n{mem_sum}\n\n"
        f"Relevant facts:\n{facts_str}\n\n"
    )
    return prefix + raw_context


def process_turn(
    character: dict,
    chain,
    narr_chain,
    raw_context: str,
    user_input: str
) -> Tuple[List[str], List[str], str]:
    """
    Do one full turn:
      1) Build extended context (with memory)
      2) Stream narrator → collect tokens
      3) Stream character → collect tokens
      4) Update memory (summary & facts)
      5) Return (narr_tokens, char_tokens, new_context)

    new_context is raw_context plus:
      "\n\nUser: {user_input}\n{character['name']}: {full_reply}"
    """
    # 1) Extend context
    ext_ctx = get_extended_context(raw_context, user_input)

    # 2) Narration
    narr_tokens = list(stream_narration(narr_chain, ext_ctx, user_input))

    # 3) Character reply
    char_tokens = list(stream_character_reply(chain, ext_ctx, user_input))
    full_reply = "".join(char_tokens)

    # 4) Update memory
    memory.update_summary(user_input, full_reply)
    memory.extract_facts(user_input, full_reply)

    from sd.prompt import generate_sd_prompt  #
    from utils.memory import MemoryManager  #
    mem = MemoryManager()  #
    result = generate_sd_prompt(mem)  #
    print(result)  #

    # 5) Append to raw context
    new_context = (
        raw_context
        + f"\n\nUser: {user_input}\n"
        + f"{character['name']}: {full_reply}"
    )

    return narr_tokens, char_tokens, new_context
