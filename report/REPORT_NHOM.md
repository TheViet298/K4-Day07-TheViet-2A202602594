# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** TEN-NHU-CU
**Thành viên:** 
1. **Ngô Thế Việt** (Nhóm trưởng / Core Implementation Lead)
2. **Nguyễn Văn Giáp** (Data & Benchmark Lead)
3. **Nguyễn Quang Đạo** (Strategy & Heading Chunker Lead)
4. **Phùng Đình Triển** (Report & Demo Lead)
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Đổi trả, Hoàn tiền, Bảo hành, Đồng kiểm và Quy định Người bán/Người mua trên Nền tảng Thương mại Điện tử Shopee.

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề chính sách TMĐT Shopee vì đây là sàn thương mại điện tử lớn nhất tại Việt Nam với lượng chính sách rất đa dạng, có ranh giới rõ ràng giữa quyền lợi Người mua (`buyer`) và trách nhiệm Người bán (`seller`). Đặc biệt, tài liệu có nhiều mốc thời gian (24h, 2 ngày, 15 ngày), con số (hạn mức 3.000.000đ) và các chế tài xử phạt giúp đánh giá chính xác năng lực truy xuất thông tin của mô hình RAG.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Những điều cần biết về Trả hàng do Đổi ý không còn nhu cầu | `help.shopee.vn/.../204305` | 2026-09-20 / not-stated | ~10,200 | `audience: buyer`, `category: returns-policy` |
| 2 | Những quy định chung về Trả hàng/Hoàn tiền của Shopee | `help.shopee.vn/.../188931` | 2026-09-20 / not-stated | ~9,000 | `audience: buyer`, `category: returns-policy` |
| 3 | Sản phẩm hạn chế trả hàng là gì? | `help.shopee.vn/.../79465` | 2026-09-20 / not-stated | ~2,400 | `audience: buyer`, `category: returns-policy` |
| 4 | Chính sách bảo hành sản phẩm của Shopee | `help.shopee.vn/.../79046` | 2026-09-20 / not-stated | ~6,000 | `audience: buyer`, `category: warranty-policy` |
| 5 | Quy định và hướng dẫn Đồng kiểm khi nhận hàng | `banhang.shopee.vn/.../18454` | 2026-09-20 / 30-07-2025 | ~7,400 | `audience: both`, `category: shipping-policy` |
| 6 | Quy định về Hàng Giả/Nhái trên Shopee | `banhang.shopee.vn/.../1858` | 2026-09-20 / 09-09-2026 | ~2,700 | `audience: seller`, `category: compliance-policy` |
| 7 | Quy định về Hệ thống điểm phạt Sao Quả Tạ cho Người bán | `banhang.shopee.vn/.../2433` | 2026-09-20 / 11-06-2024 | ~4,400 | `audience: seller`, `category: seller-penalty` |
| 8 | Hướng dẫn Người bán khiếu nại yêu cầu Trả hàng/Hoàn tiền | `banhang.shopee.vn/.../3647` | 2026-09-20 / 03-11-2025 | ~4,800 | `audience: seller`, `category: seller-policy` |
| 9 | Chính sách Trả hàng và Hoàn tiền của Shopee | `help.shopee.vn/.../77251` | 2026-09-20 / not-stated | ~26,000 | `audience: both`, `category: returns-policy` |
| 10 | Những quy định chung về Trả hàng/Hoàn tiền cho Người mua | `help.shopee.vn/.../79256` | 2026-09-20 / 24-11-2025 | ~5,400 | `audience: buyer`, `category: returns-policy-for-buyer` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `shopee-he-thong-sao-qua-ta` | Định danh tài liệu nguồn, phục vụ việc truy vết nguồn và xóa/cập nhật tài liệu. |
| `audience` | `str` | `buyer`, `seller`, `both` | **Ràng buộc riêng của L3B:** Phân định rõ đối tượng áp dụng để tránh lẫn lộn quyền lợi người mua vs trách nhiệm người bán. |
| `category` | `str` | `returns-policy`, `seller-penalty` | Lọc theo nhóm chính sách chuyên biệt (đổi trả, bảo hành, xử phạt, vận chuyển). |
| `document_version` | `str` | `30-07-2025`, `not-stated` | Xác định phiên bản và tính hiệu lực thời gian của chính sách. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính sách Shopee:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-chinh-sach-dong-kiem.md` | FixedSizeChunker (`fixed_size`) | 12 chunks | ~180 ký tự | Kém (bị cắt ngang câu và bảng điều khoản) |
| `shopee-chinh-sach-dong-kiem.md` | SentenceChunker (`by_sentences`) | 18 chunks | ~110 ký tự | Khá (giữ trọn vẹn câu nhưng mất liên kết giữa các mục) |
| `shopee-chinh-sach-dong-kiem.md` | RecursiveChunker (`recursive`) | 8 chunks | ~250 ký tự | Tốt (giữ được cấu trúc đoạn và danh mục loại trừ) |

### Chiến lược của từng thành viên

**Thành viên 1 — Ngô Thế Việt (Core Lead)**
- **Loại chiến lược:** `RecursiveChunker` (chunk_size=350)
- **Mô tả & lý do chọn cho chủ đề này:** Tách đệ quy từ cấp đoạn văn (`\n\n`) xuống dòng (`\n`) và câu (`. `), giúp bảo toàn cấu trúc phân cấp điều khoản của văn bản chính sách Shopee.

**Thành viên 2 — Nguyễn Văn Giáp (Data & Benchmark Lead)**
- **Loại chiến lược:** `SentenceChunker` (max_sentences_per_chunk=2)
- **Mô tả & lý do chọn:** Cắt văn bản thành từng cặp 2 câu liên tiếp nhằm tập trung vào từng phát biểu/quy định cụ thể, tránh việc chunk quá dài làm loãng vector embedding.

**Thành viên 3 — Nguyễn Quang Đạo (Strategy Lead - R3)**
- **Loại chiến lược:** `HeadingChunker` (Custom Chunker theo Heading Markdown `#`, `##`, `###`)
- **Mô tả & lý do chọn:** Tách văn bản chính sách theo từng tiêu đề điều khoản. Khi một điều khoản quá dài cần chia nhỏ, tiêu đề mục luôn được tự động gắn lại vào đầu mỗi sub-chunk để giữ nguyên ngữ cảnh.
- **Code snippet:**
```python
class HeadingChunker:
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive_fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = re.split(r"(?m)(?=^#{1,3}\s+)", text.strip())
        chunks: list[str] = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                header = lines[0] if lines else ""
                body = lines[1] if len(lines) > 1 else ""
                sub_chunks = self.recursive_fallback.chunk(body)
                for sub in sub_chunks:
                    chunks.append(f"{header}\n{sub}".strip())
        return chunks
```

**Thành viên 4 — Phùng Đình Triển (Report & Demo Lead)**
- **Loại chiến lược:** `FixedSizeChunker` (chunk_size=300, overlap=30)
- **Mô tả & lý do chọn:** Dùng làm chiến lược đối chứng (baseline) để so sánh xem việc cắt cố định theo ký tự bị suy giảm chất lượng truy xuất ra sao so với các phương pháp theo ngữ nghĩa.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phùng Đình Triển | `FixedSizeChunker` | 2/10 | Đơn giản, tốc độ thực thi nhanh | Hay cắt cụt câu và tiêu đề, điểm thấp nhất |
| Nguyễn Văn Giáp | `SentenceChunker` | 6/10 | Chunk ngắn, câu hoàn chỉnh | Thiếu tiêu đề mục điều khoản dẫn dắt |
| Ngô Thế Việt | `RecursiveChunker` | 8/10 | Giữ khối ngữ cảnh tự nhiên rất tốt | Đôi khi gom thừa các câu không liên quan |
| Nguyễn Quang Đạo | `HeadingChunker` | **10/10** | **Tối ưu nhất**: Bảo toàn tiêu đề mục và nội dung đi kèm | Phụ thuộc vào chất lượng format Markdown ban đầu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`HeadingChunker` là chiến lược tối ưu nhất.** Đối với các tài liệu chính sách, mỗi tiêu đề mục (`### 1.2. Thời gian tối đa...`) mang ý nghĩa ngữ cảnh quyết định. Việc giữ tiêu đề gắn kèm nội dung giúp mô hình embedding xác định chính xác mục tiêu truy vấn ngay cả khi câu hỏi dùng từ ngữ khái quát.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho đơn hàng thực phẩm tươi sống là bao lâu? | Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái "Giao hàng thành công". | `shopee-returns-policy-for-buyer#0` / `general-returns-policy#0` |
| 2 | Đơn hàng có giá trị trên bao nhiêu tiền thì KHÔNG được áp dụng chương trình Đồng kiểm? | Đơn hàng có giá trị lớn hơn 3.000.000 VND (3 Triệu Đồng). | `shopee-chinh-sach-dong-kiem#1` |
| 3 | Người bán bị phạt bao nhiêu điểm Sao Quả Tạ nếu có tỷ lệ giao hàng trễ (LSR) từ 10% trở lên và trên 30 đơn? | 2 điểm phạt Sao Quả Tạ. | `shopee-he-thong-sao-qua-ta#1` |
| 4 | Shop đăng bán sản phẩm hàng giả/hàng nhái trên Shopee sẽ phải chịu những chế tài xử lý nào? | Sản phẩm bị khóa/xóa, cộng điểm phạt Sao Quả Tạ, tạm thời đóng băng hoặc khóa vĩnh viễn tài khoản. | `shopee-chinh-sach-hang-cam-va-hang-gia#1` |
| 5 | Thời hạn khiếu nại quyết định Trả hàng/Hoàn tiền là bao nhiêu ngày? *(Cần filter: `audience: buyer`)* | Người mua có 15 ngày kể từ ngày giao hàng; Người bán có 2 ngày kể từ khi nhận được thông báo để khiếu nại. | `shopee-returns-policy-for-buyer#0` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn đơn thực phẩm tươi sống | `HeadingChunker` | Có (Top-1) | Trả về chính xác mốc 24 giờ |
| 2 | Hạn mức không được Đồng kiểm | `HeadingChunker` / `Recursive` | Có (Top-1) | Trả về đúng con số 3.000.000 VNĐ |
| 3 | Điểm phạt giao hàng trễ LSR | `HeadingChunker` | Có (Top-1) | Trích xuất chuẩn mức phạt 2 điểm |
| 4 | Chế tài xử lý bán Hàng giả/nhái | `HeadingChunker` | Có (Top-1) | Trả về đầy đủ các chế tài khóa/xóa |
| 5 | Thời hạn khiếu nại Trả hàng/Hoàn tiền | `HeadingChunker` + Filter `buyer` | Có (Top-1) | **A/B Test:** Có filter ra 15 ngày (đúng người mua), không filter dễ ra 2 ngày (người bán). |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Metadata filter đóng vai trò quyết định ở Câu hỏi số 5.** Khi người dùng đặt câu hỏi chung *"Thời hạn khiếu nại là bao lâu?"*, nếu không có `metadata_filter={"audience": "buyer"}`, công cụ tìm kiếm sẽ lấy nhầm quy định 2 ngày của Người bán. Nhờ có bộ lọc tiền xử lý `audience`, hệ thống chỉ quét tài liệu của Người mua và trả về chính xác mốc 15 ngày.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Tầm quan trọng của việc làm sạch dữ liệu (Data Cleaning) trước khi chunking để loại bỏ nhiễu menu/footer.
2. So sánh hiệu quả thực tế giữa `FixedSizeChunker` vs `HeadingChunker` trên văn bản pháp lý/chính sách.
3. Demo trực quan trường hợp A/B Testing có và không có `metadata_filter` trên câu hỏi đa nghĩa.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu, nhưng chiến lược chunking quyết định đến 80% chất lượng của Retrieval. `FixedSizeChunker` ngẫu nhiên cắt đứt mạch câu khiến điểm cosine bị sai lệch nghiêm trọng, trong khi `HeadingChunker` giữ được toàn bộ ngữ cảnh giúp hệ thống RAG luôn đạt độ chính xác cao nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa thêm trường `section_type` (như `terms`, `faq`, `penalty_table`) trong metadata để có thể kết hợp lọc đa chiều (multi-field filtering) giúp tinh chỉnh không gian tìm kiếm hẹp và chính xác hơn nữa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
