# JARVIS Model Training & Fine-Tuning Guide

This guide describes how to use the normalized JARVIS datasets for local supervised fine-tuning (SFT) and evaluation.

---

## 1. Hardware Feasibility & Constraints

- **Processor**: Intel Core i5/i7 (CPU inference, AVX2 support)
- **Graphics**: Intel Iris Xe Integrated Graphics (No CUDA acceleration)
- **RAM**: 16 GB Total System Memory (~12 GB available)
- **Storage**: ~78 GB Free Disk Space

> [!IMPORTANT]
> Because this system has integrated graphics without NVIDIA CUDA, full parameter fine-tuning on this local laptop is not recommended due to severe memory and compute constraints. 
> The primary architecture uses **In-Context Learning (ICL) via Runtime Retrieval** (`jarvis/retrieval/dataset_retriever.py`). 
> If offline fine-tuning is desired, use QLoRA on a cloud instance or Google Colab with an NVIDIA T4/A100 GPU using the prepared `splits/train.jsonl`.

---

## 2. Dataset Formats for Fine-Tuning

The dataset splits are located in `datasets/splits/`:
- `train.jsonl`: 6,272 examples (70%)
- `validation.jsonl`: 1,339 examples (15%)
- `test.jsonl`: 1,362 examples (15%)

### Sample ChatML / Instruct Formatting
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are J.A.R.V.I.S., an autonomous desktop AI agent. Translate user commands into structured JSON tool plans with strict verification criteria."
    },
    {
      "role": "user",
      "content": "Open Chrome and search for robotics tutorials"
    },
    {
      "role": "assistant",
      "content": "{\"intent\":\"web_search\",\"target_application\":\"chrome\",\"steps\":[{\"tool\":\"launch_app\",\"arguments\":{\"app_name\":\"chrome\"}},{\"tool\":\"search_web\",\"arguments\":{\"query\":\"robotics tutorials\"}}],\"expected_result\":\"Robotics tutorial search results are displayed\",\"verification\":[\"browser_is_open\",\"search_results_are_visible\"]}"
    }
  ]
}
```

---

## 3. Recommended Fine-Tuning Hyperparameters (Cloud / GPU)

- **Base Model**: `unsloth/Phi-3-mini-4k-instruct` or `unsloth/Llama-3.2-3B-Instruct`
- **Method**: QLoRA (4-bit quantization, rank=16, alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
- **Learning Rate**: 2e-4 with cosine decay
- **Batch Size**: 4 per device with 4 gradient accumulation steps (effective batch size: 16)
- **Epochs**: 3
- **Optimizer**: AdamW 8-bit

---

## 4. Benchmark Evaluation Without Re-Training

You can evaluate any local GGUF model or rule-based parser directly against the test set:

```powershell
python scripts/evaluate_dataset.py
```

This measures:
- Primary Tool Selection Accuracy
- Multi-Step Task Resolution
- Planning Latency (ms)
- Intent Classification Breakdown
