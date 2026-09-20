# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Thế Việt
**Nhóm:** TEN-NHU-CU
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) thể hiện hai vector embedding cùng chỉ về một hướng trong không gian đa chiều, phản ánh hai đoạn văn bản có sự tương đồng rất lớn về mặt ngữ nghĩa và chủ đề, không phụ thuộc vào độ dài câu hay số lượng từ vựng.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** *"Hôm nay trời mưa"*
- **Câu B:** *"Hôm nay trời không mưa"*
- **Tại sao tương đồng:** Về bản chất những từ ngữ đã được embedding thành vector, khi so sánh sự tương đồng thì mô hình embedding chủ yếu nắm bắt ý nghĩa theo cùng một chủ đề (chủ đề thời tiết mưa), chưa tách biệt sâu sắc thái phủ định đối nghịch giữa hai câu.

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** *"Hôm nay trời mưa"*
- **Câu B:** *"Thuật toán sắp xếp nhanh QuickSort có độ phức tạp trung bình là O(n log n)."*
- **Tại sao khác:** Hai câu thuộc hai chủ đề hoàn toàn độc lập (thời tiết đời sống vs cấu trúc dữ liệu giải thuật máy tính), vector embedding của chúng chỉ về các hướng trực giao nhau trong không gian vector.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Trong không gian vector nhiều chiều, khoảng cách Euclid bị chi phối bởi độ lớn của vector (liên quan trực tiếp đến độ dài văn bản và tần suất từ), trong khi Cosine Similarity chỉ xét góc giữa các vector, giúp đo lường mức độ tương đồng ngữ nghĩa thuần túy mà không bị ảnh hưởng bởi độ dài ngắn của đoạn text.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) giữa hai chunk liên tiếp: $step = chunk\_size - overlap = 500 - 50 = 450$ ký tự.
> - Áp dụng công thức tính số lượng chunk:
>   $$\text{Số chunks} = \left\lceil \frac{\text{độ\_dài\_tài\_liệu} - overlap}{chunk\_size - overlap} \right\rceil = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \lceil 22.11 \rceil = 23$$
> *(Kiểm chứng bằng thực nghiệm code: `len(FixedSizeChunker(500, 50).chunk('a'*10000))` ra đúng 23).*
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm còn $500 - 100 = 400$, số chunk tăng lên $\lceil (10000 - 100) / 400 \rceil = 25$ chunks. Chúng ta muốn tăng overlap để bảo toàn ngữ cảnh liền mạch giữa các ranh giới cắt, tránh việc các thực thể thông tin quan trọng (như con số, mốc thời hạn, tên sản phẩm) bị chia cắt làm đôi giữa hai chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy Lookbehind `re.split(r"(?<=[.!?])\s+|\n+", text.strip())` để tách các câu dựa theo dấu chấm, chấm than, hỏi chấm hoặc dấu xuống dòng mà không làm mất dấu câu cuối. Gom các câu thành từng nhóm tối đa `max_sentences_per_chunk` câu. Xử lý an toàn chuỗi rỗng/chỉ có khoảng trắng trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia đệ quy theo thứ tự ưu tiên separator: `["\n\n", "\n", ". ", " ", ""]`. Nếu đoạn văn bản dài hơn `chunk_size`, hàm gọi đệ quy với separator nhỏ hơn, sau đó gom (merge) các đoạn nhỏ liền kề lại cho tới khi đạt sát `chunk_size` để tránh sinh ra các mảnh vụn quá ngắn. Base case dừng lại khi đoạn văn bản $\le chunk\_size$ hoặc khi đã duyệt hết danh sách phân tách.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory dưới dạng danh sách các bản ghi `dict` gồm `id`, `content`, `metadata` (đảm bảo luôn gán `doc_id`) và vector `embedding`. Khi tìm kiếm (`search`), hàm tính tích vô hướng / độ tương đồng cosine giữa query vector với từng embedding trong store, sau đó sắp xếp giảm dần theo điểm và lấy Top-$k$.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc (pre-filter) danh sách tài liệu khớp với tất cả điều kiện trong `metadata_filter` **trước** khi tính điểm tương đồng, đảm bảo không bỏ sót các slot top-k hợp lệ. `delete_document` duyệt và xóa tất cả bản ghi có `id` hoặc `metadata['doc_id']` khớp với ID được yêu cầu và trả về `True` nếu có ít nhất 1 bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Triển khai kiến trúc RAG chuẩn: Lấy danh sách Top-$k$ chunks liên quan nhất từ `store.search()`, ghép nối thành phần ngữ cảnh `Context:\n...`, sau đó kết hợp với `Question:\n...` để tạo prompt có cấu trúc gửi cho hàm mô hình ngôn ngữ `llm_fn` sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
==================================== test session starts ====================================
platform win32 -- Python 3.13.x, pytest-8.x.x, pluggy-1.x.x
rootdir: d:\Vin_AI\K4-L3B--Day07-TheViet-2A202602594
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

==================================== 42 passed in 0.14s ====================================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua được đổi trả hàng trong 15 ngày | Khách hàng có thể hoàn trả sản phẩm trong vòng nửa tháng | cao | 0.88 | Đúng |
| 2 | Shopee nghiêm cấm bán hàng giả hàng nhái | Hướng dẫn cách làm món phở bò truyền thống | thấp | 0.05 | Đúng |
| 3 | Người bán bị phạt điểm Sao Quả Tạ do giao trễ | Đơn hàng giao không thành công bị trừ điểm vận hành shop | cao | 0.81 | Đúng |
| 4 | Quy định kiểm hàng đồng kiểm khi shipper giao | Cấu hình máy chủ Linux phục vụ phân tích dữ liệu | thấp | 0.09 | Đúng |
| 5 | Thời gian Shopee xử lý khiếu nại từ 3 đến 5 ngày | Yêu cầu trả hàng sẽ được giải quyết trong 3-5 ngày làm việc | cao | 0.93 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1 và cặp 5 cho điểm tương đồng rất cao dù từ vựng được thay thế hoàn toàn (*đổi trả / hoàn trả*, *15 ngày / nửa tháng*). Điều này chứng minh mô hình embedding mã hoá được tầng ngữ nghĩa trừu tượng của toàn câu thay vì chỉ so khớp từng từ khoá đơn lẻ (keyword matching) truyền thống.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` (Chiến lược: `RecursiveChunker` / `HeadingChunker`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho đơn hàng thực phẩm tươi sống là bao lâu? | Thời gian tối đa để gửi yêu cầu: Đơn hàng thực phẩm tươi sống & đông lạnh trong vòng 24 giờ kể từ lúc giao thành công... | 0.4153 | Có (Relevant) | Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái Giao hàng thành công. |
| 2 | Đơn hàng có giá trị trên bao nhiêu tiền thì KHÔNG được áp dụng chương trình Đồng kiểm? | Chương trình đồng kiểm KHÔNG áp dụng cho đơn hàng có giá trị lớn hơn 3.000.000 VND (3 Triệu Đồng)... | 0.3543 | Có (Relevant) | Đơn hàng có giá trị lớn hơn 3.000.000 VND (3 Triệu Đồng). |
| 3 | Người bán bị phạt bao nhiêu điểm Sao Quả Tạ nếu có tỷ lệ giao hàng trễ (LSR) từ 10% trở lên và trên 30 đơn? | Tỷ lệ giao hàng trễ (LSR): LSR ≥ 10% và ≥ 30 đơn hàng giao trễ: 2 điểm phạt... | 0.2887 | Có (Relevant) | Bị phạt 2 điểm Sao Quả Tạ. |
| 4 | Shop đăng bán sản phẩm hàng giả/hàng nhái trên Shopee sẽ phải chịu những chế tài xử lý nào? | Hậu quả khi vi phạm: Sản phẩm bị khóa/xóa, cộng điểm phạt Sao Quả Tạ, tạm thời đóng băng hoặc khóa tài khoản... | 0.3337 | Có (Relevant) | Khóa/xóa sản phẩm, phạt điểm Sao Quả Tạ, đóng băng hoặc khóa tài khoản bán hàng. |
| 5 | Thời hạn khiếu nại quyết định Trả hàng/Hoàn tiền là bao nhiêu ngày? *(Filter: `audience: buyer`)* | Thời gian tối đa gửi yêu cầu Trả hàng/Hoàn tiền: 15 ngày kể từ lúc đơn cập nhật trạng thái Giao hàng thành công... | 0.2911 | Có (Relevant) | Người mua có 15 ngày kể từ ngày nhận hàng. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp `HeadingChunker` (giữ tiêu đề điều khoản gắn liền với nội dung) và bộ lọc `metadata_filter={"audience": "buyer"}` là giải pháp tối ưu nhất cho văn bản chính sách thương mại điện tử, giúp tránh nhầm lẫn giữa quy định của Người mua và Người bán.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
