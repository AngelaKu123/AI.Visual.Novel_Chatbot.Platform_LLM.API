# Updated utils/memory.py with RunnableSequence.invoke fixes

import json
from typing import List, Dict
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


class MemoryManager:
    """
    Manages a rolling summary and a simple key–value store of extracted facts/feelings.
    """

    def __init__(self, model_name: str = "llama3"):
        # ── Summary chain ─────────────────────────────────────────────────
        self.summary = ""
        summary_tpl = ChatPromptTemplate.from_template(
            """Here is the current story summary:
{old_summary}

The conversation just added:
User: {user_input}
Assistant: {assistant_reply}

Please provide a concise, one-paragraph UPDATED summary that includes any new facts or emotional shifts."""
        )
        self._summary_chain = summary_tpl | OllamaLLM(model=model_name)

        # ── Extraction chain ────────────────────────────────────────────────
        extract_tpl = ChatPromptTemplate.from_template(
            """Conversation update:
User: {user_input}
Assistant: {assistant_reply}

List any new facts or feelings in JSON, like:
[
  {{ "type": "fact", "text": "…" }},
  {{ "type": "feeling", "text": "…" }}
]"""
        )
        self._extract_chain = extract_tpl | OllamaLLM(model=model_name)

        # In-memory store
        self.fact_memory: List[Dict[str, str]] = []

    def update_summary(self, user_input: str, assistant_reply: str) -> str:
        """
        Calls the summarization chain to roll your summary forward.
        """
        # Use invoke instead of run on the RunnableSequence
        new_sum = self._summary_chain.invoke({
            "old_summary":     self.summary,
            "user_input":      user_input,
            "assistant_reply": assistant_reply
        })
        self.summary = new_sum.strip()
        return self.summary

    def extract_facts(self, user_input: str, assistant_reply: str) -> List[Dict[str, str]]:
        """
        Calls the extraction chain to pull out discrete facts & feelings.
        """
        # Use invoke instead of run on the RunnableSequence
        raw = self._extract_chain.invoke({
            "user_input":      user_input,
            "assistant_reply": assistant_reply
        })
        try:
            items = json.loads(raw)
            # only keep well-formed entries
            valid = [i for i in items 
                     if isinstance(i, dict) and "type" in i and "text" in i]
            self.fact_memory.extend(valid)
            return valid
        except json.JSONDecodeError:
            return []

    def get_relevant_facts(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        """
        Naïve keyword lookup: return the first top_k facts whose text
        contains any word from `query`. Adaptable to embeddings.
        """
        qwords = set(query.lower().split())
        hits = [f for f in self.fact_memory
                if any(w in f["text"].lower() for w in qwords)]
        return hits[:top_k]

    def trim_context(self, turns: List[str], max_turns: int = 20) -> List[str]:
        """
        Keep only the last `max_turns` messages.
        """
        return turns[-max_turns:]

