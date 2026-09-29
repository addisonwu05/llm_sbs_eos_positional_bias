"""Stacked bars of guilty / not-guilty verdict proportions: one row per model, one column per
response mode, with DP and PD bars in each panel.

Example (GPT model-family figure):
    python analysis/plot_verdicts.py --models gpt-3.5-turbo gpt-4o gpt-5 --out gpt_overtime.png
"""
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
from common import CASES_DIR, FIGURES_DIR, VARIANTS, display_name, load_variant

guilty_color = "#2c2f7b"
not_guilty_color = "#a3a5d9"


def proportions(vals):
    total = sum(vals)
    return np.array(vals) / total if total > 0 else np.array([0.0, 0.0])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case_dir", default=os.path.join(CASES_DIR, "murder"))
    parser.add_argument("--variant", choices=VARIANTS, default="main",
                        help="Which pair of output dirs to compare (see VARIANTS in common.py)")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Models to plot, in row order (default: every model with results)")
    parser.add_argument("--out", default=None, help="Output filename (saved under figures/)")
    args = parser.parse_args()

    modes = list(VARIANTS[args.variant])
    data = load_variant(args.case_dir, args.variant)
    models = args.models or sorted(data)
    if not models:
        raise SystemExit(f"No parsed results found in {args.case_dir} for variant '{args.variant}'. "
                         "Run the experiments and analysis/parse_verdicts.py first.")

    fig = plt.figure(figsize=(9, 2.25 * len(models)))
    gs = GridSpec(
        nrows=len(models),
        ncols=len(modes) + 1,
        width_ratios=[1.4] + [3] * len(modes),   # label | mode 1 | mode 2
        hspace=0.5,
        wspace=0.35,
    )

    for i, model in enumerate(models):
        ax_label = fig.add_subplot(gs[i, 0])
        ax_label.axis("off")
        ax_label.text(1.0, 0.5, display_name(model), ha="right", va="center", fontsize=12, fontweight="bold")

        for j, mode in enumerate(modes):
            ax = fig.add_subplot(gs[i, j + 1])
            ax.set_title(mode, fontsize=11, fontweight="bold")

            if mode not in data.get(model, {}):
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes, color="gray")
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            dp = proportions(data[model][mode]["dp"])
            pd = proportions(data[model][mode]["pd"])
            x = np.arange(2)
            width = 0.6

            ax.bar(x, [dp[0], pd[0]], width, color=guilty_color)
            ax.bar(x, [dp[1], pd[1]], width, bottom=[dp[0], pd[0]], color=not_guilty_color)

            ax.set_xticks(x)
            ax.set_xticklabels(["DP", "PD"], fontsize=9)
            ax.set_ylim(0, 1)
            ax.grid(axis="y", linestyle="--", alpha=0.35)

            if j == 0:
                ax.set_ylabel("Proportion", fontsize=10)

    legend_handles = [
        Patch(facecolor=guilty_color, label="Guilty"),
        Patch(facecolor=not_guilty_color, label="Not Guilty"),
    ]
    fig.legend(handles=legend_handles, title="Verdict", loc="upper center", ncol=2, frameon=True,
               bbox_to_anchor=(0.5, 1.03))
    plt.subplots_adjust(top=0.92)

    os.makedirs(FIGURES_DIR, exist_ok=True)
    out = args.out or f"verdicts_{os.path.basename(os.path.normpath(args.case_dir))}_{args.variant}.png"
    path = os.path.join(FIGURES_DIR, out)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved {path}")


if __name__ == "__main__":
    main()
