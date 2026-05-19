import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# ROOT DIRECTORIES
# =========================================================

ROOT_FOLDERS = [
    "/Users/jasincekinmez/llm_sbs_eos_positional_bias-1/cases/murder/outputs_interleaved"
]

CONDITIONS = ["dp", "pd"]

# =========================================================
# PAPER-STYLE BAYES UPDATE
# =========================================================

def compute_predicted(observed, likelihoods):

    predicted = []

    for i, (p_not_g, p_g) in enumerate(likelihoods):

        # prior = PREVIOUS OBSERVED JUDGMENT
        if i == 0:
            prior = 0.5
        else:
            prior = observed[i - 1]

        posterior = (
            p_g * prior
        ) / (
            (p_g * prior) +
            (p_not_g * (1 - prior))
        )

        predicted.append(posterior)

    return np.array(predicted)

# =========================================================
# MAIN LOOP
# =========================================================

for root in ROOT_FOLDERS:

    print(f"\nROOT: {root}")

    for condition in CONDITIONS:

        condition_dir = os.path.join(root, condition)

        if not os.path.exists(condition_dir):
            continue

        # =================================================
        # LOOP OVER MODELS
        # =================================================

        for model_name in os.listdir(condition_dir):

            model_dir = os.path.join(condition_dir, model_name)

            if not os.path.isdir(model_dir):
                continue

            print(f"\nProcessing: {model_name}")

            # =================================================
            # USE merged_run FILES
            # =================================================

            json_files = sorted(
    glob.glob(
        os.path.join(
            model_dir,
            "**",
            "merged_run*.json"
        ),
        recursive=True
    )
)

            print(f"Found {len(json_files)} runs")

            all_observed = []
            all_predicted = []

            # =================================================
            # LOOP OVER RUNS
            # =================================================

            for json_file in json_files:

                try:

                    with open(json_file, "r") as f:
                        data = json.load(f)

                    # =================================================
                    # STRICT VALIDATION
                    # =================================================

                    if not isinstance(data, dict):
                        continue

                    if (
                        "intermediate_verdicts" not in data or
                        "diagnostics" not in data
                    ):
                        continue

                    if (
                        not isinstance(data["intermediate_verdicts"], list)
                        or
                        not isinstance(data["diagnostics"], list)
                    ):
                        continue

                    # =================================================
                    # OBSERVED
                    # =================================================

                    observed = np.array([
                        int(x["prob"]) / 100
                        for x in data["intermediate_verdicts"]
                        if (
                            isinstance(x, dict)
                            and
                            "prob" in x
                        )
                    ])

                    # =================================================
                    # LIKELIHOODS
                    # =================================================

                    likelihoods = [
                        (
                            int(x["not_guilty_likelihood"]) / 100,
                            int(x["guilty_likelihood"]) / 100
                        )
                        for x in data["diagnostics"]
                        if (
                            isinstance(x, dict)
                            and
                            "not_guilty_likelihood" in x
                            and
                            "guilty_likelihood" in x
                        )
                    ]

                    # =================================================
                    # LENGTH CHECK
                    # =================================================

                    if len(observed) != len(likelihoods):
                        print(
                            f"Length mismatch: {json_file}"
                        )
                        continue

                    if len(observed) == 0:
                        continue

                    # =================================================
                    # COMPUTE BAYESIAN PREDICTION
                    # =================================================

                    predicted = compute_predicted(
                        observed,
                        likelihoods
                    )

                    all_observed.append(observed)
                    all_predicted.append(predicted)

                except Exception as e:

                    print(f"Skipping {json_file}: {e}")

            # =================================================
            # VALID RUNS?
            # =================================================

            if len(all_observed) == 0:

                print(f"No valid runs for {model_name}")
                continue

            # =================================================
            # STACK
            # =================================================

            all_observed = np.vstack(all_observed)
            all_predicted = np.vstack(all_predicted)

            # =================================================
            # AVERAGE OVER ~30 RUNS
            # =================================================

            mean_observed = all_observed.mean(axis=0)
            mean_predicted = all_predicted.mean(axis=0)

            sem_observed = (
                all_observed.std(axis=0)
                /
                np.sqrt(len(all_observed))
            )

            sem_predicted = (
                all_predicted.std(axis=0)
                /
                np.sqrt(len(all_predicted))
            )

            stages = np.arange(
                1,
                len(mean_observed) + 1
            )

            # =================================================
            # PLOT
            # =================================================

            plt.figure(figsize=(8, 5))

            # observed
            plt.plot(
                stages,
                mean_observed,
                marker="o",
                linewidth=2,
                label="Observed"
            )

            # predicted
            plt.plot(
                stages,
                mean_predicted,
                marker="o",
                linewidth=2,
                label="Predicted"
            )

            # observed SEM
            plt.fill_between(
                stages,
                np.clip(
                    mean_observed - sem_observed,
                    0,
                    1
                ),
                np.clip(
                    mean_observed + sem_observed,
                    0,
                    1
                ),
                alpha=0.2
            )

            # predicted SEM
            plt.fill_between(
                stages,
                np.clip(
                    mean_predicted - sem_predicted,
                    0,
                    1
                ),
                np.clip(
                    mean_predicted + sem_predicted,
                    0,
                    1
                ),
                alpha=0.2
            )

            plt.ylim(0, 1)

            plt.xlabel("Stage")
            plt.ylabel("Probability Judgment")

            plt.title(
                f"{os.path.basename(root)} | "
                f"{condition} | "
                f"{model_name}"
            )

            plt.legend()

            plt.tight_layout()

            # =================================================
            # SAVE PNG
            # =================================================

            save_path = os.path.join(
                model_dir,
                "bayes_plot.png"
            )

            plt.savefig(save_path, dpi=300)

            plt.close()

            print(f"Saved: {save_path}")

print("\nDONE.")