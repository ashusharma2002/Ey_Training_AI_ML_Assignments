import os
from dotenv import load_dotenv

import promptlayer

load_dotenv()

PROMPTLAYER_API_KEY = os.getenv(
    "PROMPTLAYER_API_KEY"
)

if not PROMPTLAYER_API_KEY:
    raise ValueError(
        "PROMPTLAYER_API_KEY not found in .env"
    )

promptlayer.api_key = PROMPTLAYER_API_KEY


def log_prompt(
    prompt_name,
    prompt_text,
    response_text
):
    """
    Logs prompt and response to PromptLayer
    """

    try:

        promptlayer.track.prompt(
            prompt_name=prompt_name,
            prompt_input_variables={
                "prompt": prompt_text
            },
            tags=["day11", "genai"],
            metadata={
                "response": response_text
            }
        )

        print(
            f"PromptLayer Log Success: {prompt_name}"
        )

    except Exception as e:

        print(
            f"PromptLayer Logging Failed: {e}"
        )