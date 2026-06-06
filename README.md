# Demo Blocks World LLM + Symbolic Planner

Dự án này đánh giá khả năng lập kế hoạch trên các bài toán Blocks World bằng hai cách tiếp cận:

1. **LLM-only**: mô hình ngôn ngữ trực tiếp tạo kế hoạch hành động từ một nhiệm vụ bằng ngôn ngữ tự nhiên.
2. **LLM + symbolic planner**: mô hình ngôn ngữ phân tích nhiệm vụ ngôn ngữ tự nhiên thành JSON có cấu trúc, backend chuyển JSON thành PDDL, và `pyperplan` tạo kế hoạch cuối cùng.

Demo chính tập trung vào cách tiếp cận thứ hai:

```text
Natural language task
→ LLM parser
→ JSON / PDDL
→ pyperplan
→ plan
→ validator
→ metrics + visualization
```

## 1. Kiến trúc hệ thống

```text
data/*.jsonl
  ↓
natural_language
  ↓
LLM
  ├── LLM-only: direct action plan
  └── LLM + planner: structured JSON
          ↓
      JSON to PDDL
          ↓
      pyperplan
          ↓
        plan
          ↓
    validate_plan.py
          ↓
  results/metrics.csv
          ↓
  visualization + Streamlit demo
```

Các thành phần chính:

| Component | Purpose |
|---|---|
| `data/*.jsonl` | Các bài toán benchmark Blocks World |
| `pddl/domain_blocks_world.pddl` | Domain PDDL cho Blocks World |
| `src/validate_plan.py` | Bộ kiểm tra kế hoạch nội bộ |
| `src/json_to_pddl.py` | Chuyển đổi bài toán JSON sang PDDL |
| `src/run_planner.py` | Chạy `pyperplan` |
| `src/llm_only_baseline.py` | Chạy lập kế hoạch LLM-only |
| `src/llm_to_json.py` | Chạy lập kế hoạch LLM-to-JSON-to-PDDL |
| `src/evaluate.py` | Trình chạy đánh giá thống nhất |
| `src/visualize.py` | Tạo hình kết quả |
| `src/render_plan.py` | Render các trace kế hoạch định tính |
| `app/streamlit_app.py` | Ứng dụng demo tương tác |

## 2. Cấu trúc repository

```text
.
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── data/
│   ├── blocks_world_easy.jsonl
│   ├── blocks_world_medium.jsonl
│   └── blocks_world_hard.jsonl
├── docs/
│   ├── demo_design.md
│   ├── metrics.md
│   ├── experiment_protocol.md
│   └── troubleshooting.md
├── pddl/
│   ├── domain_blocks_world.pddl
│   ├── problems/
│   └── generated_problems/
├── src/
│   ├── generate_dataset.py
│   ├── check_dataset.py
│   ├── llm_client.py
│   ├── llm_only_baseline.py
│   ├── llm_to_json.py
│   ├── json_to_pddl.py
│   ├── run_planner.py
│   ├── validate_plan.py
│   ├── evaluate.py
│   ├── visualize.py
│   └── render_plan.py
├── results/
│   ├── raw_outputs/
│   ├── plans/
│   ├── metrics.csv
│   └── figures/
├── tests/
│   └── test_validator.py
└── app/
    └── streamlit_app.py
```

## 3. Thiết lập môi trường

Tạo và kích hoạt môi trường dự án.

Sử dụng conda:

```bash
conda create -n blocks-world-llm python=3.11 -y
conda activate blocks-world-llm
pip install -r requirements.txt
```

Hoặc sử dụng venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Kiểm tra cài đặt:

```bash
python -m py_compile src/validate_plan.py src/evaluate.py app/streamlit_app.py
pytest tests/test_validator.py
```

## 4. Cấu hình API

Dự án hỗ trợ hai backend LLM:

| Backend | Mô tả |
|---|---|
| `hf` | Hugging Face Inference API |
| `local` | API local tương thích OpenAI |

Tạo file môi trường cục bộ:

```bash
cp .env.example .env
```

Ví dụ `.env`:

```env
LLM_MODE=hf

HF_TOKEN=your_huggingface_token_here
HF_MODEL=Qwen/Qwen2.5-7B-Instruct

LOCAL_LLM_BASE_URL=http://localhost:8000/v1
LOCAL_LLM_API_KEY=local-token
LOCAL_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=512
```

Không commit `.env`.

## 5. Dataset

Các file dataset:

```text
data/blocks_world_easy.jsonl
data/blocks_world_medium.jsonl
data/blocks_world_hard.jsonl
```

Mỗi dòng là một bài toán JSON:

```json
{
  "id": "bw_easy_001",
  "difficulty": "easy",
  "objects": ["A", "B", "C"],
  "initial_state": [
    ["on_table", "A"],
    ["on_table", "B"],
    ["on", "C", "A"],
    ["clear", "C"],
    ["clear", "B"],
    ["handempty"]
  ],
  "goal": [
    ["on", "B", "C"]
  ],
  "natural_language": "Initially, A and B are on the table, C is on A. C and B are clear. The hand is empty. The goal is to put B on C."
}
```

Xác thực dataset:

```bash
python src/check_dataset.py --data data/blocks_world_easy.jsonl
python src/check_dataset.py --data data/blocks_world_medium.jsonl
python src/check_dataset.py --data data/blocks_world_hard.jsonl
```

## 6. Chạy từng phương pháp riêng lẻ

### LLM-only

```bash
python src/llm_only_baseline.py --data data/blocks_world_easy.jsonl --limit 3
```

Output:

```text
results/raw_outputs/llm_only/
results/llm_only_results.csv
```

### LLM + symbolic planner

```bash
python src/llm_to_json.py --data data/blocks_world_easy.jsonl --limit 3
```

Output:

```text
results/raw_outputs/llm_to_json/
pddl/problems/llm_to_json/
results/plans/llm_to_json/
results/llm_planner_results.csv
```

## 7. Chạy đánh giá thống nhất

Chạy một phương pháp:

```bash
python src/evaluate.py --method llm_only --data data/blocks_world_easy.jsonl --limit 3 --reset
python src/evaluate.py --method llm_planner --data data/blocks_world_easy.jsonl --limit 3 --reset
```

Chạy cả hai phương pháp:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
```

Chạy toàn bộ thí nghiệm:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --reset
python src/evaluate.py --method all --data data/blocks_world_medium.jsonl
python src/evaluate.py --method all --data data/blocks_world_hard.jsonl
```

Output thống nhất:

```text
results/metrics.csv
```

## 8. Metrics

`results/metrics.csv` sử dụng các cột sau:

```csv
id,difficulty,method,parse_success,planner_success,plan_valid,goal_achieved,success,plan_length,runtime,error_type
```

Các metric chính:

| Metric | Meaning |
|---|---|
| `parse_success` | LLM output có được parse thành công hay không |
| `planner_success` | `pyperplan` có tạo được kế hoạch hay không |
| `plan_valid` | Kế hoạch có thỏa mãn precondition/effect của action hay không |
| `goal_achieved` | Trạng thái cuối cùng có thỏa mãn goal hay không |
| `success` | Thành công end-to-end |
| `plan_length` | Số lượng action |
| `runtime` | Thời gian chạy tính bằng giây |
| `error_type` | Loại lỗi |

Xem `docs/metrics.md` để biết chi tiết.

## 9. Tạo figures

```bash
python src/visualize.py --metrics results/metrics.csv
```

Các figure được tạo:

```text
results/figures/success_rate_by_method.png
results/figures/success_rate_by_difficulty.png
results/figures/error_distribution.png
results/figures/avg_plan_length.png
```

Render một qualitative plan trace:

```bash
python src/render_plan.py --problem-id bw_easy_001
```

## 10. Chạy Streamlit Demo

```bash
streamlit run app/streamlit_app.py
```

Ứng dụng hỗ trợ:

- Nhập nhiệm vụ bằng ngôn ngữ tự nhiên
- Các nhiệm vụ ví dụ
- Lập kế hoạch LLM-only
- Pipeline LLM + planner
- Hiển thị raw LLM output
- Hiển thị JSON có cấu trúc và PDDL được tạo
- Hiển thị plan
- Hiển thị kết quả validator
- Render trạng thái Blocks World từng bước

Ứng dụng đọc credentials từ `.env`.

## 11. Các lỗi thường gặp

### `HF_TOKEN` bị thiếu

Tạo `.env` và thiết lập:

```env
HF_TOKEN=your_huggingface_token_here
```

### `planner_no_solution_file`

Bài toán PDDL được tạo có thể không giải được. Điều này thường có nghĩa là LLM đã tạo biểu diễn JSON không chính xác so với nhiệm vụ ban đầu.

Kiểm tra:

```bash
cat results/raw_outputs/llm_to_json/<file>.txt
cat pddl/problems/llm_to_json/<problem_id>.pddl
```

### `precondition_violation`

Kế hoạch được tạo chứa một action không thể chạy hợp lệ trong trạng thái hiện tại.

Sử dụng:

```bash
python src/render_plan.py --problem-id <problem_id> --plan <plan_file>
```

### `ModuleNotFoundError`

Đảm bảo môi trường đúng đã được kích hoạt và các dependency đã được cài đặt:

```bash
pip install -r requirements.txt
```

Thông tin chi tiết hơn có trong `docs/troubleshooting.md`.

## 12. Tài liệu

Tài liệu bổ sung:

```text
docs/demo_design.md
docs/metrics.md
docs/experiment_protocol.md
docs/troubleshooting.md
```
