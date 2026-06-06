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

## Tại sao chọn thiết kế này

Thiết kế tách biệt này cho phép chúng ta phân tích nơi xảy ra lỗi:

| Lỗi | Diễn giải |
|---|---|
| LLM-only thất bại nhưng LLM + planner thành công | LLM có thể hiểu tác vụ nhưng gặp khó khăn trong việc lập kế hoạch |
| LLM + planner thất bại ở bước phân tích JSON | Định dạng đầu ra của LLM không hợp lệ |
| LLM + planner thất bại ở bước planner | JSON/PDDL có thể biểu diễn một bài toán không giải được hoặc không chính xác |
| Kế hoạch thất bại khi xác thực | Kế hoạch được tạo ra không thỏa mãn tác vụ ban đầu |

## Streamlit Demo

Ứng dụng Streamlit cung cấp một giao diện tương tác với:

- Nhập tác vụ bằng ngôn ngữ tự nhiên
- Các tác vụ ví dụ
- Thực thi LLM-only
- Thực thi LLM + planner
- Đầu ra LLM thô
- JSON có cấu trúc
- PDDL được tạo ra
- Kế hoạch cuối cùng
- Kết quả xác thực
- Hiển thị trạng thái từng bước

Chạy:

```bash
streamlit run app/streamlit_app.py
```

## Demo Storyline

Luồng trình bày được đề xuất:

1. Tải một ví dụ dễ.
2. Chạy LLM-only.
3. Hiển thị kế hoạch được tạo ra và kết quả xác thực.
4. Chạy LLM + planner.
5. Hiển thị JSON, PDDL, kế hoạch của planner, và kết quả xác thực.
6. So sánh nơi mỗi phương pháp thành công hoặc thất bại.
7. Mở các hình kết quả từ `results/figures/`.

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

## Tại sao chọn thiết kế này

Thiết kế tách biệt này cho phép chúng ta phân tích nơi xảy ra lỗi:

| Lỗi | Diễn giải |
|---|---|
| LLM-only thất bại nhưng LLM + planner thành công | LLM có thể hiểu tác vụ nhưng gặp khó khăn trong việc lập kế hoạch |
| LLM + planner thất bại ở bước phân tích JSON | Định dạng đầu ra của LLM không hợp lệ |
| LLM + planner thất bại ở bước planner | JSON/PDDL có thể biểu diễn một bài toán không giải được hoặc không chính xác |
| Kế hoạch thất bại khi xác thực | Kế hoạch được tạo ra không thỏa mãn tác vụ ban đầu |

## Streamlit Demo

Ứng dụng Streamlit cung cấp một giao diện tương tác với:

- Nhập tác vụ bằng ngôn ngữ tự nhiên
- Các tác vụ ví dụ
- Thực thi LLM-only
- Thực thi LLM + planner
- Đầu ra LLM thô
- JSON có cấu trúc
- PDDL được tạo ra
- Kế hoạch cuối cùng
- Kết quả xác thực
- Hiển thị trạng thái từng bước

Chạy:

```bash
streamlit run app/streamlit_app.py
```

## Demo Storyline

Luồng trình bày được đề xuất:

1. Tải một ví dụ dễ.
2. Chạy LLM-only.
3. Hiển thị kế hoạch được tạo ra và kết quả xác thực.
4. Chạy LLM + planner.
5. Hiển thị JSON, PDDL, kế hoạch của planner, và kết quả xác thực.
6. So sánh nơi mỗi phương pháp thành công hoặc thất bại.
7. Mở các hình kết quả từ `results/figures/`.
