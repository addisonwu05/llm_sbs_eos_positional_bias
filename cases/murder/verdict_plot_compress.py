import matplotlib.pyplot as plt
import numpy as np
import os

# [Guilty, Not Guilty]
data = {
    "GPT 3.5 Turbo": {
        "SBS":      {"DP": [30, 0],  "PD": [11, 0]},
        "SBS-Comp": {"DP": [29, 1],  "PD": [29, 1]},
    },
    "GPT 4o": {
        "SBS":      {"DP": [0, 0],   "PD": [0, 0]},
        "SBS-Comp": {"DP": [27, 3],  "PD": [27, 3]},
    },
    "GPT 5.4": {
        "SBS":      {"DP": [2, 28],  "PD": [0, 30]},
        "SBS-Comp": {"DP": [3, 27],  "PD": [0, 30]},
    },
    "Gemini 2.0 Flash": {
        "SBS":      {"DP": [15, 15], "PD": [19, 11]},
        "SBS-Comp": {"DP": [15, 15], "PD": [0, 0]},
    },
    "Gemini 2.5 Flash": {
        "SBS":      {"DP": [24, 6],  "PD": [24, 5]},
        "SBS-Comp": {"DP": [20, 10], "PD": [18, 12]},
    },
    "Gemini 3 Flash": {
        "SBS":      {"DP": [9, 21],  "PD": [21, 9]},
        "SBS-Comp": {"DP": [23, 7],  "PD": [11, 19]},
    },
    "Claude 4 Sonnet": {
        "SBS":      {"DP": [28, 2],  "PD": [26, 4]},
        "SBS-Comp": {"DP": [30, 0],  "PD": [12, 18]},
    },
    "Claude Sonnet 4.6": {
        "SBS":      {"DP": [5, 25],  "PD": [2, 28]},
        "SBS-Comp": {"DP": [1, 29],  "PD": [7, 23]},
    },
}

os.makedirs("verdict_plots", exist_ok=True)

guilty_color     = "#2c2f7b"
not_guilty_color = "#a3a5d9"


def proportions(values):
    total = sum(values)
    return np.array(values) / total if total > 0 else np.array([0.0, 0.0])


for model, conditions in data.items():
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharey=True)
    plt.subplots_adjust(wspace=0.25)

    for j, mode in enumerate(["SBS", "SBS-Comp"]):
        ax = axes[j]
        dp = proportions(conditions[mode]["DP"])
        pd = proportions(conditions[mode]["PD"])
        x = np.arange(2)
        width = 0.6

        ax.bar(x, [dp[0], pd[0]], width, color=guilty_color,     label="Guilty"     if j == 0 else "")
        ax.bar(x, [dp[1], pd[1]], width, bottom=[dp[0], pd[0]], color=not_guilty_color, label="Not Guilty" if j == 0 else "")

        ax.set_title(mode, fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(["DP", "PD"], fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        if j == 0:
            ax.set_ylabel("Proportion of Verdict", fontsize=10)

    axes[1].legend(title="Verdict", loc="upper right")
    fig.suptitle(f"{model} — Verdict Proportions (SbS vs SbS-Compressed)", fontsize=14, fontweight="bold", y=1.02)

    filename = model.replace(" ", "_").replace(".", "") + "_compress.png"
    filepath = os.path.join("verdict_plots", filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved {filepath}")

print("\nAll verdict plots saved in the 'verdict_plots/' folder!")
