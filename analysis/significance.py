"""Order-effect significance tests on guilty-verdict counts.

For each model and response mode: Fisher's exact test of DP vs PD.
When both modes are present: Breslow-Day test of whether the DP/PD gap differs between them.
"""
import argparse
import os
import numpy as np
from scipy.stats import fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable
from common import CASES_DIR, VARIANTS, display_name, load_variant

ALPHA = 0.05


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case_dir", default=os.path.join(CASES_DIR, "murder"))
    parser.add_argument("--variant", choices=VARIANTS, default="main",
                        help="Which pair of output dirs to compare (see VARIANTS in common.py)")
    args = parser.parse_args()

    modes = list(VARIANTS[args.variant])
    all_data = load_variant(args.case_dir, args.variant)

    print(f"Fisher's Exact Test (DP vs PD within each mode) — {os.path.basename(args.case_dir)}, {args.variant}\n")

    for model in sorted(all_data):
        print(display_name(model))
        data = all_data[model]

        tables = {}
        for mode in modes:
            if mode not in data:
                print(f"  {mode}: no data")
                continue
            dp = data[mode]["dp"]
            pd = data[mode]["pd"]
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

        # Breslow-Day: does the DP/PD gap size differ between the two modes?
        if len(tables) == 2:
            strat = StratifiedTable([np.array(t) for t in tables.values()])
            bd = strat.test_equal_odds()
            bd_sig = "SIGNIFICANT (gap differs between modes)" if bd.pvalue < ALPHA else "not significant"
            print(f"  Breslow-Day ({' vs '.join(tables)}): p={bd.pvalue:.6f} → {bd_sig}")
        print()


if __name__ == "__main__":
    main()
