import json
import os
import glob

CASE_DIR = "cases/murder"
INTERLEAVED_DIRS = ["outputs_interleaved", "outputs_eos_interleaved"]


def merge_run(judgments_path, verdict_trail_path):
    with open(judgments_path) as f:
        judgments = json.load(f)
    with open(verdict_trail_path) as f:
        verdict_trail = json.load(f)

    # Last element is parsed bool, second-to-last is verdict text, third-to-last is final prob
    final_guilty = judgments[-1] if isinstance(judgments[-1], bool) else None
    final_verdict = judgments[-2] if isinstance(judgments[-2], str) else None
    final_prob = judgments[-3] if final_verdict else judgments[-2]

    # Everything before the final prob+verdict+bool are diagnostic pairs
    n_diagnostics_end = 3 if isinstance(judgments[-1], bool) else 2
    diagnostic_nums = judgments[:-n_diagnostics_end]

    # Group into pairs: (not_guilty_likelihood, guilty_likelihood)
    diagnostics = [
        {"not_guilty_likelihood": diagnostic_nums[i], "guilty_likelihood": diagnostic_nums[i + 1]}
        for i in range(0, len(diagnostic_nums), 2)
    ]

    return {
        "type": "merged_interleaved",
        "intermediate_verdicts": verdict_trail,
        "diagnostics": diagnostics,
        "final": {
            "prob": final_prob,
            "verdict": final_verdict,
            "guilty": final_guilty,
        },
    }


def main():
    created = 0
    skipped = 0

    for out_dir in INTERLEAVED_DIRS:
        pattern = os.path.join(CASE_DIR, out_dir, "**", "judgments_run*.json")
        for judgments_path in sorted(glob.glob(pattern, recursive=True)):
            run_dir = os.path.dirname(judgments_path)
            basename = os.path.basename(judgments_path)
            run_id = basename.replace("judgments_", "")  # e.g. "run1.json"

            verdict_trail_path = os.path.join(run_dir, f"verdict_trail_{run_id}")
            merged_path = os.path.join(run_dir, f"merged_{run_id}")

            if os.path.exists(merged_path):
                skipped += 1
                continue

            if not os.path.exists(verdict_trail_path):
                print(f"SKIP (no verdict_trail): {judgments_path}")
                skipped += 1
                continue

            merged = merge_run(judgments_path, verdict_trail_path)

            with open(merged_path, "w") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            created += 1

    print(f"Done — created {created}, skipped {skipped}")


if __name__ == "__main__":
    main()
