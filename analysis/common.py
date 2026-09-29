"""Shared helpers for locating and loading experiment outputs."""
import glob
import json
import os
from collections import defaultdict

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(REPO_DIR, "cases")
FIGURES_DIR = os.path.join(REPO_DIR, "figures")

ORDERS = ["dp", "pd"]

# Output directory for each response mode, per experiment variant
VARIANTS = {
    "main": {"EoS": "outputs_eos", "SbS": "outputs"},
    "interleaved": {"EoS": "outputs_eos_interleaved", "SbS": "outputs_interleaved"},
    "compress": {"SbS": "outputs", "SbS-Compressed": "outputs_compress"},
}

MODEL_NAMES = {
    "gpt-3.5-turbo": "GPT 3.5 Turbo",
    "gpt-4o": "GPT 4o",
    "gpt-5": "GPT 5",
    "gpt-5.4": "GPT 5.4",
    "claude-3-haiku-20240307": "Claude 3 Haiku",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku",
    "claude-3-7-sonnet-20250219": "Claude 3.7 Sonnet",
    "claude-sonnet-4-20250514": "Claude 4 Sonnet",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "gemini-2.0-flash": "Gemini 2.0 Flash",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-3-flash-preview": "Gemini 3 Flash",
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama 4 Maverick",
    "Qwen/Qwen2.5-72B-Instruct-Turbo": "Qwen 2.5 72B",
}


def all_case_dirs():
    return sorted(os.path.dirname(p) for p in glob.glob(os.path.join(CASES_DIR, "*", "case.yaml")))


def display_name(model):
    return MODEL_NAMES.get(model, model)


def model_runs(case_dir, out_dir, order, pattern="judgments_run*.json"):
    """Returns {model: [paths]} for run files under <case_dir>/<out_dir>/<order>/<model>/.

    Model names may contain a slash (e.g. "Qwen/Qwen2.5-72B-Instruct-Turbo").
    """
    order_path = os.path.join(case_dir, out_dir, order)
    runs = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(order_path, "**", pattern), recursive=True)):
        runs[os.path.relpath(os.path.dirname(path), order_path)].append(path)
    return runs


def verdict_counts(case_dir, out_dir):
    """Returns {model: {"dp": [guilty, not_guilty], "pd": [guilty, not_guilty]}}.

    Only counts runs whose verdict has been classified by parse_verdicts.py.
    """
    counts = defaultdict(lambda: {order: [0, 0] for order in ORDERS})
    for order in ORDERS:
        for model, paths in model_runs(case_dir, out_dir, order).items():
            for path in paths:
                with open(path) as f:
                    data = json.load(f)
                if not data or not isinstance(data[-1], bool):
                    continue  # not yet parsed
                counts[model][order][0 if data[-1] else 1] += 1
    return counts


def load_variant(case_dir, variant):
    """Returns {model: {mode: {"dp": [guilty, not_guilty], "pd": [...]}}} for one experiment variant."""
    data = defaultdict(dict)
    for mode, out_dir in VARIANTS[variant].items():
        for model, orders in verdict_counts(case_dir, out_dir).items():
            data[model][mode] = orders
    return data
