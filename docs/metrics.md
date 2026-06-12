# Chỉ Số Đánh Giá

Đầu ra đánh giá thống nhất được lưu tại:

```text
results/metrics.csv                              (legacy, single-config)
results/<model>/<prompt_variant>/metrics.csv      (per-config)
```

Mỗi hàng tương ứng với một cặp bài toán–phương pháp trong một cấu hình cụ thể.

## Các cột

```text
id,difficulty,method,prompt_variant,parse_success,planner_success,plan_valid,goal_achieved,success,plan_length,runtime,error_type
```

## Định nghĩa các cột

| Cột | Mô tả |
|---|---|
| id | ID bài toán |
| difficulty | Độ khó của bài toán: easy, medium, hoặc hard |
| method | Phương pháp đánh giá: llm_only hoặc llm_planner |
| prompt_variant | Biến thể prompt đã sử dụng: basic hoặc detailed |
| parse_success | LLM output có được phân tích thành công hay không |
| planner_success | pyperplan có tạo được kế hoạch hay không |
| plan_valid | Kế hoạch được tạo ra có hợp lệ theo luật Blocks World hay không |
| goal_achieved | Trạng thái cuối có thỏa mãn mục tiêu hay không |
| success | Thành công đầu-cuối |
| plan_length | Số lượng hành động trong kế hoạch được tạo ra |
| runtime | Thời gian chạy tính bằng giây |
| error_type | Loại lỗi nếu lần chạy thất bại |

## Ghi chú về schema migration

File `evaluate.py` tự động detect metrics CSV với schema cũ (không có cột `prompt_variant`) và migrate bằng cách gán `prompt_variant = "basic"` cho các hàng hiện có.

## Điểm số chính

Điểm số chính là tỷ lệ thành công:

```text
success_rate = successful_runs / total_runs
```

Một lần chạy chỉ được xem là thành công nếu:

```text
parse_success = true
planner_success = true hoặc không áp dụng
plan_valid = true
goal_achieved = true
success = true
```

Đối với LLM-only, `planner_success` để trống vì không sử dụng symbolic planner.

## Các chỉ số tổng hợp được khuyến nghị

### Tỷ lệ thành công theo phương pháp

So sánh hiệu suất tổng thể của `llm_only` và `llm_planner`.

### Tỷ lệ thành công theo độ khó

Đo lường cách mỗi phương pháp hoạt động trên các bài toán easy, medium, và hard.

### Tỷ lệ thành công theo prompt variant

So sánh hiệu quả giữa basic và detailed prompt trên cùng model và method.

### Phân phối lỗi

Đếm các loại lỗi như:

```text
parse_error
json_parse_error
planner_no_solution_file
pddl_generation_error
precondition_violation
goal_not_achieved
unknown_action
unknown_object
unexpected_error
```

### Độ dài kế hoạch trung bình

Đo số lượng hành động trung bình đối với các kế hoạch thành công.

## Phân tích nâng cao (viz_analysis.py)

Module `src/viz_analysis.py` cung cấp các phân tích factorial cho notebook:

- **Central heatmap**: Success rate theo (model × prompt) × method
- **Main effects**: Method effect, model effect, prompt effect
- **Prompt delta**: Chênh lệch detailed − basic theo method và model
- **Sensitivity**: So sánh prompt sensitivity vs model sensitivity
- **Difficulty scaling**: Success rate theo difficulty, faceted theo model
- **Funnel analysis**: Tỷ lệ vượt qua từng pipeline stage
- **Error distribution**: Stacked bar chart phân bố lỗi theo model × prompt × method

## Các hình được tạo ra

### CLI cơ bản

```bash
python src/visualize.py --metrics results/metrics.csv
```

Đầu ra:

```text
results/figures/success_rate_by_method.png
results/figures/success_rate_by_difficulty.png
results/figures/error_distribution.png
results/figures/avg_plan_length.png
```

### Notebook phân tích

Sử dụng `notebook/analysis.ipynb` để tạo các hình phân tích đa mô hình. Module `viz_analysis.py` tải dữ liệu từ:

```text
results/qwen2.5-3b-instruct/{basic,detailed}/metrics.csv
results/qwen2.5-7b-instruct/{basic,detailed}/metrics.csv
results/llama3.1-8b/{basic,detailed}/metrics.csv
```

## Diễn giải

Nếu `llm_only` thất bại với `precondition_violation`, mô hình có khả năng đã tạo ra một chuỗi hành động không hợp lệ.

Nếu `llm_planner` thất bại với `json_parse_error`, mô hình đã không tạo ra JSON có cấu trúc hợp lệ.

Nếu `llm_planner` thất bại với `planner_no_solution_file`, bài toán JSON/PDDL có thể không nhất quán, không giải được, hoặc khác về mặt ngữ nghĩa so với tác vụ ban đầu.

Nếu `llm_planner` thất bại với `pddl_generation_error`, JSON hợp lệ nhưng quá trình chuyển sang PDDL bị lỗi (ví dụ thiếu trường, objects không khớp).
