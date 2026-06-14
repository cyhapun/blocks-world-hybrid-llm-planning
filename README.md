# Blocks World – Hybrid LLM Planning

Dự án này đánh giá khả năng lập kế hoạch trên các bài toán Blocks World bằng hai cách tiếp cận:

1. **LLM-only**: mô hình ngôn ngữ trực tiếp tạo kế hoạch hành động từ một nhiệm vụ bằng ngôn ngữ tự nhiên.
2. **LLM + symbolic planner**: mô hình ngôn ngữ phân tích nhiệm vụ ngôn ngữ tự nhiên thành JSON có cấu trúc, backend chuyển JSON thành PDDL, và `pyperplan` tạo kế hoạch cuối cùng.

Hệ thống hỗ trợ so sánh đa mô hình (Qwen 2.5 3B, Qwen 2.5 7B, Llama 3.1 8B) với hai biến thể prompt (basic, detailed).

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
  results/<model>/<prompt_variant>/metrics.csv
          ↓
  viz_analysis.py (notebook) + visualize.py (CLI)
          ↓
  visualization + Streamlit demo
```

Các thành phần chính:

| Component | Purpose |
|---|---|
| `data/*.jsonl` | Các bài toán benchmark Blocks World |
| `pddl/domain_blocks_world.pddl` | Domain PDDL cho Blocks World |
| `src/llm_client.py` | Client LLM thống nhất (Hugging Face / local API) |
| `src/llm_only_baseline.py` | Chạy lập kế hoạch LLM-only |
| `src/llm_to_json.py` | Chạy lập kế hoạch LLM-to-JSON-to-PDDL |
| `src/json_to_pddl.py` | Chuyển đổi bài toán JSON sang PDDL |
| `src/run_planner.py` | Chạy `pyperplan` |
| `src/validate_plan.py` | Bộ kiểm tra kế hoạch nội bộ |
| `src/evaluate.py` | Trình chạy đánh giá thống nhất (hỗ trợ multi-prompt) |
| `src/visualize.py` | Tạo figures cơ bản từ CLI |
| `src/viz_analysis.py` | Phân tích trực quan đa mô hình/đa prompt (dùng trong notebook) |
| `src/render_plan.py` | Render các trace kế hoạch định tính |
| `src/prompts/` | Thư mục chứa prompt templates (basic/ và detailed/) |
| `notebook/analysis.ipynb` | Notebook phân tích kết quả thí nghiệm |
| `app/streamlit_app.py` | Ứng dụng demo tương tác |

## 2. Cấu trúc repository

```text
.
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .streamlit/
│   └── config.toml
├── data/
│   ├── blocks_world_easy.jsonl
│   ├── blocks_world_medium.jsonl
│   └── blocks_world_hard.jsonl
├── docs/
│   ├── demo_design.md
│   ├── metrics.md
│   ├── experiment_protocol.md
│   └── troubleshooting.md
├── notebook/
│   └── analysis.ipynb
├── pddl/
│   ├── domain_blocks_world.pddl
│   └── problems/
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
│   ├── viz_analysis.py
│   ├── render_plan.py
│   └── prompts/
│       ├── basic/
│       │   ├── llm_only_prompt.txt
│       │   └── llm_to_json_prompt.txt
│       └── detailed/
│           ├── llm_only_prompt.txt
│           └── llm_to_json_prompt.txt
├── results/
│   ├── metrics.csv
│   ├── figures/
│   ├── raw_outputs/
│   ├── plans/
│   ├── qwen2.5-3b-instruct/
│   │   ├── basic/
│   │   └── detailed/
│   ├── qwen2.5-7b-instruct/
│   │   ├── basic/
│   │   └── detailed/
│   └── llama3.1-8b/
│       ├── basic/
│       └── detailed/
├── tests/
│   ├── test_validator.py
│   ├── test_evaluate_metrics.py
│   └── test_viz_analysis.py
└── app/
    ├── block_visualizer.py
    ├── pipeline_viz.py
    ├── streamlit_app.py
    └── styles.css
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
pytest tests/
```

## 4. Cấu hình API

Dự án hỗ trợ hai backend LLM:

| Backend | Mô tả |
|---|---|
| `hf` | Hugging Face Inference API |
| `local` | API local tương thích OpenAI (vLLM, Ollama, ...) |

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
data/blocks_world_easy.jsonl      (10 bài)
data/blocks_world_medium.jsonl    (15 bài)
data/blocks_world_hard.jsonl      (15 bài)
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

## 6. Prompt Variants

Dự án hỗ trợ hai biến thể prompt:

| Variant | Đường dẫn | Mô tả |
|---|---|---|
| `basic` | `src/prompts/basic/` | Prompt ngắn gọn, chỉ chứa hướng dẫn cơ bản |
| `detailed` | `src/prompts/detailed/` | Prompt chi tiết với ví dụ và ràng buộc cụ thể |

Mỗi variant chứa hai file prompt:

- `llm_only_prompt.txt` – dùng cho phương pháp LLM-only
- `llm_to_json_prompt.txt` – dùng cho phương pháp LLM + planner

## 7. Chạy từng phương pháp riêng lẻ

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

## 8. Chạy đánh giá thống nhất

### Chạy một cấu hình đơn

```bash
python src/evaluate.py --method llm_only --data data/blocks_world_easy.jsonl --limit 3 --reset
python src/evaluate.py --method llm_planner --data data/blocks_world_easy.jsonl --limit 3 --reset
```

### Chạy cả hai phương pháp

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset
```

### Chạy với prompt variant khác nhau

Sử dụng `--prompt-variant`, `--llm-only-prompt`, `--llm-planner-prompt`, và `--results-dir` để phân tách kết quả:

```bash
# Basic prompt
python src/evaluate.py --method all \
  --data data/blocks_world_easy.jsonl \
  --prompt-variant basic \
  --llm-only-prompt src/prompts/basic/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/basic/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/basic \
  --reset

# Detailed prompt
python src/evaluate.py --method all \
  --data data/blocks_world_easy.jsonl \
  --prompt-variant detailed \
  --llm-only-prompt src/prompts/detailed/llm_only_prompt.txt \
  --llm-planner-prompt src/prompts/detailed/llm_to_json_prompt.txt \
  --results-dir results/qwen2.5-7b-instruct/detailed \
  --reset
```

### Chạy toàn bộ thí nghiệm (một model, một prompt variant)

```bash
python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --results-dir results/<model>/<variant> --prompt-variant <variant> --llm-only-prompt src/prompts/<variant>/llm_only_prompt.txt --llm-planner-prompt src/prompts/<variant>/llm_to_json_prompt.txt --reset
python src/evaluate.py --method all --data data/blocks_world_medium.jsonl --results-dir results/<model>/<variant> --prompt-variant <variant> --llm-only-prompt src/prompts/<variant>/llm_only_prompt.txt --llm-planner-prompt src/prompts/<variant>/llm_to_json_prompt.txt
python src/evaluate.py --method all --data data/blocks_world_hard.jsonl --results-dir results/<model>/<variant> --prompt-variant <variant> --llm-only-prompt src/prompts/<variant>/llm_only_prompt.txt --llm-planner-prompt src/prompts/<variant>/llm_to_json_prompt.txt
```

Output thống nhất:

```text
results/<model>/<variant>/metrics.csv
```

## 9. Metrics

`metrics.csv` sử dụng các cột sau:

```csv
id,difficulty,method,prompt_variant,parse_success,planner_success,plan_valid,goal_achieved,success,plan_length,runtime,error_type
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
| `prompt_variant` | Biến thể prompt đã sử dụng (basic / detailed) |

Xem `docs/metrics.md` để biết chi tiết.

## 10. Tạo figures

### Figures cơ bản (CLI)

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

### Phân tích đa mô hình (Notebook)

Sử dụng `notebook/analysis.ipynb` cùng với module `src/viz_analysis.py` để phân tích so sánh đa mô hình, đa prompt. Module này hỗ trợ:

- Tải và ghép metrics từ tất cả các cấu hình (model × prompt variant)
- Heatmap success rate theo factorial 3 yếu tố
- Main effect của method, model, prompt
- Prompt delta và sensitivity analysis
- Difficulty scaling
- Funnel analysis (pipeline stage pass rate)
- Phân bố lỗi faceted theo model

Render một qualitative plan trace:

```bash
python src/render_plan.py --problem-id bw_easy_001
```

## 11. Chạy Streamlit Demo

```bash
streamlit run app/streamlit_app.py
```

Ứng dụng đã được nâng cấp giao diện toàn diện với các tính năng:

- Bố cục so sánh trực tiếp Side-by-side giữa LLM-only và LLM + planner
- Nút **Run Both Methods** cho phép chạy song song 2 pipeline
- Thanh hiển thị tiến trình trực quan (Pipeline Progress Visualization)
- Trình biên tập cấu trúc prompt ngay trong UI (Editable Prompts)
- Trình hiển thị trạng thái khối hình học trực quan (Visual Block Rendering)
- Nhập nhiệm vụ bằng ngôn ngữ tự nhiên hoặc chọn từ các bài toán mẫu
- Hiển thị raw LLM output, JSON có cấu trúc và PDDL được tạo
- Hiển thị kết quả xác thực từng bước

Ứng dụng đọc credentials từ `.env`.

## 12. Các lỗi thường gặp

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

## 13. Tests

Chạy toàn bộ test suite:

```bash
pytest tests/
```

Các file test hiện có:

| File | Mô tả |
|---|---|
| `tests/test_validator.py` | Kiểm tra logic validate kế hoạch |
| `tests/test_evaluate_metrics.py` | Kiểm tra ghi/đọc metrics CSV và migration schema |
| `tests/test_viz_analysis.py` | Kiểm tra load dữ liệu và các plot helpers |

## 14. Tài liệu

Tài liệu bổ sung:

```text
docs/demo_design.md           Thiết kế demo và luồng trình bày
docs/metrics.md                Định nghĩa các chỉ số đánh giá
docs/experiment_protocol.md    Quy trình tái tạo thí nghiệm
docs/troubleshooting.md        Khắc phục sự cố thường gặp
```
