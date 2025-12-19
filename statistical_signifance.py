from scipy.stats import fisher_exact

data = {
    "GPT 3.5 Turbo": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [26, 4], "PD": [30, 0]}},
    "GPT 4o": {"SBS": {"DP": [30, 0], "PD": [26, 4]}, "EOS": {"DP": [30, 0], "PD": [6, 24]}},
    "GPT 5": {"SBS": {"DP": [19, 11], "PD": [29, 1]}, "EOS": {"DP": [16, 14], "PD": [30, 0]}},
    "Claude 3 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 7]}},
    "Claude 3.5 Haiku": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [30, 0], "PD": [22, 8]}},
    "Claude 3.7 Sonnet": {"SBS": {"DP": [25, 5], "PD": [30, 0]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Claude 4 Sonnet": {"SBS": {"DP": [28, 2], "PD": [26, 4]}, "EOS": {"DP": [29, 1], "PD": [0, 30]}},
    "Gemini 2.0 Flash": {"SBS": {"DP": [25, 1], "PD": [22, 3]}, "EOS": {"DP": [27, 3], "PD": [14, 16]}},
    "Gemini 2.5 Flash": {"SBS": {"DP": [24, 6], "PD": [25, 4]}, "EOS": {"DP": [27, 3], "PD": [21, 9]}},
     "LLAMA": {"SBS": {"DP": [24, 6], "PD": [28, 2]}, "EOS": {"DP": [26, 4], "PD": [1, 29]}},
    "QWEN": {"SBS": {"DP": [30, 0], "PD": [30, 0]}, "EOS": {"DP": [25, 5], "PD": [21, 9]}}
}

ALPHA = 0.05

print("Fisher’s Exact Test (DP vs PD within each mode)\n")

for model, modes in data.items():
    print(model)

    for mode in ["EOS", "SBS"]:
        dp = modes[mode]["DP"][0]
        pd = modes[mode]["PD"][0]

        table = [[dp, pd],
                 [pd, dp]]

        _, p = fisher_exact(table, alternative="two-sided")
        verdict = "SIGNIFICANT" if p < ALPHA else "not significant"

        print(f"  {mode}: p = {p:.6f} → {verdict}")

    
