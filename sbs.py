import argparse
import random
import os
import yaml
from utils import extract_trailing_int, chat_completion, add_common_args, run_experiment


def ask_model_judgments(args, client):
    case_path = os.path.join(args.case_dir, "case.yaml")
    with open(case_path) as f:
        case = yaml.safe_load(f)

    message_log, model_judgments, verdict_trail = [], [], []
    message_log.append({"role": "user", "content": case["case_summary"]})

    prosecution_blocks = case["prosecution"]["evidence_blocks"]
    defense_blocks = case["defense"]["evidence_blocks"]

    random.shuffle(prosecution_blocks)
    random.shuffle(defense_blocks)

    if args.defend_then_prosecute:
        first_blocks, second_blocks = defense_blocks, prosecution_blocks
    else:
        first_blocks, second_blocks = prosecution_blocks, defense_blocks

    elicit = "**AT THE END OF YOUR RESPONSE**, please output a probability judgment which is an integer between 0 and 100, where 100 denotes certainty. This **MUST** appear at the end of your response!!"
    vq1, vq2 = case["verdict_questions"]

    step = 0
    block_idx = 0
    block_starts = []
    for blocks in (first_blocks, second_blocks):
        for block in blocks:
            evidence = block["evidence"]
            q1, q2 = block["sbs_questions"]

            if getattr(args, "compress", False) and not args.interleave_verdict and block_idx >= 2:
                start = block_starts[block_idx - 2]
                for msg in message_log[start:start + 4]:
                    if msg["role"] == "assistant":
                        msg["content"] = extract_trailing_int(msg["content"])

            block_starts.append(len(message_log))

            if args.interleave_verdict:
                # Present evidence + ask verdict in one turn
                message_log.append({"role": "user", "content": evidence + "\n" + vq1 + "\n" + elicit})
                resp = chat_completion(args, client, message_log)
                prob = extract_trailing_int(resp)
                while prob is None:
                    resp = chat_completion(args, client, message_log)
                    prob = extract_trailing_int(resp)
                message_log.append({"role": "assistant", "content": resp})

                message_log.append({"role": "user", "content": vq2})
                resp = chat_completion(args, client, message_log)
                verdict_trail.append({"step": step, "prob": prob, "verdict": resp})
                message_log.append({"role": "assistant", "content": resp})
                step += 1

                # Diagnostic questions — evidence already in context, no prefix needed
                message_log.append({"role": "user", "content": q1 + "\n" + elicit})
            else:
                message_log.append({"role": "user", "content": evidence + "\n" + q1 + "\n" + elicit})

            response = chat_completion(args, client, message_log)
            num = extract_trailing_int(response)
            while num is None:
                response = chat_completion(args, client, message_log)
                num = extract_trailing_int(response)
            model_judgments.append(num)
            message_log.append({"role": "assistant", "content": response})

            message_log.append({"role": "user", "content": q2 + "\n" + elicit})
            response = chat_completion(args, client, message_log)
            num = extract_trailing_int(response)
            while num is None:
                response = chat_completion(args, client, message_log)
                num = extract_trailing_int(response)
            model_judgments.append(num)
            message_log.append({"role": "assistant", "content": response})
            block_idx += 1

    message_log.append({"role": "user", "content": vq1 + "\n" + elicit})
    response = chat_completion(args, client, message_log)
    num = extract_trailing_int(response)
    while num is None:
        response = chat_completion(args, client, message_log)
        num = extract_trailing_int(response)
    model_judgments.append(num)
    message_log.append({"role": "assistant", "content": response})

    message_log.append({"role": "user", "content": vq2})
    response = chat_completion(args, client, message_log)
    model_judgments.append(response)
    message_log.append({"role": "assistant", "content": response})

    return message_log, model_judgments, verdict_trail


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--compress", action="store_true")
    args = parser.parse_args()
    base_dir = "outputs_compress" if args.compress else "outputs"
    run_experiment(args, ask_model_judgments, base_dir)
