from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve relevant chunks
        records = self.store.search(question, top_k=top_k)

        if not records:
            return "I could not find relevant information to answer this question."

        # 2. Build context from retrieved chunks
        context_blocks = []
        for idx, r in enumerate(records, start=1):
            context_blocks.append(f"[{idx}]\n{r['content']}")

        context = "\n\n".join(context_blocks)

        prompt = (
            "You are a knowledgeable assistant. Use the context below to answer the question.\n\n"
            "Context:\n"
            f"{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 3. Call the LLM
        return self.llm_fn(prompt)