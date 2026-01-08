import os
from openai import OpenAI
import json
from engine_tools import TOOL_DEFINITIONS,run_crisp_prolog,run_fuzzy_simpful
from prompts import CRISP_PROLOG_GENERATOR_PROMPT, NO_LOGIC_PROMPT,FUZZY_SIMPFUL_GENERATOR_PROMPT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_RETRIES = 3

def inference(reasoning_mode,clean_question,clean_context):
    system_prompt = NO_LOGIC_PROMPT

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




    if reasoning_mode=='fuzzy':

        system_prompt = FUZZY_SIMPFUL_GENERATOR_PROMPT

        user_content = (
        "Context:\n"
        f"{clean_context}\n\n"
        "Question:\n"
        f"{clean_question}\n"
        "Return clean SIMPFUL code that will answer this question using fuzzy inference!"
    )


        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7
        )
        code = response.choices[0].message.content.strip()
        print("RUNNING FUZZY CODE!!\n",code)
        result=run_fuzzy_simpful(code)

        return result
  # TODO: add retry loop here as well above      
    
    else:
        system_prompt=CRISP_PROLOG_GENERATOR_PROMPT

    messages=[{"role": "system", "content": system_prompt},
            {"role": "user", "content":f"Context: {clean_context}\nQuestion: {clean_question}\n Reasoning Mode: {reasoning_mode}, if reasoning mode is crisp, call crisp_prolog tool, but by all means call tool!"}
            ]
    # print(len(TOOL_DEFINITIONS1), "MY LEEENGTH!")
    for attempt in range(1, MAX_RETRIES + 1):

        print(f"\n=== LOGIC GENERATION ATTEMPT {attempt} ===")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.6
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
            if name == "run_crisp_prolog":
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
                "The generated  program failed at runtime.\n\n"
                f"Error:\n{result['message']}\n\n"
                "You must fix the program\n"
                "Ensure:\n"
                "- Use correct fuzzy or crisp syntax\n"
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
            print("TOOL CALL NOT USED!")
            return msg.content

    # -------------------------
    # Hard fallback
    # -------------------------
    return {
        "error": "max_retries_exceeded",
        "message": "Failed to generate valid Prolog after multiple attempts."
    }

            # ---- Tool calls ----
   