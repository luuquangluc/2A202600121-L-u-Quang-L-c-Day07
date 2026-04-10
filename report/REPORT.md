# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lưu Quang Lực - 2A202600121
**Nhóm:** D3-C401
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *High cosine similarity có nghĩa là các vector biểu diễn của văn bản hướng về cùng một phía trong không gian embedding, cho thấy chúng có sự tương đồng lớn về mặt ngữ nghĩa hoặc từ vựng.*

**Ví dụ HIGH similarity:**
- Sentence A: Tôi sắp ăn cơm
- Sentence B: Tôi sẽ ăn cơm
- Tại sao tương đồng: Có nhiều từ giống nhau, ý nghĩa cũng giống nhau

**Ví dụ LOW similarity:**
- Sentence A: Tôi không biết
- Sentence B: a^2 + b^2 = c^2
- Tại sao khác: Không có từ giống nhau, domain khác nhau

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity đo góc giữa hai vector, không phụ thuộc vào độ dài vector, trong khi Euclidean distance đo khoảng cách giữa hai vector, phụ thuộc vào độ dài vector

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Tổng số chunks = 1 + ceil((Tổng_kích_thước - Chunk_size) / (Chunk_size - Overlap)) = 1 + ceil((10000 - 500) / (500 - 50)) = 1 + ceil(9500 / 450) = 1 + ceil(21.11) = 1 + 22 = 23.
> *Đáp án:* 23 chunks.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:* Khi overlap lên 100 thì chunk count tăng lên 25. Muốn overlap nhiều hơn vì nó giúp bảo toàn ngữ cảnh giữa các chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** XanhSM

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:* Do chatbot sử dụng các tài liệu của XanhSM chưa tối ưu. Người dùng (tài xế) có nhiều nhu cầu để tìm hiểu về chính sách với các trường hợp cụ thể của cá nhân.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Chính sách bảo vệ dữ liệu cá nhân.txt | https://www.xanhsm.com/helps | 36,439 | category= chính sách, source=xanhsm.com |
| 2 | donhang.txt|https://www.xanhsm.com/news/so-tay-van-hanh-dich-vu-giao-hang-xanh-express |15,104 |category=quy trình , source=xanhsm.com |
| 3 | ĐIỀU KHOẢN CHUNG.txt|https://www.xanhsm.com/helps |208,756 |category= Điều khoản,dịch vụ, source=xanhsm.com|
| 4 |khach_hang.txt|https://www.xanhsm.com/terms-policies/general?terms=12 |52,702 |category = hỏi đáp hỗ trợ khách hàng, audience = khách hàng  |
| 5 |nhahang.txt|https://www.xanhsm.com/terms-policies/general?terms=10 |38,996 | category=chính sách nhà hàng, source=xanhsm.com |
|6  |tai_xe.txt | https://www.xanhsm.com/terms-policies/general?terms=6|11,424|category=điều khoản của tài xế, audience = tài xế|
### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|| category | string | `chính sách ` , `quy trình `,`Điều khoản ` | Lọc theo loại tài liệu, tránh trả về chunk không liên quan loại nội dung |
| source | string | `xanhsm.com` | Truy vết nguồn gốc tài liệu, hỗ trợ citation và kiểm tra độ tin cậy |
| audience | string | `tài xế`, `khách hàng ` | Lọc theo đối tượng người dùng, trả về nội dung phù hợp với từng nhóm |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| ĐIỀU KHOẢN CHUNG.txt | FixedSizeChunker (`fixed_size`) | 351 | 498.68 | Low (Dễ bị ngắt câu giữa chừng) |
| ĐIỀU KHOẢN CHUNG.txt | SentenceChunker (`by_sentences`) | 424 | 369.8 | High (Đảm bảo trọn vẹn câu) |
| ĐIỀU KHOẢN CHUNG.txt | RecursiveChunker (`recursive`) | 428 | 366.48 | High (Tốt cho cấu trúc văn bản pháp lý) |
| nhahang.txt | FixedSizeChunker (`fixed_size`) | 66 | 497.06 | Low |
| nhahang.txt | SentenceChunker (`by_sentences`) | 103 | 285.26 | High |
| nhahang.txt | RecursiveChunker (`recursive`) | 67 | 439.55 | Medium-High |

### Strategy Của Tôi

**Loại:** FixedSizeChunker

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: Strategy chia tài liệu thành các đoạn có độ dài cố định chunk_size, đoạn sau có overlap_size với đoạn trước. Làm như vậy cho đến khi đoạn cuối không đủ chunk_size thì dừng lại. Cần tìm chunk_size và overlap_size cho phù hợp để tránh mất ngữ nghĩa. 

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain này đơn giản, giúp tiếp cận và triển khai nhanh cho domain. 

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| ĐIỀU KHOẢN CHUNG.txt | Recursive (Best Baseline) | 428 | 366.48 | High (Hợp lý nhất cho văn bản pháp lý) |
| ĐIỀU KHOẢN CHUNG.txt | **FixedSize (Của tôi)** | 351 | 498.68 | Medium (Dễ bị cắt nhỏ thông tin quan trọng) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | FixedSizeChunker | 7/10 | Triển khai nhanh, ổn định cho chunk_size lớn | Dễ ngắt câu giữa chừng |
| Thành viên 2 | SentenceChunker | 8/10 | Giữ trọn vẹn ý nghĩa của từng câu | Số lượng chunk lớn, rời rạc |
| Thành viên 3 | RecursiveChunker | 9/10 | Cân bằng tốt giữa độ dài và cấu trúc | Phức tạp hơn trong cài đặt |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:* RecursiveChunker là tốt nhất cho domain XanhSM. Bởi vì các tài liệu chính sách thường có cấu trúc phân cấp rõ ràng theo Điều/Khoản, việc cắt theo cấu trúc giúp AI hiểu đúng ngữ cảnh pháp lý thay vì chỉ là các đoạn văn bản rời rạc.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])[\s\n]+` (kỹ thuật positive lookbehind) để tách văn bản thành các câu mà vẫn giữ lại dấu câu ở cuối. Thuật toán này xử lý các edge case như văn bản có nhiều dấu xuống dòng hoặc khoảng trắng dư thừa bằng cách lọc bỏ các đoạn rỗng sau khi tách.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Sử dụng thuật toán đệ quy để chia nhỏ văn bản theo danh sách ký tự phân tách ưu tiên (đoạn văn, dòng, câu, từ). Nếu một đoạn vẫn vượt quá `chunk_size`, nó sẽ được chia nhỏ tiếp bằng dấu phân tách ở mức độ thấp hơn. Base case là khi đoạn văn bản đã đủ nhỏ hoặc khi không còn dấu phân tách nào để thử.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` thực hiện nhúng văn bản và lưu trữ vào ChromaDB (hoặc danh sách trong bộ nhớ). Hàm `search` chuyển đổi query thành vector và tìm kiếm top-k kết quả dựa trên độ tương đồng Cosine (tính toán qua hàm `_dot` vì vector đã chuẩn hóa).

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` thực hiện lọc dữ liệu theo metadata (pre-filtering) trước khi tính toán score để đảm bảo hiệu suất. `delete_document` xóa toàn bộ các chunk dựa trên trường `doc_id` được lưu trong metadata của mỗi bản ghi.

### KnowledgeBaseAgent

**`answer`** — approach:
> Triển khai mô hình RAG tiêu chuẩn: Tra cứu thông tin liên quan từ knowledge base, định dạng kết quả thành danh sách ngữ cảnh được đánh số, và đưa vào template prompt để LLM trả lời dựa trên nội dung đó.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.8.5, pytest-8.3.5, pluggy-1.5.0 -- c:\users\thinkpad\anaconda3\python.exe
cachedir: .pytest_cache
rootdir: D:\luc\Luc_Lenovo\Study\AI_thuc_chien_3_10\2A202600121-L-u-Quang-L-c-Day07
plugins: anyio-4.2.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

======================== 42 passed, 1 warning in 0.18s ========================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi sắp ăn cơm | Tôi sẽ ăn cơm | high | 0.6966 | Yes |
| 2 | Tôi không biết | "a^2 + b^2 = c^2" | low | 0.052 | Yes |
| 3 | Tôi biết rất rõ | Tôi không biết gì cả | low | 0.61 | No |
| 4 | a^2 + b^2 = c^2 | !^$&((%)(*%#)) | low | 0.07 | Yes |
| 5 | Tôi muốn ăn cơm | Tôi muốn ngủ | high | 0.74 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> * Câu phủ định và câu khẳng định vẫn có similarity cao. Muốn có giá trị gần 0 thì 2 câu phải thuộc 2 domain xa nhau, đặc biệt với ký tự toán học.*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Khách hàng có thể hủy chuyến xe trong bao lâu mà không bị tính phí? | Khách hàng có thể hủy chuyến miễn phí trong vòng 5 phút sau khi đặt xe. |
| 2 | Tài xế cần cung cấp những giấy tờ gì khi đăng ký tham gia Xanh SM? | Tài xế cần cung cấp bằng lái xe, CMND/CCCD, đăng ký xe và bảo hiểm còn hiệu lực. |
| 3 | Xanh SM xử lý thông tin cá nhân của khách hàng như thế nào? | Xanh SM bảo vệ dữ liệu cá nhân theo quy định pháp luật, không chia sẻ cho bên thứ ba nếu không có sự đồng ý. |
| 4 | Quy trình giao hàng Xanh Express diễn ra như thế nào? | Khách đặt đơn → tài xế nhận đơn → lấy hàng → giao hàng → xác nhận hoàn thành. |
| 5 | Nhà hàng cần đáp ứng các tiêu chuẩn gì để hợp tác với Xanh SM? | Nhà hàng cần đảm bảo vệ sinh thực phẩm, giấy phép kinh doanh hợp lệ và tuân thủ chính sách đối tác. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khách hàng có thể hủy...| "Để làm rõ, Tài liệu là loại Hàng hóa mang tin bao gồm văn bản..." | 0.7848 | No | Dựa trên tài liệu: Thông tin về hủy chuyến không được đề cập rõ ràng trong đoạn này... |
| 2 | Tài xế cần giấy tờ gì? | "1.10. “Tài Khoản Ứng Dụng” hay “TKUD” là tài khoản định danh..." | 0.7284 | No | Dựa trên tài liệu: Tài khoản ứng dụng là tài khoản định danh của người sử dụng... |
| 3 | Xử lý thông tin cá nhân? | "3.1.4. Chịu trách nhiệm về tính chính xác và đầy đủ của thông tin..." | 0.7604 | Partial | Dựa trên tài liệu: Người dùng chịu trách nhiệm về tính chính xác của thông tin nhập trên ứng dụng... |
| 4 | Quy trình Xanh Express? | "Xanh SM cam kết sẽ nghiêm túc kiểm tra và làm việc với tài xế..." | 0.6631 | Partial | Dựa trên tài liệu: Xanh SM cam kết kiểm tra và xử lý thích đáng các sai phạm của tài xế... |
| 5 | Nhà hàng hợp tác? | "4.2.3. Cam đoan và bảo đảm rằng Bạn đã đóng gói Hàng hoá..." | 0.8076 | Yes | Dựa trên tài liệu: Đối tác cần cam đoan việc đóng gói hàng hoá đúng quy cách và phù hợp đặc tính... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Qua thảo luận, tôi nhận ra tầm quan trọng của việc lựa chọn `RecursiveChunker` thay vì `FixedSizeChunker` đối với các tài liệu pháp lý phức tạp. Việc này giúp giữ trọn vẹn ngữ cảnh của các điều khoản, tránh tình trạng thông tin bị cắt nửa chừng gây hiểu lầm.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Tôi thấy các nhóm khác sử dụng 50 câu hỏi. Sử dụng nhiều metric để đo các phương pháp. Các Metric áp dụng cho retrieval. 

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ tập trung nhiều hơn vào việc làm sạch dữ liệu (data cleaning) trước khi đưa vào hệ thống, loại bỏ các phần tiêu đề lặp lại (header/footer). Ngoài ra, tôi muốn áp dụng `DocumentStructureChunker` tùy chỉnh riêng cho format của XanhSM để đảm bảo không một điều khoản nào bị chia cắt.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 3 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 7 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **82 / 90** |
