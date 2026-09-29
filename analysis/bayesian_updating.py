"""Compares a model's intermediate P(guilty) with a Bayesian update built from its own likelihoods.

For each interleaved run, the predicted posterior at step i uses the model's observed P(guilty)
at step i-1 as the prior (0.5 at the first step) and its reported P(evidence | guilty) and
P(evidence | not guilty) for step i. Plots mean observed vs. predicted (± SEM) across runs.
Reads the merged_run*.json files written by merge_interleaved.py.
"""
import argparse
import glob
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from common import CASES_DIR, FIGURES_DIR, ORDERS

INTERLEAVED_DIRS = ["outputs_interleaved", "outputs_eos_interleaved"]


def compute_predicted(observed, likelihoods):
    predicted = []
    for i, (p_not_g, p_g) in enumerate(likelihoods):
        # prior = previous observed judgment
        prior = 0.5 if i == 0 else observed[i - 1]
        posterior = (p_g * prior) / ((p_g * prior) + (p_not_g * (1 - prior)))
        predicted.append(posterior)
    return np.array(predicted)


def load_run(json_file):
    """Returns (observed, likelihoods) for one merged run, or None if it is malformed."""
    with open(json_file) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("intermediate_verdicts"), list) or not isinstance(data.get("diagnostics"), list):
        return None

    observed = np.array([
        int(x["prob"]) / 100
        for x in data["intermediate_verdicts"]
        if isinstance(x, dict) and "prob" in x
    ])
    likelihoods = [
        (int(x["not_guilty_likelihood"]) / 100, int(x["guilty_likelihood"]) / 100)
        for x in data["diagnostics"]
        if isinstance(x, dict) and "not_guilty_likelihood" in x and "guilty_likelihood" in x
    ]

    if len(observed) != len(likelihoods):
        print(f"Length mismatch: {json_file}")
        return None
    if len(observed) == 0:
        return None
    return observed, likelihoods


def plot(stages, observed, predicted, title, save_path):
    plt.figure(figsize=(8, 5))
    for runs, label in [(observed, "Observed"), (predicted, "Predicted")]:
        mean = runs.mean(axis=0)
        sem = runs.std(axis=0) / np.sqrt(len(runs))
        plt.plot(stages, mean, marker="o", linewidth=2, label=label)
        plt.fill_between(stages, np.clip(mean - sem, 0, 1), np.clip(mean + sem, 0, 1), alpha=0.2)

    plt.ylim(0, 1)
    plt.xlabel("Stage")
    plt.ylabel("Probability Judgment")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Saved: {save_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case_dir", default=os.path.join(CASES_DIR, "murder"))
    args = parser.parse_args()

    out_root = os.path.join(FIGURES_DIR, "bayes")
    os.makedirs(out_root, exist_ok=True)
    case = os.path.basename(os.path.normpath(args.case_dir))

    for out_dir in INTERLEAVED_DIRS:
        for condition in ORDERS:
            condition_dir = os.path.join(args.case_dir, out_dir, condition)
            if not os.path.isdir(condition_dir):
                continue

            for model_name in sorted(os.listdir(condition_dir)):
                model_dir = os.path.join(condition_dir, model_name)
                if not os.path.isdir(model_dir):
                    continue

                json_files = sorted(glob.glob(os.path.join(model_dir, "**", "merged_run*.json"), recursive=True))
                print(f"\n{out_dir}/{condition}/{model_name}: found {len(json_files)} runs")

                all_observed, all_predicted = [], []
                for json_file in json_files:
                    try:
                        run = load_run(json_file)
                    except Exception as e:
                        print(f"Skipping {json_file}: {e}")
                        continue
                    if run is None:
                        continue
                    observed, likelihoods = run
                    all_observed.append(observed)
                    all_predicted.append(compute_predicted(observed, likelihoods))

                if not all_observed:
                    print(f"No valid runs for {model_name}")
                    continue

                all_observed = np.vstack(all_observed)
                all_predicted = np.vstack(all_predicted)
                stages = np.arange(1, all_observed.shape[1] + 1)

                save_path = os.path.join(out_root, f"{case}_{out_dir}_{condition}_{model_name}.png")
                plot(stages, all_observed, all_predicted, f"{out_dir} | {condition} | {model_name}", save_path)


if __name__ == "__main__":
    main()
