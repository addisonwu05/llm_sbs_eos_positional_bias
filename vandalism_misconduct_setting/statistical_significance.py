from scipy.stats import fisher_exact

data = {
    "GPT 4o": {"SBS": {"DP": [0, 30], "PD": [0, 30]}, "EOS": {"DP": [8, 22], "PD": [0, 30]}},
    "Claude 3.7 Sonnet": {"SBS": {"DP": [3, 27], "PD": [0, 30]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}}, 
    "Claude 4 Sonnet": {"SBS": {"DP": [11, 19], "PD": [2, 28]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Gemini 2.5 Flash": {"SBS": {"DP": [9, 21], "PD": [10, 20]}, "EOS": {"DP": [17, 13], "PD": [14, 16]}},
    "Llama-4-Maverick": {"SBS": {"DP": [5, 25], "PD": [0, 30]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Qwen2.5": {"SBS": {"DP": [11, 19], "PD": [5, 25]}, "EOS": {"DP": [27, 3], "PD": [1, 29]}},
}

ALPHA = 0.05
TOTAL_N = 30  # Assuming standard 30 samples. If variable, calculate per mode.

from scipy.stats import fisher_exact
print(f"{'MODEL':<20} | {'STAGE 1 (Both Sig?)':<20} | {'STARKNESS TEST':<20} | {'VERDICT'}")
print("-" * 110)

for model, modes in data.items():
    # --- 1. Extract Counts ---
    eos_dp = modes["EOS"]["DP"][0]
    eos_pd = modes["EOS"]["PD"][0]
    sbs_dp = modes["SBS"]["DP"][0]
    sbs_pd = modes["SBS"]["PD"][0]

    # --- 2. Stage 1: Check internal significance ---
    _, p_eos = fisher_exact([[eos_dp, eos_pd], [eos_pd, eos_dp]])
    _, p_sbs = fisher_exact([[sbs_dp, sbs_pd], [sbs_pd, sbs_dp]])
    is_both_sig = (p_eos < ALPHA) and (p_sbs < ALPHA)
    
    stage1_str = "YES" if is_both_sig else "No"

    if is_both_sig:
        # --- 3. Stage 2: The "Intensity" Test ---
        
        # A. Determine the "Dominant" count for EOS (The bias intensity)
        # If DP > PD, the "Score" is DP count. If PD > DP, "Score" is PD count.
        eos_hits = max(eos_dp, eos_pd)
        eos_misses = TOTAL_N - eos_hits
        
        # B. Determine the "Dominant" count for SBS
        sbs_hits = max(sbs_dp, sbs_pd)
        sbs_misses = TOTAL_N - sbs_hits

        # C. Compare the Intensity (Hit Rate vs Hit Rate)
        # Table: [[EOS_Hits, EOS_Misses], [SBS_Hits, SBS_Misses]]
        table_stark = [
            [eos_hits, eos_misses],
            [sbs_hits, sbs_misses]
        ]
        
        _, p_stark = fisher_exact(table_stark, alternative="two-sided")

        # D. Verdict Logic
        if p_stark < ALPHA:
            diff = abs(eos_hits - sbs_hits)
            direction = "EOS Starker" if eos_hits > sbs_hits else "SBS Starker"
            verdict = f"SIGNIFICANT ({direction})"
            stats_msg = f"p={p_stark:.4f} (Diff: {diff})"
        else:
            diff = abs(eos_hits - sbs_hits)
            verdict = "NOT Significant"
            stats_msg = f"p={p_stark:.4f} (Diff: {diff})"

        print(f"{model:<20} | {stage1_str:<20} | {stats_msg:<20} | {verdict}")

    else:
        print(f"{model:<20} | {stage1_str:<20} | {'--':<20} | N/A")