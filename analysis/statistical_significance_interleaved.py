import json
import os
import glob
from collections import defaultdict
from scipy.stats import fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable

CASE_DIR = os.path.join(os.path.dirname(__file__), "..", "cases", "murder")
ALPHA = 0.05

MODE_DIRS = {
    "SBS": "outputs_interleaved",
    "EOS": "outputs_eos_interleaved",
}


def scrape_counts(case_dir, out_dir):
    """Returns {model_name: {"dp": [guilty, not_guilty], "pd": [guilty, not_guilty]}}"""
    counts = defaultdict(lambda: {"dp": [0, 0], "pd": [0, 0]})

    for order in ["dp", "pd"]:
        order_path = os.path.join(case_dir, out_dir, order)
        if not os.path.isdir(order_path):
            continue

        pattern = os.path.join(order_path, "**", "judgments_run*.json")
        for path in glob.glob(pattern, recursive=True):
            # Derive model name from path relative to order_path
            rel = os.path.relpath(os.path.dirname(path), order_path)
            model = rel  # e.g. "claude-sonnet-4-6" or "meta-llama/Llama-4-..."

            with open(path) as f:
                data = json.load(f)

            if not isinstance(data[-1], bool):
                continue  # not yet parsed

            guilty = data[-1]
            if guilty is True:
                counts[model][order][0] += 1
            elif guilty is False:
                counts[model][order][1] += 1

    return counts


def main():
    # Collect data across both modes
    all_data = {}
    for mode, out_dir in MODE_DIRS.items():
        counts = scrape_counts(CASE_DIR, out_dir)
        for model, orders in counts.items():
            if model not in all_data:
                all_data[model] = {}
            all_data[model][mode] = {
                "DP": orders["dp"],
                "PD": orders["pd"],
            }

    print("Fisher's Exact Test (DP vs PD within each mode) — interleaved\n")

    for model in sorted(all_data):
        print(model)
        modes = all_data[model]

        tables = {}
        for mode in ["EOS", "SBS"]:
            if mode not in modes:
                print(f"  {mode}: no data")
                continue
            dp = modes[mode]["DP"]
            pd = modes[mode]["PD"]
            if sum(dp) == 0 or sum(pd) == 0:
                print(f"  {mode}: insufficient data")
                continue

            gap = dp[0] / sum(dp) - pd[0] / sum(pd)
            direction = "DP > PD" if gap > 0 else "PD > DP"

            table = [dp, pd]
            _, p = fisher_exact(table, alternative="two-sided")
            sig = "SIGNIFICANT" if p < ALPHA else "not significant"
            print(f"  {mode}: DP={dp} PD={pd}  gap={gap:+.2f} ({direction})  p={p:.6f} → {sig}")
            tables[mode] = table

        # Breslow-Day: does the DP/PD gap size differ between EOS and SBS?
        if "EOS" in tables and "SBS" in tables:
            import numpy as np
            strat = StratifiedTable([np.array(tables["EOS"]), np.array(tables["SBS"])])
            bd = strat.test_equal_odds()
            bd_sig = "SIGNIFICANT (gap differs between modes)" if bd.pvalue < ALPHA else "not significant"
            print(f"  Breslow-Day (EOS vs SBS): p={bd.pvalue:.6f} → {bd_sig}")
        print()


if __name__ == "__main__":
    main()
