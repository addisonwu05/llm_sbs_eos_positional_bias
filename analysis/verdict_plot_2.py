#   "GPT 3.5 Turbo": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [26, 4], "PD": [30, 0]}},
#     "GPT 4o": {"SBS": {"DP": [30, 0], "PD": [26, 4]}, "EOS": {"DP": [30, 0], "PD": [6, 24]}},
#     "GPT 5": {"SBS": {"DP": [19, 11], "PD": [29, 1]}, "EOS": {"DP": [16, 14], "PD": [30, 0]}},
#     "Claude 3 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 7]}},
#     "Claude 3.5 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 8]}},
#     "Claude 3.7 Sonnet": {"SBS": {"DP": [25, 5], "PD": [30, 0]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
#     "Claude 4 Sonnet": {"SBS": {"DP": [28, 2], "PD": [26, 4]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
#     "Gemini 2.0 Flash": {"SBS": {"DP": [25, 1], "PD": [22, 3]}, "EOS": {"DP": [27, 3], "PD": [14, 16]}},
#     "Gemini 2.5 Flash": {"SBS": {"DP": [24, 6], "PD": [25, 4]}, "EOS": {"DP": [27, 3], "PD": [21, 9]}},
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

# -------------------------------
# Data
# -------------------------------
data = {
     "Claude 3 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 7]}},
     "Claude 3.5 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 8]}},
     "Claude 3.7 Sonnet": {"SBS": {"DP": [25, 5], "PD": [30, 0]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
     "Claude 4 Sonnet": {"SBS": {"DP": [28, 2], "PD": [26, 4]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
}

# -------------------------------
# Styling
# -------------------------------
guilty_color = "#2c2f7b"
not_guilty_color = "#a3a5d9"

def proportions(vals):
    return np.array(vals) / sum(vals)

models = list(data.keys())

# -------------------------------
# Figure + GridSpec
# -------------------------------
fig = plt.figure(figsize=(9, 9))
gs = GridSpec(
    nrows=len(models),
    ncols=3,
    width_ratios=[1.2, 3, 3],   # label | EOS | SBS
    hspace=0.5,
    wspace=0.35
)

# -------------------------------
# Plot rows
# -------------------------------
for i, model in enumerate(models):

    # Model label column
    ax_label = fig.add_subplot(gs[i, 0])
    ax_label.axis("off")
    ax_label.text(
        1.0, 0.5, model,
        ha="right",
        va="center",
        fontsize=12,
        fontweight="bold"
    )

    for j, mode in enumerate(["EOS", "SBS"]):
        ax = fig.add_subplot(gs[i, j + 1])

        dp = proportions(data[model][mode]["DP"])
        pd = proportions(data[model][mode]["PD"])

        x = np.arange(2)
        width = 0.6

        ax.bar(x, [dp[0], pd[0]], width, color=guilty_color)
        ax.bar(
            x, [dp[1], pd[1]],
            width,
            bottom=[dp[0], pd[0]],
            color=not_guilty_color
        )

        ax.set_xticks(x)
        ax.set_xticklabels(["DP", "PD"], fontsize=9)
        ax.set_ylim(0, 1)
        ax.grid(axis="y", linestyle="--", alpha=0.35)

        ax.set_title(mode, fontsize=11, fontweight="bold")

        if j == 0:
            ax.set_ylabel("Proportion", fontsize=10)

# -------------------------------
# Legend (FIXED: moved up)
# -------------------------------
legend_handles = [
    Patch(facecolor=guilty_color, label="Guilty"),
    Patch(facecolor=not_guilty_color, label="Not Guilty"),
]

fig.legend(
    handles=legend_handles,
    title="Verdict",
    loc="upper center",
    ncol=2,
    frameon=True,
    bbox_to_anchor=(0.5, 1.03)   # ← moved up
)

# -------------------------------
# Layout fix (more top space)
# -------------------------------
plt.subplots_adjust(top=0.92)

# -------------------------------
# Save
# -------------------------------
plt.savefig(
    "claude_overtime.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close(fig)

print("✅ Saved GPT_models_vertical_clean_fixed.png")


# import matplotlib.pyplot as plt
# import numpy as np
# import os
# from matplotlib.patches import Patch   # ← ADDED

# # -------------------------------
# # Data: [Guilty, Not Guilty]
# # -------------------------------
# data = {
#     "GPT 3.5 Turbo": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [26, 4], "PD": [30, 0]}},
#     "GPT 4o": {"SBS": {"DP": [30, 0], "PD": [26, 3]}, "EOS": {"DP": [30, 0], "PD": [6, 24]}},
#     "GPT 5": {"SBS": {"DP": [19, 11], "PD": [29, 1]}, "EOS": {"DP": [16, 14], "PD": [30, 0]}},
#     "Claude 3 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 7]}},
#     "Claude 3.5 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 8]}},
#     "Claude 3.7 Sonnet": {"SBS": {"DP": [25, 5], "PD": [30, 0]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
#     "Claude 4 Sonnet": {"SBS": {"DP": [28, 2], "PD": [26, 4]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
#     "Gemini 2.0 Flash": {"SBS": {"DP": [25, 1], "PD": [22, 3]}, "EOS": {"DP": [27, 3], "PD": [14, 16]}},
#     "Gemini 2.5 Flash": {"SBS": {"DP": [24, 6], "PD": [25, 4]}, "EOS": {"DP": [27, 3], "PD": [21, 9]}},
# }

# # -------------------------------
# # Output directory
# # -------------------------------
# os.makedirs("verdict_plots", exist_ok=True)

# # Colors
# guilty_color = "#2c2f7b"
# not_guilty_color = "#a3a5d9"

# # Helper function
# def proportions(values):
#     total = sum(values)
#     return np.array(values) / total if total > 0 else np.array([0, 0])

# # -------------------------------
# # Generate 1 plot per model
# # -------------------------------
# for model, conditions in data.items():
#     fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharey=True)
#     plt.subplots_adjust(wspace=0.25)

#     for j, mode in enumerate(["EOS", "SBS"]):
#         ax = axes[j]
#         dp = proportions(conditions[mode]["DP"])
#         pd = proportions(conditions[mode]["PD"])
#         x = np.arange(2)
#         width = 0.6

#         # Bars
#         ax.bar(x, [dp[0], pd[0]], width, color=guilty_color)
#         ax.bar(x, [dp[1], pd[1]], width, bottom=[dp[0], pd[0]], color=not_guilty_color)

#         # Formatting
#         ax.set_title(mode, fontsize=12, fontweight="bold")
#         ax.set_xticks(x)
#         ax.set_xticklabels(["DP", "PD"], fontsize=10)
#         ax.set_ylim(0, 1)
#         ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
#         ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
#         ax.grid(axis="y", linestyle="--", alpha=0.4)
#         if j == 0:
#             ax.set_ylabel("Proportion of Verdict", fontsize=10)

#     # -------------------------------
#     # Guilty / Not Guilty Legend (ADDED)
#     # -------------------------------
#     legend_handles = [
#         Patch(facecolor=guilty_color, label="Guilty"),
#         Patch(facecolor=not_guilty_color, label="Not Guilty"),
#     ]

#     fig.legend(handles=legend_handles, title="Verdict", loc="upper right")

#     # Title
#     fig.suptitle(f"{model} — Verdict Proportions (EoS vs SbS)", fontsize=14, fontweight="bold", y=1.02)

#     # Save
#     filename = model.replace(" ", "_").replace(".", "") + ".png"
#     filepath = os.path.join("verdict_plots", filename)
#     plt.tight_layout()
#     plt.savefig(filepath, dpi=300, bbox_inches="tight")
#     plt.close(fig)
#     print(f"✅ Saved {filepath}")

# print("\nAll verdict plots saved in the 'verdict_plots/' folder!")
