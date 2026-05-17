import random
defendant_evidence, prosecution_evidence = [], []

defendant_questions, prosecution_questions = [], [] #each array is of len 4, each element is a tuple of the 2 questions

for i in range(1,5,1):
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
array= [q[0] for q in prosecution_questions]
print(array)
