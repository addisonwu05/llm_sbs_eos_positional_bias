"""Step-by-Step (SbS) response mode: likelihood questions after each individual piece of evidence."""
import argparse
import random
import os
import yaml
from utils import ELICIT, extract_trailing_int, ask_for_int, ask_verdict, add_common_args, run_experiment


def ask_model_judgments(args, client):
    with open(os.path.join(args.case_dir, "case.yaml")) as f:
        case = yaml.safe_load(f)

    message_log, model_judgments, verdict_trail = [], [], []
    message_log.append({"role": "user", "content": case["case_summary"]})

    prosecution_blocks = case["prosecution"]["evidence_blocks"]
    defense_blocks = case["defense"]["evidence_blocks"]

    random.shuffle(prosecution_blocks)
    random.shuffle(defense_blocks)

    if args.defend_then_prosecute:
        blocks = defense_blocks + prosecution_blocks
    else:
        blocks = prosecution_blocks + defense_blocks

    vq1, vq2 = case["verdict_questions"]

    block_starts = []
    for block_idx, block in enumerate(blocks):
        evidence = block["evidence"]
        q1, q2 = block["sbs_questions"]

        # Compressed ablation: once a block is two blocks old, replace its answers with their numeric score
        if args.compress and not args.interleave_verdict and block_idx >= 2:
            start = block_starts[block_idx - 2]
            for msg in message_log[start:start + 4]:
                if msg["role"] == "assistant":
                    msg["content"] = extract_trailing_int(msg["content"])

        block_starts.append(len(message_log))

        if args.interleave_verdict:
            # Present evidence + ask verdict in one turn
            message_log.append({"role": "user", "content": evidence + "\n" + vq1 + "\n" + ELICIT})
            prob, verdict = ask_verdict(args, client, message_log, vq2)
            verdict_trail.append({"step": block_idx, "prob": prob, "verdict": verdict})

            # Diagnostic questions — evidence already in context, no prefix needed
            message_log.append({"role": "user", "content": q1 + "\n" + ELICIT})
        else:
            message_log.append({"role": "user", "content": evidence + "\n" + q1 + "\n" + ELICIT})
        model_judgments.append(ask_for_int(args, client, message_log))

        message_log.append({"role": "user", "content": q2 + "\n" + ELICIT})
        model_judgments.append(ask_for_int(args, client, message_log))

    message_log.append({"role": "user", "content": vq1 + "\n" + ELICIT})
    model_judgments.extend(ask_verdict(args, client, message_log, vq2))

    return message_log, model_judgments, verdict_trail


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--compress", action="store_true",
                        help="SbS-Compressed ablation: answers older than two blocks are replaced by their numeric score")
    args = parser.parse_args()
    base_dir = "outputs_compress" if args.compress else "outputs"
    run_experiment(args, ask_model_judgments, base_dir)
