import json
import re
import os

# ---- helper: extract integer from a string ----
def extract_number(text):
    nums = re.findall(r"\b\d+\b", text)
    return int(nums[-1]) if nums else None

# ---- helper: extract nums from a transcript list ----
def parse_transcript(transcript):
    nums = []
    for item in transcript:
        if item.get("role") == "assistant":
            n = extract_number(item.get("content", ""))
            nums.append(n)
    return nums

# ---- main: load transcript_run{1..30}.json ----
def load_all_transcripts(base_path="."):
    results = {}

    for i in range(1, 31):
        filename = f"transcript_run{i}.json"
        path = os.path.join(base_path, filename)

        if not os.path.exists(path):
            print(f"⚠️ File not found: {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            transcript = json.load(f)

        results[i] = parse_transcript(transcript)

    return results


# ---- run it ----
all_numbers = load_all_transcripts("/Users/addisonwu/Desktop/llm_sbs_eos_positional_bias/outputs_eos/dp/gpt-4o")

print(all_numbers)
