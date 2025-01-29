import logging
from enum import StrEnum
from typing import BinaryIO, Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from config.settings import CommonSettings

token = CommonSettings().OPENAI_API_KEY


class Model(StrEnum):
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"
    o1_mini = "o1-mini"
    o1_preview = "o1-preview"


def get_client():
    return OpenAI(
        api_key=token,
        organization="org-ivGGIRGxUk5rZmvxkoypdUUy",
        project="proj_t7kgt6Awz7m2knmH4gL0xeh2"
    )


def get_english_teacher_comment(content: str, model: str = "gpt-4o-mini") -> ChatCompletionMessage:
    prompt = """You are a helpful english teacher. 
    Please help to improve grammar, vocabulary and naturalness of this speech"""
    developer_message = {"role": "system", "content": prompt}
    return generate(content, model, developer_message)


def generate(
        content: str,
        model: str = "gpt-4o-mini",
        developer_message: Optional[Dict] = None,
        n: int = 1) -> ChatCompletionMessage:
    messages = [
        {"role": "user", "content": f"{content}"}
    ]
    if developer_message:
        messages.append(developer_message)
    completion = get_client().chat.completions.create(
        model=model,
        store=True,
        messages=messages,
        n=n
    )
    logging.info(f"Запрос к {completion.model} использовал {completion.usage.total_tokens} токенов")
    return completion.choices[0].message


def transcript_by_gpt(temperature, system_prompt, audio_file):
    completion = get_client().chat.completions.create(
        model="gpt-4o",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcribe(audio_file, "")
            }
        ]
    )
    return completion.choices[0].message.content


def transcript_by_whisper(audio_file: BinaryIO):
    transcription = get_client().audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcription


def text_answer_to_audio():
    pass
