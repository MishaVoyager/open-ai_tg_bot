import logging
from enum import StrEnum
from typing import BinaryIO, Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from config.settings import CommonSettings

token = CommonSettings().OPENAI_API_KEY


def generate_text(
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
        messages=messages,  # type: ignore
        n=n
    )
    logging.info(f"Запрос к {completion.model} использовал {completion.usage.total_tokens} токенов")
    return completion.choices[0].message


def audio_to_text(audio_file: BinaryIO) -> str:
    transcription = get_client().audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcription


def text_to_audio(text: str, response_format: str = "mp3") -> BinaryIO:
    response = get_client().audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format=response_format  # type: ignore
    )
    return response.read()  # type: ignore


def generate_image(prompt: str, model: str = "dall-e-3", size: str = "1792x1024") -> Optional[str]:
    response = get_client().images.generate(
        model=model,
        prompt=prompt,
        size=size,  # type: ignore
        quality="standard",
        n=1,
        response_format="b64_json",
        style="vivid"
    )
    return response.data[0].b64_json


def get_answer_from_friend(content: str, model: str = "gpt-4o-mini") -> ChatCompletionMessage:
    prompt = """You are an american man. We are friends. We are in a friendly dialogue."""
    developer_message = {"role": "system", "content": prompt}
    return generate_text(content, model, developer_message)


def get_english_teacher_comment(content: str, model: str = "gpt-4o-mini") -> ChatCompletionMessage:
    prompt = """You are a helpful english teacher. 
    Please help to improve grammar, vocabulary and naturalness of this speech.
    Make verbose comment about errors in this areas.
    """
    developer_message = {"role": "system", "content": prompt}
    return generate_text(content, model, developer_message)


def improve_transcript_by_gpt(transcript: str) -> str:
    system_prompt = """
    You are a helpful assistant. Your task is to correct any spelling discrepancies in the transcribed text.
    Only add necessary punctuation such as periods, commas, and capitalization, and use only the context provided.
    """

    completion = get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcript
            }
        ]
    )
    return completion.choices[0].message.content


class GPTModel(StrEnum):
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"
    o1_mini = "o1-mini"
    o1_preview = "o1-preview"


def get_client() -> OpenAI:
    return OpenAI(
        api_key=token,
        organization="org-ivGGIRGxUk5rZmvxkoypdUUy",
        project="proj_t7kgt6Awz7m2knmH4gL0xeh2"
    )
