"""End-of-Sequence (EoS) response mode: likelihood questions only after all of one side's evidence."""
import argparse
import random
import os
import yaml
from utils import ELICIT, ask_for_int, ask_verdict, add_common_args, run_experiment


def ask_model_judgments(args, client):
    with open(os.path.join(args.case_dir, "case.yaml")) as f:
        case = yaml.safe_load(f)

    message_log, model_judgments, verdict_trail = [], [], []
    message_log.append({"role": "user", "content": case["case_summary"]})

    prosecution_evidence = [b["evidence"] for b in case["prosecution"]["evidence_blocks"]]
    defense_evidence = [b["evidence"] for b in case["defense"]["evidence_blocks"]]

    random.shuffle(prosecution_evidence)
    random.shuffle(defense_evidence)

    sides = [
        (prosecution_evidence, case["prosecution"]["eos_questions"]),
        (defense_evidence, case["defense"]["eos_questions"]),
    ]
    if args.defend_then_prosecute:
        sides.reverse()

    vq1, vq2 = case["verdict_questions"]

    for step, (evidence, questions) in enumerate(sides):
        block = "\n".join(e + "\n" for e in evidence)

        if args.interleave_verdict:
            # Present block + ask verdict in one turn
            message_log.append({"role": "user", "content": block + "\n" + vq1 + "\n" + ELICIT})
            prob, verdict = ask_verdict(args, client, message_log, vq2)
            verdict_trail.append({"step": step, "prob": prob, "verdict": verdict})

        for i, q in enumerate(questions):
            # The block goes with the first question unless it was already shown with the verdict prompt
            prefix = block if i == 0 and not args.interleave_verdict else ""
            message_log.append({"role": "user", "content": prefix + q + "\n" + ELICIT})
            model_judgments.append(ask_for_int(args, client, message_log))

    message_log.append({"role": "user", "content": vq1 + "\n" + ELICIT})
    model_judgments.extend(ask_verdict(args, client, message_log, vq2))

    return message_log, model_judgments, verdict_trail


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    run_experiment(args, ask_model_judgments, "outputs_eos")
