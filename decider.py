import os
from openai import OpenAI
import json
from engine_tools import TOOL_DEFINITIONS,run_crisp_prolog,run_fuzzy_prolog
from prompts import GENERATOR_PROMPT, NO_LOGIC_PROMPT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_RETRIES = 3

def inference(reasoning_mode,clean_question,clean_context):
    system_prompt = GENERATOR_PROMPT

    if reasoning_mode=='no':

        user_helper=(
    
            f"The question is:\n{clean_question}\n"
            f"The context is:\n{clean_context}\n"
            f"Please summarize and solve it in textual manner and return the answer"
            )
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": NO_LOGIC_PROMPT},
                    {"role": "user", "content": user_helper}
                ],
                temperature=0.8
            )
        final_summary = response.choices[0].message.content.strip()
        return final_summary
        

    messages=[{"role": "system", "content": system_prompt},
            {"role": "user", "content":f"Context: {clean_context}\nQuestion: {clean_question}\n Reasoning Mode: {reasoning_mode}"}
            ]

    for attempt in range(1, MAX_RETRIES + 1):

        print(f"\n=== LOGIC GENERATION ATTEMPT {attempt} ===")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.4
        )

        msg = response.choices[0].message

        # -------------------------
        # Tool call
        # -------------------------
        if msg.tool_calls:
            call = msg.tool_calls[0]
            name = call.function.name
            args = json.loads(call.function.arguments)

            print(f"Calling tool: {name}")
            print("Args:", args)

            if name == "run_fuzzy_prolog":
                result = run_fuzzy_prolog(**args)
            elif name == "run_crisp_prolog":
                result = run_crisp_prolog(**args)
            else:
                return {
                    "error": "unknown_tool",
                    "message": name
                }

            # -------------------------
            # SUCCESS
            # -------------------------
            if "error" not in result:
                print("Execution successful.")
                return result

            # -------------------------
            # FAILURE -> feedback to LLM
            # -------------------------
            error_feedback = (
                "The generated Prolog program failed at runtime.\n\n"
                f"Error:\n{result['message']}\n\n"
                "You must fix the program and query.\n"
                "Ensure:\n"
                "- All predicates used in the query are defined\n"
                "- Predicate arities match\n"
                "- Use correct fuzzy or crisp syntax\n"
                "- If logic is not applicable, return NoLogic"
            )

            messages.append({
                "role": "assistant",
                "content": msg.content or ""
            })
            messages.append({
                "role": "user",
                "content": error_feedback
            })

        else:
            # LLM didn't call a tool
            return msg.content

    # -------------------------
    # Hard fallback
    # -------------------------
    return {
        "error": "max_retries_exceeded",
        "message": "Failed to generate valid Prolog after multiple attempts."
    }

            # ---- Tool calls ----
   