import logging
from enum import StrEnum
from typing import BinaryIO, Dict, Optional, List

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from config.settings import CommonSettings

token = CommonSettings().OPENAI_API_KEY

user_conversation_history: Dict[str, List[Dict[str, str]]] = {}


def clean(user_id: str) -> None:
    if user_id in user_conversation_history:
        user_conversation_history[user_id] = []


def generate_text(
        user_id: str,
        content: str,
        model: str = "gpt-4o-mini",
        developer_message: Optional[Dict] = None,
        max_history: int = 10,
        n: int = 1,
) -> ChatCompletionMessage:
    """
    Generate text response while maintaining conversation history for a specific user.
    
    Args:
        content: User's message content
        user_id: user id to maintain separate conversation history
        model: OpenAI model to use
        developer_message: Optional system message to set context
        n: Number of responses to generate
        max_history: Maximum number of messages to keep in history
    
    Returns:
        ChatCompletionMessage containing the model's response
    """
    if user_id not in user_conversation_history:
        user_conversation_history[user_id] = []
    messages = user_conversation_history[user_id].copy()
    if developer_message:
        messages.append(developer_message)
    messages.append({"role": "user", "content": content})
    completion = get_client().chat.completions.create(
        model=model,
        store=True,
        messages=messages,  # type: ignore
        n=n
    )
    if model == "o3-mini" or model == "o4-mini":
        messages.append(
            {"role": "system", "content": "Formatting re-enabled"}
        )
        completion = get_client().chat.completions.create(
            model=model,
            store=True,
            messages=messages,  # type: ignore
            n=n,
            reasoning_effort="high"
        )
    user_conversation_history[user_id].extend([
        {"role": "user", "content": content},
        {"role": "assistant", "content": completion.choices[0].message.content}
    ])

    if len(user_conversation_history[user_id]) > max_history * 2:  # *2 because each exchange has 2 messages
        user_conversation_history[user_id] = user_conversation_history[user_id][-max_history * 2:]

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


def get_answer_from_friend(user_id: str, content: str, model: str = "gpt-4o-mini") -> ChatCompletionMessage:
    prompt = """You are an american man. We are in a friendly dialogue.
    You can express your opinion and use informal phrases.
    Sometimes you can make jokes or ironical tone. 
    """
    developer_message = {"role": "system", "content": prompt}
    return generate_text(user_id, content, model, developer_message)


def get_english_teacher_comment(user_id: str, content: str, model: str = "gpt-4o-mini") -> ChatCompletionMessage:
    prompt = """You are a helpful english teacher. 
    Please help to improve grammar, vocabulary and naturalness of this speech.
    Make verbose comment about errors in this areas.
    """
    developer_message = {"role": "system", "content": prompt}
    return generate_text(user_id, content, model, developer_message)


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
    gpt_4o_mini = "gpt-4o-mini"
    gpt_41_mini = "gpt-4.1-mini"
    gpt_41_nano = "gpt-4.1-nano"
    o3_mini = "o3-mini"
    o4_mini = "o4-mini"
    # требуют верификации личности на 15.06.2025 (ее не пройти с российским паспортом):
    # o3 = "o3"
    # o3_pro = "o3-pro-2025-06-10"


def get_client() -> OpenAI:
    return OpenAI(
        api_key=token,
        organization="org-ivGGIRGxUk5rZmvxkoypdUUy",
        project="proj_t7kgt6Awz7m2knmH4gL0xeh2"
    )
