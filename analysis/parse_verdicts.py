"""Classifies each free-text final verdict as guilty / not guilty with an LLM.

The label (True = guilty) is appended to judgments_run*.json, and a "guilty" field is added to
each entry of verdict_trail_run*.json. Files that are already labeled are skipped.
"""
import argparse
import glob
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from common import all_case_dirs

load_dotenv()

MODEL = "gpt-5.4"
client = OpenAI(api_key=os.getenv("OpenAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a verdict classifier. Given a legal verdict text, first briefly reason about "
    "what verdict is expressed, then on the final line respond with exactly one word: "
    "'guilty' or 'not_guilty'."
)
USER_PROMPT = (
    "What is the verdict in the following text? Reason briefly, then end with exactly "
    "one word on its own line: 'guilty' or 'not_guilty'.\n\n{text}"
)


def classify_verdict(text):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(text=text)},
        ],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip().lower()
    words = re.findall(r"[a-z_]+", raw)
    if words:
        last = words[-1]
        second_last = words[-2] if len(words) >= 2 else ""
        if last == "not_guilty" or (second_last == "not" and last == "guilty"):
            return False
        if last == "guilty":
            return True
    print(f"  WARNING: unexpected response: {repr(raw)}")
    return None


def process_judgments(path):
    with open(path) as f:
        data = json.load(f)
    if not data:
        return f"SKIP (empty) {path}"
    if isinstance(data[-1], bool):
        return f"SKIP {path}"
    verdict_text = data[-1]
    if not isinstance(verdict_text, str):
        return f"SKIP (unexpected type) {path}"

    guilty = classify_verdict(verdict_text)
    data.append(guilty)

    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return f"OK {path} -> {guilty}"


def process_verdict_trail(path):
    with open(path) as f:
        data = json.load(f)
    if all("guilty" in entry for entry in data):
        return f"SKIP {path}"

    for entry in data:
        if "guilty" in entry:
            continue
        verdict_text = entry.get("verdict", "")
        entry["guilty"] = classify_verdict(verdict_text) if verdict_text else None

    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return f"OK {path}"


def collect_files(case_dir, include_interleaved):
    tasks = []
    for out_dir in sorted(glob.glob(os.path.join(case_dir, "outputs*"))):
        if not include_interleaved and "interleaved" in out_dir:
            continue
        for path in sorted(glob.glob(os.path.join(out_dir, "**", "*.json"), recursive=True)):
            basename = os.path.basename(path)
            if basename.startswith("judgments_"):
                tasks.append(("judgments", path))
            elif basename.startswith("verdict_trail_"):
                tasks.append(("verdict_trail", path))
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case_dirs", nargs="+", default=all_case_dirs(),
                        help="Case folders to process (default: every folder in cases/)")
    parser.add_argument("--no-interleaved", action="store_true", help="Skip interleaved output dirs")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    tasks = [t for case_dir in args.case_dirs for t in collect_files(case_dir, not args.no_interleaved)]
    print(f"Found {len(tasks)} files to process")

    def process(task):
        kind, path = task
        try:
            if kind == "judgments":
                return process_judgments(path)
            else:
                return process_verdict_trail(path)
        except Exception as e:
            return f"ERROR {path}: {e}"

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process, t): t for t in tasks}
        with tqdm(total=len(futures)) as pbar:
            for future in as_completed(futures):
                result = future.result()
                if not result.startswith("SKIP"):
                    tqdm.write(result)
                pbar.update(1)


if __name__ == "__main__":
    main()
