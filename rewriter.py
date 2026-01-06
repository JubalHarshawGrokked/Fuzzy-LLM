import os
from openai import OpenAI
from prompts import REWRITER_PROMPT,REASONING_DECIDER_PROMPT
from pydantic import BaseModel
from typing import Literal

class ReasoningModeOutput(BaseModel):
    reasoning_mode: Literal["crisp", "fuzzy","no"]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def rewrite_text(user_text: str) -> str:
    """
    Rewrites arbitrary user input text into clearer, more precise natural language.
    This is Step (1) of the Logic-LLM pipeline.
    """

    system_prompt = REWRITER_PROMPT

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ] ,
        temperature=0.3)

    return response.choices[0].message.content.strip()



def decide_reasoning_mode(clean_context: str, clean_question: str) -> str:
    """
    Decide whether to use crisp or fuzzy logic or if they aren't required return 'no'.
    Uses structured output to guarantee valid results.
    """

    system_prompt = REASONING_DECIDER_PROMPT

    user_content = (
        "Context:\n"
        f"{clean_context}\n\n"
        "Question:\n"
        f"{clean_question}\n"
        "Return only one of of three: 'crisp', 'fuzzy' or 'no'; return only those string! nothing additional!"
    )


    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        text_format=ReasoningModeOutput,
        temperature=0.65
    )

    return response.output_parsed.reasoning_mode
