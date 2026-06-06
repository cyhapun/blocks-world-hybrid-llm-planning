# Chỉ Số Đánh Giá

Đầu ra đánh giá thống nhất được lưu tại:

```text
results/metrics.csv
```

Mỗi hàng tương ứng với một cặp bài toán-phương pháp.

## Các cột

```text
id,difficulty,method,parse_success,planner_success,plan_valid,goal_achieved,success,plan_length,runtime,error_type
```

## Định nghĩa các cột

| Cột | Mô tả |
|---|---|
| id | ID bài toán |
| difficulty | Độ khó của bài toán: easy, medium, hoặc hard |
| method | Phương pháp đánh giá: llm_only hoặc llm_planner |
| parse_success | LLM output có được phân tích thành công hay không |
| planner_success | pyperplan có tạo được kế hoạch hay không |
| plan_valid | Kế hoạch được tạo ra có hợp lệ theo luật Blocks World hay không |
| goal_achieved | Trạng thái cuối có thỏa mãn mục tiêu hay không |
| success | Thành công đầu-cuối |
| plan_length | Số lượng hành động trong kế hoạch được tạo ra |
| runtime | Thời gian chạy tính bằng giây |
| error_type | Loại lỗi nếu lần chạy thất bại |

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

### Phân phối lỗi

Đếm các loại lỗi như:

```text
parse_error
json_parse_error
planner_no_solution_file
precondition_violation
goal_not_achieved
unknown_action
unknown_object
```

### Độ dài kế hoạch trung bình

Đo số lượng hành động trung bình đối với các kế hoạch thành công.

## Các hình được tạo ra

Chạy:

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

## Diễn giải

Nếu `llm_only` thất bại với `precondition_violation`, mô hình có khả năng đã tạo ra một chuỗi hành động không hợp lệ.

Nếu `llm_planner` thất bại với `json_parse_error`, mô hình đã không tạo ra JSON có cấu trúc hợp lệ.

Nếu `llm_planner` thất bại với `planner_no_solution_file`, bài toán JSON/PDDL có thể không nhất quán, không giải được, hoặc khác về mặt ngữ nghĩa so với tác vụ ban đầu.
