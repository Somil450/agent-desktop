"""
Dataset Inspection & Manifest Generation for JARVIS NLU.
Queries HuggingFace & GitHub APIs to inspect remote dataset repositories,
calculate file sizes, extract licenses, and generate initial manifests.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path
from huggingface_hub import HfApi

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFESTS_DIR = REPO_ROOT / "datasets" / "manifests"
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_CONFIGS = {
    "omniact": {
        "repo_id": "Writer/omniact",
        "repo_type": "dataset",
        "platform": "HuggingFace",
        "official_url": "https://huggingface.co/datasets/Writer/omniact",
        "license": "Apache-2.0",
        "purpose": "Natural language desktop tasks and PyAutoGUI action demonstrations.",
        "download_policy": "full_metadata_and_annotations",
        "max_budget_mb": 500,
    },
    "agentnet": {
        "repo_id": "xlangai/AgentNet",
        "repo_type": "dataset",
        "platform": "HuggingFace",
        "official_url": "https://huggingface.co/datasets/xlangai/AgentNet",
        "github_url": "https://github.com/xlang-ai/OpenCUA",
        "license": "CC-BY-4.0",
        "purpose": "Human-annotated multi-step computer-use trajectories across OSes.",
        "download_policy": "selective_windows_trajectories",
        "max_budget_mb": 1500,  # ~1.35 GB for agentnet_win_mac_18k.jsonl + metadata
    },
    "screenspot_pro": {
        "repo_id": "likaixin/ScreenSpot-Pro",
        "repo_type": "dataset",
        "platform": "HuggingFace",
        "official_url": "https://huggingface.co/datasets/likaixin/ScreenSpot-Pro",
        "github_url": "https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding",
        "license": "Apache-2.0",
        "purpose": "Professional application GUI element localization & grounding.",
        "download_policy": "selective_windows_annotations",
        "max_budget_mb": 200,
    },
    "windows_agent_arena": {
        "repo_id": "microsoft/WindowsAgentArena",
        "platform": "GitHub",
        "official_url": "https://github.com/microsoft/WindowsAgentArena",
        "docs_url": "https://microsoft.github.io/WindowsAgentArena/",
        "license": "MIT",
        "purpose": "Windows desktop task evaluation benchmarks & task definitions.",
        "download_policy": "evaluation_tasks_and_benchmarks",
        "max_budget_mb": 100,
    }
}

def inspect_hf_dataset(api: HfApi, name: str, cfg: dict) -> dict:
    repo_id = cfg["repo_id"]
    print(f"[*] Inspecting HuggingFace repository: {repo_id}...")
    try:
        ds_info = api.dataset_info(repo_id)
        sha = ds_info.sha or "main"
        files = list(api.list_repo_tree(repo_id, repo_type="dataset", recursive=True))
        
        file_list = []
        total_size = 0
        windows_files = []
        
        for f in files:
            size = getattr(f, "size", 0) or 0
            path = f.path
            total_size += size
            is_win = "windows" in path.lower() or "win" in path.lower()
            file_entry = {
                "path": path,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "is_windows": is_win
            }
            file_list.append(file_entry)
            if is_win:
                windows_files.append(file_entry)

        return {
            "name": name,
            "repo_id": repo_id,
            "status": "available",
            "commit_sha": sha,
            "total_files": len(file_list),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "windows_files_count": len(windows_files),
            "files": file_list[:50],  # sample top 50 in manifest
            "license": cfg["license"],
            "url": cfg["official_url"],
            "purpose": cfg["purpose"],
            "download_policy": cfg["download_policy"]
        }
    except Exception as e:
        print(f"[!] Error inspecting {repo_id}: {e}")
        return {
            "name": name,
            "repo_id": repo_id,
            "status": "error",
            "error": str(e),
            "license": cfg["license"],
            "url": cfg["official_url"]
        }

def inspect_github_repo(name: str, cfg: dict) -> dict:
    repo_id = cfg["repo_id"]
    print(f"[*] Inspecting GitHub repository: {repo_id}...")
    api_url = f"https://api.github.com/repos/{repo_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "JARVIS-Dataset-Inspector"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            default_branch = data.get("default_branch", "main")
            return {
                "name": name,
                "repo_id": repo_id,
                "status": "available",
                "default_branch": default_branch,
                "stars": data.get("stargazers_count", 0),
                "license": data.get("license", {}).get("name", cfg["license"]),
                "url": cfg["official_url"],
                "purpose": cfg["purpose"],
                "download_policy": cfg["download_policy"],
                "size_kb": data.get("size", 0)
            }
    except Exception as e:
        print(f"[!] Error inspecting GitHub repo {repo_id}: {e}")
        return {
            "name": name,
            "repo_id": repo_id,
            "status": "error",
            "error": str(e),
            "license": cfg["license"],
            "url": cfg["official_url"]
        }

def run_inspection():
    api = HfApi()
    inspection_results = {}
    
    for name, cfg in DATASET_CONFIGS.items():
        if cfg["platform"] == "HuggingFace":
            inspection_results[name] = inspect_hf_dataset(api, name, cfg)
        else:
            inspection_results[name] = inspect_github_repo(name, cfg)

    # 1. Write dataset_versions.json
    versions = {}
    for name, res in inspection_results.items():
        versions[name] = {
            "source": res.get("url"),
            "commit_or_branch": res.get("commit_sha") or res.get("default_branch", "unknown"),
            "status": res.get("status"),
            "license": res.get("license"),
            "policy": DATASET_CONFIGS[name]["download_policy"]
        }
    with open(MANIFESTS_DIR / "dataset_versions.json", "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    # 2. Write licenses.json
    licenses = {}
    for name, cfg in DATASET_CONFIGS.items():
        licenses[name] = {
            "dataset_name": name,
            "license_type": cfg["license"],
            "official_url": cfg["official_url"],
            "commercial_use_allowed": cfg["license"] in ["Apache-2.0", "MIT", "CC-BY-4.0"],
            "attribution_required": True,
            "notes": f"Attributed to {cfg['repo_id']}. Full compliance with license terms."
        }
    with open(MANIFESTS_DIR / "licenses.json", "w", encoding="utf-8") as f:
        json.dump(licenses, f, indent=2)

    # 3. Write downloads.json
    with open(MANIFESTS_DIR / "downloads.json", "w", encoding="utf-8") as f:
        json.dump(inspection_results, f, indent=2)

    print("\n" + "="*70)
    print("DATASET INSPECTION SUMMARY")
    print("="*70)
    for name, res in inspection_results.items():
        status = res.get("status", "unknown")
        total_sz = res.get("total_size_mb", 0)
        license_str = res.get("license", "unknown")
        print(f"[{status.upper()}] {name:20} | Total: {total_sz} MB | License: {license_str}")
    print("="*70)
    print(f"Manifests written to {MANIFESTS_DIR}")

if __name__ == "__main__":
    run_inspection()
