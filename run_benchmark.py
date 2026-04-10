import os
import sys
from typing import List
from src import (
    Document,
    RecursiveChunker,
    EmbeddingStore,
    KnowledgeBaseAgent,
    LocalEmbedder,
    _mock_embed
)

# Đảm bảo output hiển thị đúng tiếng Việt trên Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_and_ingest(store: EmbeddingStore):
    chunker = RecursiveChunker(chunk_size=500)
    data_dir = "data_XanhSM"
    files = ["khach_hang.txt", "ĐIỀU KHOẢN CHUNG.txt"]
    
    all_chunks = []
    
    for filename in files:
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chunks = chunker.chunk(text)
        for i, content in enumerate(chunks):
            doc_id = f"{filename}_{i}"
            all_chunks.append(Document(
                id=doc_id,
                content=content,
                metadata={"source": filename, "doc_id": doc_id}
            ))
            
    print(f"Ingesting {len(all_chunks)} chunks into store...")
    store.add_documents(all_chunks)

def run_benchmark():
    # Sử dụng MockEmbedder để đảm bảo chạy được mà không cần GPU/Internet
    # Nếu muốn dùng thật, thay bằng LocalEmbedder()
    try:
        embedder = LocalEmbedder()
        print("Using LocalEmbedder (Sentence Transformers)")
    except Exception:
        embedder = _mock_embed
        print("Using MockEmbedder (Hash-based)")

    store = EmbeddingStore(embedding_fn=embedder)
    load_and_ingest(store)
    
    def mock_llm(prompt: str) -> str:
        # Giả lập câu trả lời của LLM bằng cách lấy thông tin từ dữ liệu đã tìm được
        # Trong thực tế, đây sẽ là call tới GPT/Claude/Gemini
        if "Context:" in prompt:
            # Lấy phần context đầu tiên để giả lập câu trả lời
            lines = prompt.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("[1]"):
                    return f"(Bản demo RAG) Dựa trên tài liệu: {lines[i+1][:200]}..."
        return "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong ngữ cảnh cung cấp."

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)
    
    queries = [
        {
            "q": "Khách hàng có thể hủy chuyến xe trong bao lâu mà không bị tính phí?",
            "gold": "Khách hàng có thể hủy chuyến miễn phí trong vòng 5 phút sau khi đặt xe."
        },
        {
            "q": "Tài xế cần cung cấp những giấy tờ gì khi đăng ký tham gia Xanh SM?",
            "gold": "Tài xế cần cung cấp bằng lái xe, CMND/CCCD, đăng ký xe và bảo hiểm còn hiệu lực."
        },
        {
            "q": "Xanh SM xử lý thông tin cá nhân của khách hàng như thế nào?",
            "gold": "Xanh SM bảo vệ dữ liệu cá nhân theo quy định pháp luật, không chia sẻ cho bên thứ ba nếu không có sự đồng ý."
        },
        {
            "q": "Quy trình giao hàng Xanh Express diễn ra như thế nào?",
            "gold": "Khách đặt đơn → tài xế nhận đơn → lấy hàng → giao hàng → xác nhận hoàn thành."
        },
        {
            "q": "Nhà hàng cần đáp ứng các tiêu chuẩn gì để hợp tác với Xanh SM?",
            "gold": "Nhà hàng cần đảm bảo vệ sinh thực phẩm, giấy phép kinh doanh hợp lệ và tuân thủ chính sách đối tác."
        }
    ]
    
    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    
    for i, item in enumerate(queries, 1):
        query = item['q']
        print(f"\nQuery {i}: {query}")
        
        # Retrieval
        results = store.search(query, top_k=1)
        if results:
            best_doc = results[0]
            score = best_doc.get('score', 0.0)
            chunk_text = best_doc['content']
            print(f"- Top-1 Score: {score:.4f}")
            print(f"- Retrieved Chunk: {chunk_text[:100]}...")
        else:
            print("- No results found.")
            
        # Generation
        answer = agent.answer(query)
        print(f"- Agent Answer: {answer[:150]}...")
        print("-" * 30)

if __name__ == "__main__":
    run_benchmark()
