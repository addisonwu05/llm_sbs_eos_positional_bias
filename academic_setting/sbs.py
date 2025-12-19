import argparse
import random
import os
import re
import json
from openai import OpenAI
from together import Together
import anthropic
from dotenv import load_dotenv

# this is for sbs


# argumetns you want to add

# you want to add an argument store_true that does if it is DP then or PD (boolean store_true)

# two different sbs folders

# save two jsons per run: transcript, and judgments

# and just gpt the main

load_dotenv()
OpenAI_API_KEY = os.getenv("OpenAI_API_KEY")
Anthropic_API_KEY = os.getenv("Anthropic_API_KEY")
Gemini_API_KEY = os.getenv("Gemini_API_KEY")
Together_API_KEY = os.getenv("Together_API_KEY")
def is_integer(text):
    if not isinstance(text, str):
        return False
        
    try:
        int(text)
        return True
    except ValueError:
        return False

def init_client(args):
    if "gpt" in args.model or args.model[0] == 'o':
        return OpenAI(api_key=OpenAI_API_KEY)
    elif "gemini" in args.model:
        return OpenAI(api_key=Gemini_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    elif "claude" in args.model:
        return anthropic.Anthropic(api_key=Anthropic_API_KEY)
    else:
        return Together(api_key=Together_API_KEY)
    
def chat_completion(args, client, messages, max_tokens=500, temperature=1):
    if args.alter_temperature:
        temperature = args.temperature
    if "claude" in args.model:
        kwargs = {
            "model": args.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        return client.messages.create(**kwargs).content[0].text
    
    else:
        # OpenAI and Together APIs (assumes OpenAI-style client)
        if args.model == "gpt-5":
            if args.direct:
                return client.responses.create(
                    model=args.model,
                    input=messages,
                    temperature=temperature,
                    reasoning={
                        "effort": "minimal"
                    }
                ).output_text
            else:
                return client.responses.create(
                    model=args.model,
                    input=messages,
                    temperature=temperature
                ).output_text

        return client.chat.completions.create(
            model=args.model,
            messages=messages,
            temperature=temperature
        ).choices[0].message.content

def ask_model_judgments(args, client):

    NUM_PIECES_OF_EVIDENCE = 4

    message_log, model_judgments = [], []

    with open("case_summary.txt", "r") as file:
        case_summary = file.read()
    message_log.append({"role": "user", "content": case_summary})
    
    defendant_evidence, prosecution_evidence = [], []

    defendant_questions, prosecution_questions = [], [] #each array is of len 4, each element is a tuple of the 2 questions

    for i in range(1,NUM_PIECES_OF_EVIDENCE+1,1):
        with open(f"sbs_defense_evidence_{i}.txt", "r") as file:
            defense_evidence = file.read()
        defendant_evidence.append(defense_evidence)
        with open(f"sbs_prosecution_evidence_{i}.txt", "r") as file:
            prosecutor_evidence = file.read()
        prosecution_evidence.append(prosecutor_evidence)
        with open(f"sbs_defense_qs_{i}1.txt", "r") as file:
            defense_questions1 = file.read()
        with open(f"sbs_defense_qs_{i}2.txt", "r") as file:
            defense_questions2 = file.read()
        defendant_questions.append((defense_questions1,defense_questions2))
        with open(f"sbs_prosecution_qs_{i}1.txt", "r") as file:
            prosecution_questions1 = file.read()
        with open(f"sbs_prosecution_qs_{i}2.txt", "r") as file:
            prosecution_questions2 = file.read()
        prosecution_questions.append((prosecution_questions1,prosecution_questions2))
    
    prosecution_pairs = list(zip(prosecution_evidence, prosecution_questions))
    defendant_pairs = list(zip(defendant_evidence, defendant_questions))

    random.shuffle(prosecution_pairs)
    random.shuffle(defendant_pairs)


    prosecution_evidence, prosecution_questions = zip(*prosecution_pairs)
    defendant_evidence, defendant_questions = zip(*defendant_pairs)

    prosecution_evidence = list(prosecution_evidence)
    prosecution_questions = list(prosecution_questions)
    defendant_evidence = list(defendant_evidence)
    defendant_questions = list(defendant_questions)
    

    # make sure to do the shuffles pair the defendant evidence with defendant quesitons, same thing with the prosecution

     # don't do a random choice, have it controlled by an argument

    if args.defend_then_prosecute:
        first_set_of_evidence=defendant_evidence
        first_set_of_questions=defendant_questions
        second_set_of_evidence=prosecution_evidence
        second_set_of_questions=prosecution_questions

    else:
        first_set_of_evidence=prosecution_evidence
        first_set_of_questions=prosecution_questions
        second_set_of_evidence=defendant_evidence
        second_set_of_questions=defendant_questions


    with open("verdict_q_1.txt", "r") as file:
            final_question1 = file.read()
    with open("verdict_q_2.txt", "r") as file:
            final_question2 = file.read()

    elicit_probability = "**AT THE END OF YOUR RESPONSE**, please output a probability judgment which is an integer between 0 and 100, where 100 denotes certainty. This **MUST** appear at the end of your response!!"

    # for loop for first set
    for idx in range(NUM_PIECES_OF_EVIDENCE):
        # append the evidence and the first question
        message_log.append({"role": "user", "content": first_set_of_evidence[idx] + "\n" + first_set_of_questions[idx][0] + "\n" + elicit_probability})
        # get the initial response
        model_response = chat_completion(args, client, message_log)
        print(model_response)
        while(is_integer(model_response.split()[-1])==False):
            model_response = chat_completion(args, client, message_log)
            print(model_response)
        model_judgments.append(model_response.split()[-1])
        message_log.append({"role": "assistant", "content": model_response})

        # now do the next quesiton
        message_log.append({"role": "user", "content": first_set_of_questions[idx][1] + "\n" + elicit_probability})
        # and get the model's response
        model_response = chat_completion(args, client, message_log)
        while(is_integer(model_response.split()[-1])==False):
            model_response = chat_completion(args, client, message_log)
            print(model_response)
        model_judgments.append(model_response.split()[-1])
        message_log.append({"role": "assistant", "content": model_response})

    # for loop for second set
    for idx in range(NUM_PIECES_OF_EVIDENCE):
        # append the evidence and the first question
        message_log.append({"role": "user", "content": second_set_of_evidence[idx] + "\n" + second_set_of_questions[idx][0] + "\n" + elicit_probability})
        # get the initial response
        model_response = chat_completion(args, client, message_log)
        while(is_integer(model_response.split()[-1])==False):
            model_response = chat_completion(args, client, message_log)
            print(model_response)
        model_judgments.append(model_response.split()[-1])
        message_log.append({"role": "assistant", "content": model_response})
    
        # now do the next question
        message_log.append({"role": "user", "content": second_set_of_questions[idx][1] + "\n" + elicit_probability})
        # and get the model's response
        model_response = chat_completion(args, client, message_log)
        while(is_integer(model_response.split()[-1])==False):
            model_response = chat_completion(args, client, message_log)
            print(model_response)
        model_judgments.append(model_response.split()[-1])
        message_log.append({"role": "assistant", "content": model_response})

    message_log.append({"role": "user", "content":final_question1 + "\n" + elicit_probability})
    model_response = chat_completion(args, client, message_log)
    while(is_integer(model_response.split()[-1])==False):
        model_response = chat_completion(args, client, message_log)
    model_judgments.append(model_response.split()[-1])
    message_log.append({"role": "assistant", "content": model_response})
    message_log.append({"role": "user", "content":final_question2})
    model_response = chat_completion(args, client, message_log)
    model_judgments.append(model_response)
    message_log.append({"role": "assistant", "content": model_response})


    return message_log, model_judgments


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--num_runs", type=int, default=30)
    parser.add_argument("--defend_then_prosecute", action="store_true")
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--alter_temperature", action="store_true")
    return parser.parse_args()

def main(args):
    # initialize API client
    client = init_client(args)

    # create the base outputs directory
    base_dir = "outputs"
    os.makedirs(base_dir, exist_ok=True)

    # create subfolder for DP or PD condition
    condition = "dp" if args.defend_then_prosecute else "pd"
    condition_dir = os.path.join(base_dir, condition)
    os.makedirs(condition_dir, exist_ok=True)

    # create subfolder for model name
    model_dir = os.path.join(condition_dir, args.model)
    os.makedirs(model_dir, exist_ok=True)

    # --- detect existing completed runs ---
    existing_runs = [
        int(re.search(r"run(\d+)\.json", f).group(1))
        for f in os.listdir(model_dir)
        if re.search(r"run(\d+)\.json", f)
    ]
    completed_runs = len(set(existing_runs))  # unique run indices
    print(f"➡️ Found {completed_runs} completed runs for {args.model} ({condition.upper()})")

    # --- skip if already 30 or more ---
    if completed_runs >= 30:
        print(f"⏭️  Skipping {args.model} ({condition.upper()}) — already has {completed_runs} runs.")
        return

    start_run = max(existing_runs) + 1 if existing_runs else 1
    remaining_runs = args.num_runs - completed_runs
    print(f"▶️  Resuming from run {start_run} ({remaining_runs} remaining)")

    # --- main loop ---
    for run_idx in range(start_run, start_run + remaining_runs):
        print(f"Running {args.model} — {condition.upper()} (run {run_idx})")

        message_log, model_judgments = ask_model_judgments(args, client)

        # filenames
        transcript_path = os.path.join(model_dir, f"transcript_run{run_idx}.json")
        judgments_path = os.path.join(model_dir, f"judgments_run{run_idx}.json")

        # save the results
        with open(transcript_path, "w") as f:
            json.dump(message_log, f, indent=2, ensure_ascii=False)

        with open(judgments_path, "w") as f:
            json.dump(model_judgments, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {transcript_path} and {judgments_path}")





if __name__ == "__main__":
    args = parse_args()
    main(args)