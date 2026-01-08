from rewriter import rewrite_text, decide_reasoning_mode
from decider import inference
from openai import OpenAI
from prompts import FINAL_PROMPT
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Step 0: Get user input ----
# raw_context = input("Please give the context, describe facts: ")
# raw_question = input("Please give the query in natural language: ")

raw_context = """John is fast with degree of 0.7, John is tall with degree of 0.6. Person is strong if he is tall or fast with degree of 0.55."""
raw_question = "Who is strong?"

raw_context= "Dimitri is Student, Giorgi is Student!"
raw_question="Who is student?"

# ---- Step 1: Rewrite text ----
clean_context = rewrite_text(raw_context)
clean_question = rewrite_text(raw_question)

# ---- Step 2: Decide reasoning mode ----
mode = decide_reasoning_mode(clean_context, clean_question)
print(f"[INFO] Reasoning mode: {mode}")

# ---- Step 3: Generate logic code and execute ----
program_result = inference(mode, clean_question, clean_context)
print(f"[INFO] Tool execution result: {program_result}")

# ---- Step 4: Summarize results in natural language ----
user_text = (
    f"We generated a program from the context:\n{clean_context}\n"
    f"and the question:\n{clean_question}\n"
    f"Reasoning mode used was \n{mode}\n"
    f"The tool returned the following result:\n{program_result}\n"
    f"Please summarize it in clear natural language for the user."
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": FINAL_PROMPT},
        {"role": "user", "content": user_text}
    ],
    temperature=0.7
)

# ---- Step 5: Print final natural-language answer ----
final_summary = response.choices[0].message.content.strip()
print("\n=== FINAL SUMMARY ===")
print(final_summary)
