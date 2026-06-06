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

## 3. Xác thực Core Plan Validator

```bash
pytest tests/test_validator.py
```

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

## 7. Chạy Unified Evaluation

Kiểm thử nhanh:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
```

Đánh giá đầy đủ:

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --reset
python src/evaluate.py --method all --data data/blocks_world_medium.jsonl
python src/evaluate.py --method all --data data/blocks_world_hard.jsonl
```

Đầu ra:

```text
results/metrics.csv
```

## 8. Tạo Figures

```bash
python src/visualize.py --metrics results/metrics.csv
```

Đầu ra:

```text
results/figures/
```

## 9. Chạy Demo App

```bash
streamlit run app/streamlit_app.py
```

## 10. Checklist tái lập được khuyến nghị

Trước khi nộp kết quả, chạy:

```bash
python -m py_compile src/*.py app/streamlit_app.py
pytest tests/test_validator.py
python src/check_dataset.py --data data/blocks_world_easy.jsonl
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
python src/visualize.py --metrics results/metrics.csv
```

## 11. Các artifact mong đợi

```text
results/metrics.csv
results/figures/success_rate_by_method.png
results/figures/success_rate_by_difficulty.png
results/figures/error_distribution.png
results/figures/avg_plan_length.png
```
