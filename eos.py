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

    prosecution_evidence = [b["evidence"] for b in case["prosecution"]["evidence_blocks"]]
    defense_evidence = [b["evidence"] for b in case["defense"]["evidence_blocks"]]
    prosecution_eos_qs = case["prosecution"]["eos_questions"]
    defense_eos_qs = case["defense"]["eos_questions"]

    random.shuffle(prosecution_evidence)
    random.shuffle(defense_evidence)

    if args.defend_then_prosecute:
        first_evidence, first_qs = defense_evidence, defense_eos_qs
        second_evidence, second_qs = prosecution_evidence, prosecution_eos_qs
    else:
        first_evidence, first_qs = prosecution_evidence, prosecution_eos_qs
        second_evidence, second_qs = defense_evidence, defense_eos_qs

    first_block = "\n".join(e + "\n" for e in first_evidence)
    second_block = "\n".join(e + "\n" for e in second_evidence)

    vq1, vq2 = case["verdict_questions"]
    elicit = "**AT THE END OF YOUR RESPONSE**, please output a probability judgment which is an integer between 0 and 100, where 100 denotes certainty. This **MUST** appear at the end of your response!!"

    step = 0
    for block, questions in [(first_block, first_qs), (second_block, second_qs)]:
        if args.interleave_verdict:
            # Present block + ask verdict in one turn
            message_log.append({"role": "user", "content": block + "\n" + vq1 + "\n" + elicit})
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

            # EoS diagnostic questions — block already in context, no prefix needed
            for q in questions:
                message_log.append({"role": "user", "content": q + "\n" + elicit})
                response = chat_completion(args, client, message_log)
                num = extract_trailing_int(response)
                while num is None:
                    response = chat_completion(args, client, message_log)
                    num = extract_trailing_int(response)
                model_judgments.append(num)
                message_log.append({"role": "assistant", "content": response})
        else:
            for i, q in enumerate(questions):
                prefix = block if i == 0 else ""
                message_log.append({"role": "user", "content": prefix + q + "\n" + elicit})
                response = chat_completion(args, client, message_log)
                num = extract_trailing_int(response)
                while num is None:
                    response = chat_completion(args, client, message_log)
                    num = extract_trailing_int(response)
                model_judgments.append(num)
                message_log.append({"role": "assistant", "content": response})

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
    args = parser.parse_args()
    run_experiment(args, ask_model_judgments, "outputs_eos")
