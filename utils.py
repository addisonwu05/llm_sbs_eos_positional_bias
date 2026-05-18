import os
import re
import json
from openai import OpenAI
from together import Together
import anthropic
from dotenv import load_dotenv

load_dotenv()
OpenAI_API_KEY = os.getenv("OpenAI_API_KEY")
Anthropic_API_KEY = os.getenv("Anthropic_API_KEY")
Gemini_API_KEY = os.getenv("Gemini_API_KEY")
Together_API_KEY_Llama = os.getenv("Together_API_KEY_Llama")
Together_API_KEY_Qwen = os.getenv("Together_API_KEY_Qwen")


def is_integer(text):
    if not isinstance(text, str):
        return False
    try:
        int(text)
        return True
    except ValueError:
        return False


def extract_trailing_int(text):
    if not text:
        return None
    m = re.search(r'(\d+)\D*$', text)
    return m.group(1) if m else None


def init_client(args):
    key = getattr(args, 'api_key', None) or None
    if "gpt" in args.model or args.model[0] == 'o':
        return OpenAI(api_key=key or OpenAI_API_KEY)
    elif "gemini" in args.model:
        return OpenAI(api_key=key or Gemini_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    elif "claude" in args.model:
        return anthropic.Anthropic(api_key=key or Anthropic_API_KEY)
    elif "qwen" in args.model.lower():
        return Together(api_key=key or Together_API_KEY_Qwen)
    else:
        return Together(api_key=key or Together_API_KEY_Llama)


def chat_completion(args, client, messages, max_tokens=2000, temperature=1):
    if args.alter_temperature:
        temperature = args.temperature
    if "claude" in args.model:
        return client.messages.create(
            model=args.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        ).content[0].text
    if args.model == "gpt-5":
        kwargs = {"model": args.model, "input": messages, "temperature": temperature}
        if args.direct:
            kwargs["reasoning"] = {"effort": "minimal"}
        return client.responses.create(**kwargs).output_text
    return client.chat.completions.create(
        model=args.model,
        messages=messages,
        temperature=temperature,
    ).choices[0].message.content


def add_common_args(parser):
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--num_runs", type=int, default=30)
    parser.add_argument("--defend_then_prosecute", action="store_true")
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--alter_temperature", action="store_true")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--case_dir", type=str, default=".")
    parser.add_argument("--interleave_verdict", action="store_true")
    parser.add_argument("--api_key", type=str, default=None)
    return parser


def run_experiment(args, ask_fn, base_dir_name):
    client = init_client(args)

    if getattr(args, "interleave_verdict", False):
        base_dir_name = base_dir_name + "_interleaved"
    base_dir = os.path.join(args.case_dir, base_dir_name)
    os.makedirs(base_dir, exist_ok=True)

    condition = "dp" if args.defend_then_prosecute else "pd"
    condition_dir = os.path.join(base_dir, condition)
    os.makedirs(condition_dir, exist_ok=True)

    stripped = re.sub(r'^cocoscilab/', '', args.model)
    if stripped != args.model:  # was a cocoscilab model — also strip the trailing hash
        stripped = re.sub(r'-[0-9a-f]{8}$', '', stripped)
    model_dir_name = stripped
    model_dir = os.path.join(condition_dir, model_dir_name)
    os.makedirs(model_dir, exist_ok=True)

    existing_runs = [
        int(re.search(r"run(\d+)\.json", f).group(1))
        for f in os.listdir(model_dir)
        if re.search(r"run(\d+)\.json", f)
    ]
    completed_runs = len(set(existing_runs))
    print(f"➡️ Found {completed_runs} completed runs for {args.model} ({condition.upper()})")

    if completed_runs >= 30:
        print(f"⏭️  Skipping {args.model} ({condition.upper()}) — already has {completed_runs} runs.")
        return

    start_run = max(existing_runs) + 1 if existing_runs else 1
    remaining_runs = args.num_runs - completed_runs
    print(f"▶️  Resuming from run {start_run} ({remaining_runs} remaining)")

    for run_idx in range(start_run, start_run + remaining_runs):
        print(f"Running {args.model} — {condition.upper()} (run {run_idx})")

        message_log, model_judgments, verdict_trail = ask_fn(args, client)

        transcript_path = os.path.join(model_dir, f"transcript_run{run_idx}.json")
        judgments_path = os.path.join(model_dir, f"judgments_run{run_idx}.json")

        with open(transcript_path, "w") as f:
            json.dump(message_log, f, indent=2, ensure_ascii=False)
        with open(judgments_path, "w") as f:
            json.dump(model_judgments, f, indent=2, ensure_ascii=False)

        if verdict_trail:
            verdict_trail_path = os.path.join(model_dir, f"verdict_trail_run{run_idx}.json")
            with open(verdict_trail_path, "w") as f:
                json.dump(verdict_trail, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {transcript_path}, {judgments_path}, and {verdict_trail_path}")
        else:
            print(f"✅ Saved {transcript_path} and {judgments_path}")
