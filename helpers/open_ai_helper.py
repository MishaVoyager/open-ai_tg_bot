from enum import StrEnum

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from config.settings import CommonSettings

token = CommonSettings().OPENAI_API_KEY


class Model(StrEnum):
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"
    gpt_o1 = "gpt-o1"
    gpt_o1_mini = "gpt-o1-mini"


def get_client():
    return OpenAI(
        api_key=token,
        organization="org-ivGGIRGxUk5rZmvxkoypdUUy",
        project="proj_t7kgt6Awz7m2knmH4gL0xeh2"
    )


def generate(content: str, model: str = "gpt-4o-mini", n: int = 1) -> ChatCompletionMessage:
    completion = get_client().chat.completions.create(
        model=model,
        store=True,
        messages=[
            {"role": "user", "content": f"{content}"}
        ],
        n=n
    )
    return completion.choices[0].message
