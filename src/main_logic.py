from rewriter import rewrite_text, decide_reasoning_mode
from decider import inference
from openai import OpenAI
from prompts import FINAL_PROMPT
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Step 0: Get user input ----
raw_context = input("Please give the context, describe facts: ")
raw_question = input("Please give the query in natural language: ")

# ---- Step 1: Rewrite text ----
clean_context = rewrite_text(raw_context)
clean_question = rewrite_text(raw_question)

# ---- Step 2: Decide reasoning mode ----
mode = decide_reasoning_mode(clean_context, clean_question)
print(f"[INFO] Reasoning mode: {mode}")

# ---- Step 3: Do Inference  ----
program_result = inference(mode, clean_question, clean_context)
print(f"[INFO] Tool execution result: {program_result}")

# ---- Step 4: Summarize results in natural language ----
user_text = (
    f"We did inference from the context:\n{clean_context}\n"
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
