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
Together_API_KEY = os.getenv("Together_API_KEY")

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

ELICIT = "**AT THE END OF YOUR RESPONSE**, please output a probability judgment which is an integer between 0 and 100, where 100 denotes certainty. This **MUST** appear at the end of your response!!"


def extract_trailing_int(text):
    if not text:
        return None
    m = re.search(r'(\d+)\D*$', text)
    return m.group(1) if m else None


def init_client(args):
    key = args.api_key
    if "gpt" in args.model or args.model[0] == 'o':
        return OpenAI(api_key=key or OpenAI_API_KEY)
    elif "gemini" in args.model:
        return OpenAI(api_key=key or Gemini_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    elif "claude" in args.model:
        return anthropic.Anthropic(api_key=key or Anthropic_API_KEY)
    else:
        return Together(api_key=key or Together_API_KEY)


def chat_completion(args, client, messages, max_tokens=2000):
    if "claude" in args.model:
        return client.messages.create(
            model=args.model,
            max_tokens=max_tokens,
            temperature=args.temperature,
            messages=messages,
        ).content[0].text
    if args.model == "gpt-5":
        kwargs = {"model": args.model, "input": messages, "temperature": args.temperature}
        if args.direct:
            kwargs["reasoning"] = {"effort": "minimal"}
        return client.responses.create(**kwargs).output_text
    return client.chat.completions.create(
        model=args.model,
        messages=messages,
        temperature=args.temperature,
    ).choices[0].message.content


def ask_for_int(args, client, message_log):
    """Re-queries until the response ends in an integer, logs the response, and returns that integer."""
    response = chat_completion(args, client, message_log)
    num = extract_trailing_int(response)
    while num is None:
        response = chat_completion(args, client, message_log)
        num = extract_trailing_int(response)
    message_log.append({"role": "assistant", "content": response})
    return num


def ask_verdict(args, client, message_log, verdict_question):
    """Answers the P(guilty) question already posed as the last user turn, then asks for a verdict.

    Returns (probability, free-text verdict).
    """
    prob = ask_for_int(args, client, message_log)
    message_log.append({"role": "user", "content": verdict_question})
    verdict = chat_completion(args, client, message_log)
    message_log.append({"role": "assistant", "content": verdict})
    return prob, verdict


def add_common_args(parser):
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="Model name; the provider is inferred from it (gpt/o*, claude, gemini, else Together)")
    parser.add_argument("--num_runs", type=int, default=30,
                        help="Target number of runs; existing runs are kept and the rest are filled in")
    parser.add_argument("--defend_then_prosecute", action="store_true",
                        help="Present defense evidence first (DP); default is prosecution first (PD)")
    parser.add_argument("--direct", action="store_true",
                        help="gpt-5 only: use minimal reasoning effort")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--case_dir", type=str, default=os.path.join(REPO_DIR, "cases", "murder"),
                        help="Folder containing case.yaml; outputs are written here")
    parser.add_argument("--interleave_verdict", action="store_true",
                        help="Also elicit P(guilty) and a verdict after each evidence step")
    parser.add_argument("--api_key", type=str, default=None,
                        help="Overrides the provider key from .env")
    return parser


def run_experiment(args, ask_fn, base_dir_name):
    client = init_client(args)

    if args.interleave_verdict:
        base_dir_name = base_dir_name + "_interleaved"
    condition = "dp" if args.defend_then_prosecute else "pd"
    model_dir = os.path.join(args.case_dir, base_dir_name, condition, args.model)
    os.makedirs(model_dir, exist_ok=True)

    existing_runs = [
        int(re.search(r"run(\d+)\.json", f).group(1))
        for f in os.listdir(model_dir)
        if re.search(r"run(\d+)\.json", f)
    ]
    completed_runs = len(set(existing_runs))
    print(f"➡️ Found {completed_runs} completed runs for {args.model} ({condition.upper()})")

    if completed_runs >= args.num_runs:
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
