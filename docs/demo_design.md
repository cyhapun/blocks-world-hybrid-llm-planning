# Thiết Kế Demo

## Mục tiêu

Demo cho thấy cách một mô hình ngôn ngữ có thể được kết hợp với một bộ lập kế hoạch biểu tượng cho bài toán lập kế hoạch Blocks World.

Cách tiếp cận chính được trình bày là:

```text
Tác vụ ngôn ngữ tự nhiên
→ Bộ phân tích LLM
→ JSON có cấu trúc
→ Bài toán PDDL
→ pyperplan
→ kế hoạch
→ trình xác thực
→ chỉ số và trực quan hóa
```

Cách này được gọi là phương pháp **LLM + planner**.

## Các phương pháp được so sánh

### 1. LLM-only

Mô hình nhận một tác vụ bằng ngôn ngữ tự nhiên và trực tiếp xuất ra một kế hoạch.

```text
natural_language
→ LLM
→ danh sách hành động
→ trình xác thực
```

LLM phải vừa hiểu tác vụ vừa thực hiện lập kế hoạch.

### 2. LLM + planner

Mô hình nhận một tác vụ bằng ngôn ngữ tự nhiên và xuất ra JSON có cấu trúc.

```text
natural_language
→ LLM
→ JSON
→ PDDL
→ pyperplan
→ danh sách hành động
→ trình xác thực
```

Trong cách tiếp cận này, LLM thực hiện phân tích ngữ nghĩa, trong khi pyperplan thực hiện lập kế hoạch biểu tượng.

## Các mô hình được đánh giá

Dự án so sánh 3 mô hình trên 2 biến thể prompt:

| Mô hình | Kích thước | ID |
|---|---|---|
| Qwen 2.5 Instruct | 3B | `qwen2.5-3b` |
| Qwen 2.5 Instruct | 7B | `qwen2.5-7b` |
| Llama 3.1 Instruct | 8B | `llama3.1-8b` |

Hai biến thể prompt:

| Variant | Mô tả |
|---|---|
| `basic` | Prompt ngắn gọn, chỉ chứa hướng dẫn cơ bản |
| `detailed` | Prompt chi tiết với ví dụ và ràng buộc cụ thể |

## Tại sao chọn thiết kế này

Thiết kế tách biệt này cho phép chúng ta phân tích nơi xảy ra lỗi:

| Lỗi | Diễn giải |
|---|---|
| LLM-only thất bại nhưng LLM + planner thành công | LLM có thể hiểu tác vụ nhưng gặp khó khăn trong việc lập kế hoạch |
| LLM + planner thất bại ở bước phân tích JSON | Định dạng đầu ra của LLM không hợp lệ |
| LLM + planner thất bại ở bước planner | JSON/PDDL có thể biểu diễn một bài toán không giải được hoặc không chính xác |
| Kế hoạch thất bại khi xác thực | Kế hoạch được tạo ra không thỏa mãn tác vụ ban đầu |

Với thiết kế factorial (model × prompt × method), ta có thể phân tích:

- **Main effect của method**: LLM + planner có tốt hơn LLM-only không?
- **Main effect của prompt**: Detailed prompt có giúp ích không?
- **Main effect của model**: Model lớn hơn có tốt hơn không?
- **Interaction effects**: Prompt nào phù hợp với model nào?

## Streamlit Demo

Ứng dụng Streamlit được thiết kế với giao diện hiện đại (Dark theme), cung cấp một môi trường tương tác trực quan:

- Bố cục Side-by-side cho phép đối chiếu trực tiếp giữa 2 phương pháp
- Thanh tiến trình ngang (Pipeline Progress Visualization) giúp nhận diện lỗi nằm ở khâu nào
- Trình hiển thị trạng thái bằng hình khối (Visual Block Rendering) thay cho chữ ASCII khô khan
- Mục "Prompt Templates" cho phép người thuyết trình sửa prompt ngay tại chỗ để thử nghiệm
- Tùy chọn chạy song song cả 2 phương pháp cùng lúc (Run Both Methods)
- Hiển thị đầu ra LLM thô, JSON có cấu trúc, và PDDL được sinh ra
- Hiển thị báo cáo so sánh (Comparison summary) gồm runtime và độ hợp lệ

Chạy:

```bash
streamlit run app/streamlit_app.py
```

## Demo Storyline

Luồng trình bày được đề xuất dựa trên giao diện Side-by-side mới:

1. **Phân tích Bài toán dễ**:
   - Tải "Example 1: Easy".
   - Chạy **Run Both Methods**.
   - Khoe tính năng Visual Block Rendering và thanh trạng thái tiến trình xanh báo hiệu cả 2 đều Valid.
2. **Khai thác Điểm yếu của LLM**:
   - Tải "Example 3: Hard".
   - Chạy **Run Both Methods**.
   - Phân tích bên LLM-only: Kế hoạch sẽ hiển thị thẻ lỗi đỏ (Failed). Kéo xuống phần Visualizer để xem bước nào bị lỗi "precondition violation" (ví dụ: bốc khối đang bị đè).
   - Phân tích bên LLM + Planner: Hiển thị thẻ xanh (Valid). Mở phần JSON và PDDL để xem hệ thống trích xuất cấu trúc chuẩn xác như thế nào để pyperplan tính toán.
3. **Thử nghiệm Động**:
   - Mở phần **Prompt Templates** ở cột bên trái.
   - Thay đổi prompt của LLM-to-JSON để yêu cầu mô hình phản hồi sai định dạng (vd: bắt giải thích).
   - Chạy lại để xem Pipeline Progress báo lỗi đỏ ngay tại bước "Parse JSON" thay vì "Validate", chứng minh khả năng debug trực quan.
4. **Đánh giá Thống kê**:
   - Mở notebook `notebook/analysis.ipynb` để trình bày phân tích đa mô hình (funnel analysis, success rate heatmap).
   - Thảo luận về ảnh hưởng của prompt variant đến kết quả chung.
