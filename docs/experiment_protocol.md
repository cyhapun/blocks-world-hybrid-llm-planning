# Quy Trình Thí Nghiệm

Tài liệu này mô tả cách tái tạo các thí nghiệm.

## 1. Thiết lập

Tạo môi trường:

```bash
conda create -n blocks-world-llm python=3.11 -y
conda activate blocks-world-llm
pip install -r requirements.txt
```

Tạo `.env`:

```bash
cp .env.example .env
```

Thiết lập cấu hình Hugging Face hoặc local API.

## 2. Xác thực Dataset

```bash
python src/check_dataset.py --data data/blocks_world_easy.jsonl
python src/check_dataset.py --data data/blocks_world_medium.jsonl
python src/check_dataset.py --data data/blocks_world_hard.jsonl
```

## 3. Chạy Tests

```bash
pytest tests/
```

Các test bao gồm:

- `test_validator.py` – xác thực logic validate kế hoạch
- `test_evaluate_metrics.py` – xác thực ghi/đọc metrics CSV và migration schema
- `test_viz_analysis.py` – xác thực load dữ liệu và plot helpers

## 4. Kiểm thử Pyperplan Pipeline

Tạo một bài toán PDDL:

```bash
python src/json_to_pddl.py --input data/blocks_world_easy.jsonl --index 0
```

Chạy planner:

```bash
python src/run_planner.py --problem pddl/problems/bw_easy_001.pddl
```

Xác thực kế hoạch:

```bash
python src/validate_plan.py --problem-id bw_easy_001 --plan results/example_plan.txt
```

## 5. Chạy LLM-only Baseline

```bash
python src/llm_only_baseline.py --data data/blocks_world_easy.jsonl --limit 3
```

Đầu ra:

```text
results/llm_only_results.csv
```

## 6. Chạy LLM + Planner Pipeline

```bash
python src/llm_to_json.py --data data/blocks_world_easy.jsonl --limit 3
```

Đầu ra:

```text
results/llm_planner_results.csv
```

## 7. Chạy Unified Evaluation (single config)

Kiểm thử nhanh:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
```

Đánh giá đầy đủ (basic prompt, default model):

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --reset
python src/evaluate.py --method all --data data/blocks_world_medium.jsonl
python src/evaluate.py --method all --data data/blocks_world_hard.jsonl
```

Đầu ra:

```text
results/metrics.csv
```

## 8. Chạy Multi-Model / Multi-Prompt Evaluation

Để so sánh nhiều mô hình và prompt variant, sử dụng `--results-dir` và `--prompt-variant` để phân tách kết quả theo cấu hình.

### Ví dụ: Qwen 2.5 7B, basic prompt

```bash
python src/evaluate.py --method all \
  --data data/blocks_world_easy.jsonl \
  --prompt-variant basic \
  --llm-only-prompt src/prompts/basic/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/basic/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/basic \
  --reset

python src/evaluate.py --method all \
  --data data/blocks_world_medium.jsonl \
  --prompt-variant basic \
  --llm-only-prompt src/prompts/basic/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/basic/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/basic

python src/evaluate.py --method all \
  --data data/blocks_world_hard.jsonl \
  --prompt-variant basic \
  --llm-only-prompt src/prompts/basic/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/basic/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/basic
```

### Ví dụ: Qwen 2.5 7B, detailed prompt

```bash
python src/evaluate.py --method all \
  --data data/blocks_world_easy.jsonl \
  --prompt-variant detailed \
  --llm-only-prompt src/prompts/detailed/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/detailed/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/detailed \
  --reset

python src/evaluate.py --method all \
  --data data/blocks_world_medium.jsonl \
  --prompt-variant detailed \
  --llm-only-prompt src/prompts/detailed/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/detailed/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/detailed

python src/evaluate.py --method all \
  --data data/blocks_world_hard.jsonl \
  --prompt-variant detailed \
  --llm-only-prompt src/prompts/detailed/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/detailed/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/detailed
```

Lặp lại tương tự cho các model khác (thay `--mode`, `--model`, và thư mục results):

- `results/qwen2.5-3b-instruct/{basic,detailed}/`
- `results/llama3.1-8b/{basic,detailed}/`

### Cấu trúc đầu ra

```text
results/<model>/<prompt_variant>/
  ├── metrics.csv
  ├── raw_outputs/
  │   ├── llm_only/
  │   └── llm_to_json/
  ├── plans/
  │   └── llm_to_json/
  └── figures/
```

## 9. Tạo Figures

### CLI cơ bản

```bash
python src/visualize.py --metrics results/metrics.csv
```

Đầu ra:

```text
results/figures/
```

### Notebook phân tích

Mở `notebook/analysis.ipynb` để tạo các hình phân tích đa mô hình. Module `src/viz_analysis.py` tự động tải metrics từ tất cả các cấu hình.

## 10. Chạy Demo App

```bash
streamlit run app/streamlit_app.py
```

## 11. Checklist tái lập được khuyến nghị

Trước khi nộp kết quả, chạy:

```bash
python -m py_compile src/*.py app/streamlit_app.py
pytest tests/
python src/check_dataset.py --data data/blocks_world_easy.jsonl
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
python src/visualize.py --metrics results/metrics.csv
```

## 12. Các artifact mong đợi

### Single-config (legacy)

```text
results/metrics.csv
results/figures/success_rate_by_method.png
results/figures/success_rate_by_difficulty.png
results/figures/error_distribution.png
results/figures/avg_plan_length.png
```

### Multi-config (per model × prompt variant)

```text
results/qwen2.5-3b-instruct/{basic,detailed}/metrics.csv
results/qwen2.5-7b-instruct/{basic,detailed}/metrics.csv
results/llama3.1-8b/{basic,detailed}/metrics.csv
```

### Notebook

```text
notebook/analysis.ipynb
```
