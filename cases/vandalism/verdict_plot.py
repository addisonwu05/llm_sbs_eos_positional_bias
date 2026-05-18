import matplotlib.pyplot as plt
import numpy as np
import os

# -------------------------------
# Data: [Guilty, Not Guilty]
# -------------------------------
data = {
    "GPT 4o": {"SBS": {"DP": [0, 30], "PD": [0, 30]}, "EOS": {"DP": [8, 22], "PD": [0, 30]}},
    "Claude 3.7 Sonnet": {"SBS": {"DP": [3, 27], "PD": [0, 30]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}}, 
    "Claude 4 Sonnet": {"SBS": {"DP": [11, 19], "PD": [2, 28]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Gemini 2.5 Flash": {"SBS": {"DP": [9, 21], "PD": [10, 20]}, "EOS": {"DP": [17, 13], "PD": [14, 16]}},
    "Llama-4-Maverick": {"SBS": {"DP": [5, 25], "PD": [0, 30]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Qwen2.5": {"SBS": {"DP": [11, 19], "PD": [5, 25]}, "EOS": {"DP": [27, 3], "PD": [1, 29]}},
}

# -------------------------------
# Output directory
# -------------------------------
os.makedirs("verdict_plots", exist_ok=True)

# Colors
guilty_color = "#2c2f7b"
not_guilty_color = "#a3a5d9"

# Helper function
def proportions(values):
    total = sum(values)
    return np.array(values) / total if total > 0 else np.array([0, 0])

# -------------------------------
# Generate 1 plot per model
# -------------------------------
for model, conditions in data.items():
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharey=True)
    plt.subplots_adjust(wspace=0.25)

    for j, mode in enumerate(["EOS", "SBS"]):
        ax = axes[j]
        dp = proportions(conditions[mode]["DP"])
        pd = proportions(conditions[mode]["PD"])
        x = np.arange(2)
        width = 0.6

        # Bars
        ax.bar(x, [dp[0], pd[0]], width, color=guilty_color, label="Guilty" if j == 0 else "")
        ax.bar(x, [dp[1], pd[1]], width, bottom=[dp[0], pd[0]], color=not_guilty_color, label="Not Guilty" if j == 0 else "")

        # Formatting
        ax.set_title(mode, fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(["DP", "PD"], fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        if j == 0:
            ax.set_ylabel("Proportion of Verdict", fontsize=10)

    # Legend & Title
    axes[1].legend(title="Verdict", loc="upper right")
    fig.suptitle(f"{model} — Verdict Proportions (EoS vs SbS)", fontsize=14, fontweight="bold", y=1.02)

    # Save
    filename = model.replace(" ", "_").replace(".", "") + ".png"
    filepath = os.path.join("verdict_plots", filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved {filepath}")

print("\nAll 10 verdict plots saved in the 'verdict_plots/' folder!")
