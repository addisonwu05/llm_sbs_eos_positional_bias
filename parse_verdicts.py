import json
import os
import glob
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

API_KEYS = [
    os.getenv("OpenAI_API_KEY"),
    os.getenv("OpenAI_API_KEY_2"),
    os.getenv("OpenAI_API_KEY_3"),
    os.getenv("OpenAI_API_KEY_4"),
    os.getenv("OpenAI_API_KEY_5"),
    os.getenv("OpenAI_API_KEY_6"),
]
CLIENTS = [OpenAI(api_key=k) for k in API_KEYS if k]
MODEL = "gpt-5.4"

_client_lock = threading.Lock()
_client_index = 0


def get_client():
    global _client_index
    with _client_lock:
        client = CLIENTS[_client_index % len(CLIENTS)]
        _client_index += 1
        return client


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
    client = get_client()
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


_file_lock = threading.Lock()


def process_judgments(path):
    with _file_lock:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data[-1], bool):
            return f"SKIP {path}"

    if not data:
        return f"SKIP (empty) {path}"
    verdict_text = data[-1]
    if not isinstance(verdict_text, str):
        return f"SKIP (unexpected type) {path}"

    guilty = classify_verdict(verdict_text)
    data.append(guilty)

    with _file_lock:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return f"OK {path} -> {guilty}"


def process_verdict_trail(path):
    with _file_lock:
        with open(path) as f:
            data = json.load(f)
        if all("guilty" in entry for entry in data):
            return f"SKIP {path}"

    for entry in data:
        if "guilty" in entry:
            continue
        verdict_text = entry.get("verdict", "")
        entry["guilty"] = classify_verdict(verdict_text) if verdict_text else None

    with _file_lock:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return f"OK {path}"


def collect_files(case_dir, interleaved_dirs):
    tasks = []
    for out_dir in interleaved_dirs:
        pattern = os.path.join(case_dir, out_dir, "**", "*.json")
        for path in sorted(glob.glob(pattern, recursive=True)):
            basename = os.path.basename(path)
            if basename.startswith("judgments_"):
                tasks.append(("judgments", path))
            elif basename.startswith("verdict_trail_"):
                tasks.append(("verdict_trail", path))
    return tasks


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-interleaved", action="store_true", help="Skip interleaved output dirs")
    args = parser.parse_args()

    case_dir = "cases/murder"
    all_dirs = [
        "outputs",
        "outputs_compress",
        "outputs_eos",
        "outputs_interleaved",
        "outputs_eos_interleaved",
    ]
    interleaved_dirs = [d for d in all_dirs if not args.no_interleaved or "interleaved" not in d]

    tasks = collect_files(case_dir, interleaved_dirs)
    print(f"Found {len(tasks)} files to process ({len(CLIENTS)} API keys)")

    def process(task):
        kind, path = task
        try:
            if kind == "judgments":
                return process_judgments(path)
            else:
                return process_verdict_trail(path)
        except Exception as e:
            return f"ERROR {path}: {e}"

    with ThreadPoolExecutor(max_workers=len(CLIENTS)) as executor:
        futures = {executor.submit(process, t): t for t in tasks}
        with tqdm(total=len(futures)) as pbar:
            for future in as_completed(futures):
                result = future.result()
                if not result.startswith("SKIP"):
                    tqdm.write(result)
                pbar.update(1)


if __name__ == "__main__":
    main()
