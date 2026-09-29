"""Mean (95% CI) SbS likelihood judgment at each evidence stage, across runs, for one model and order.

At each stage the model answers two questions about the newest piece of evidence:
P(evidence | not guilty) and P(evidence | guilty). The paper plots the guilty-conditioned one.

Example:
    python analysis/plot_sbs_trajectory.py --model gpt-4o --order dp
"""
import argparse
import json
import os
import matplotlib.pyplot as plt
import numpy as np
from common import CASES_DIR, FIGURES_DIR, ORDERS, model_runs

NUM_STAGES = 8  # 4 prosecution + 4 defense evidence blocks


def mean_ci(x, z=1.96):
    mean = np.mean(x)
    sem = np.std(x, ddof=1) / np.sqrt(len(x))
    return mean, z * sem


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case_dir", default=os.path.join(CASES_DIR, "murder"))
    parser.add_argument("--out_dir", default="outputs", help="SbS output dir (outputs or outputs_compress)")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--order", choices=ORDERS, default="dp")
    parser.add_argument("--condition", choices=["guilty", "not_guilty"], default="guilty",
                        help="Which likelihood to plot: P(evidence | guilty) or P(evidence | not guilty)")
    args = parser.parse_args()

    paths = model_runs(args.case_dir, args.out_dir, args.order).get(args.model, [])
    if not paths:
        raise SystemExit(f"No runs found for {args.model} in {os.path.join(args.case_dir, args.out_dir, args.order)}")

    # judgments alternate [P(e|not guilty), P(e|guilty)] per stage, followed by the final P(guilty) and verdict
    offset = 1 if args.condition == "guilty" else 0
    runs = []
    for path in paths:
        with open(path) as f:
            judgments = json.load(f)
        runs.append([int(judgments[2 * s + offset]) for s in range(NUM_STAGES)])
    runs = np.array(runs)

    means, cis = zip(*(mean_ci(runs[:, s]) for s in range(NUM_STAGES)))

    plt.figure()
    plt.errorbar(range(1, NUM_STAGES + 1), means, yerr=cis, fmt="o", capsize=5)
    plt.xlabel("Stage")
    plt.ylabel("Probability Judgment")

    os.makedirs(FIGURES_DIR, exist_ok=True)
    case = os.path.basename(os.path.normpath(args.case_dir))
    path = os.path.join(FIGURES_DIR, f"sbs_trajectory_{case}_{args.model.replace('/', '_')}_{args.order}.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved {path} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
