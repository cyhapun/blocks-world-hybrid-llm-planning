    # Khắc Phục Sự Cố

## 1. Sai môi trường Python

### Triệu chứng

Các lệnh thất bại do thiếu package hoặc lỗi pyperplan.

### Cách sửa

Kích hoạt đúng môi trường:

```bash
conda activate blocks-world-llm
pip install -r requirements.txt
```

Kiểm tra:

```bash
which python
python --version
python -m py_compile src/evaluate.py
```

## 2. Thiếu Hugging Face Token

### Triệu chứng

```text
HF_TOKEN is missing
```

### Cách sửa

Tạo `.env`:

```bash
cp .env.example .env
```

Thiết lập:

```env
LLM_MODE=hf
HF_TOKEN=your_huggingface_token_here
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
```

## 3. Lỗi kết nối Local API

### Triệu chứng

```text
Connection refused
```

hoặc

```text
Failed to establish a new connection
```

### Cách sửa

Đảm bảo local model server đang chạy và URL là chính xác:

```env
LLM_MODE=local
LOCAL_LLM_BASE_URL=http://localhost:8000/v1
LOCAL_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

Sau đó chạy lại:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
```

## 4. Lỗi phân tích JSON

### Triệu chứng

```text
json_parse_error
```

### Ý nghĩa

LLM không trả về JSON hợp lệ cho pipeline LLM + planner.

### Cách sửa

Kiểm tra raw output:

```bash
ls results/raw_outputs/llm_to_json
cat results/raw_outputs/llm_to_json/<file>.txt
```

Output nên có dạng:

```json
{
  "objects": ["A", "B", "C"],
  "init": [
    ["on_table", "A"],
    ["on_table", "B"],
    ["clear", "A"],
    ["clear", "B"],
    ["handempty"]
  ],
  "goal": [
    ["on", "A", "B"]
  ]
}
```

## 5. Planner không tìm thấy lời giải

### Triệu chứng

```text
planner_no_solution_file
```

hoặc

```text
Task unsolvable
```

### Ý nghĩa

pyperplan không tìm thấy lời giải cho bài toán PDDL được tạo ra.

Điều này thường có nghĩa là JSON do LLM tạo ra đã tạo thành một bài toán không chính xác hoặc không giải được.

### Debug

Kiểm tra JSON được tạo ra:

```bash
cat results/raw_outputs/llm_to_json/<file>.txt
```

Kiểm tra PDDL được tạo ra:

```bash
cat pddl/problems/llm_to_json/<problem_id>.pddl
```

Chạy pyperplan trực tiếp:

```bash
python -m pyperplan -H hff -s gbf pddl/domain_blocks_world.pddl pddl/problems/llm_to_json/<problem_id>.pddl
```

## 6. Vi phạm tiền điều kiện

### Triệu chứng

```text
precondition_violation
```

### Ý nghĩa

Một hành động trong kế hoạch đã được thử thực hiện trước khi các tiền điều kiện của nó được thỏa mãn.

Ví dụ:

```text
stack(B,C)
```

là không hợp lệ nếu robot hiện không đang cầm B.

### Debug

Render kế hoạch:

```bash
python src/render_plan.py --problem-id <problem_id> --plan <plan_file>
```

## 7. Mục tiêu không đạt được

### Triệu chứng

```text
goal_not_achieved
```

### Ý nghĩa

Kế hoạch được thực thi thành công, nhưng trạng thái cuối không thỏa mãn mục tiêu.

### Debug

Kiểm tra trạng thái cuối trong output của validator:

```bash
python src/validate_plan.py --problem-id <problem_id> --plan <plan_file>
```

## 8. Metrics rỗng hoặc bị trùng lặp

### Triệu chứng

```text
results/metrics.csv has duplicated rows.
```

### Cách sửa

Dùng `--reset` ở lệnh đánh giá đầu tiên:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --reset
```

Sau đó append medium và hard:

```bash
python src/evaluate.py --method all --data data/blocks_world_medium.jsonl
python src/evaluate.py --method all --data data/blocks_world_hard.jsonl
```

## 9. Streamlit App không khởi động

### Triệu chứng

```text
streamlit: command not found
```

### Cách sửa

Cài đặt requirements:

```bash
pip install -r requirements.txt
```

Chạy:

```bash
streamlit run app/streamlit_app.py
```

## 10. Raw logs quá dài

Các lỗi planner có thể bao gồm các log kỹ thuật. Trong ứng dụng Streamlit, các log này được hiển thị trong các phần có thể mở rộng để giao diện chính vẫn dễ đọc.
