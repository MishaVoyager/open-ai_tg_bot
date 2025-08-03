import logging
from enum import StrEnum
from typing import BinaryIO, Dict, Optional, List

from openai import AsyncOpenAI

from config.settings import CommonSettings

token = CommonSettings().OPENAI_API_KEY

# Храним последний response_id для каждого пользователя для продолжения разговора
user_last_response_id: Dict[str, str] = {}

# Модели, поддерживающие reasoning_effort
REASONING_MODELS = {
    "o3-mini", "o3", "o3-pro", "o3-pro-2025-06-10",
    "o4-mini", "o4"
}

# Модели, поддерживающие веб-поиск
WEB_SEARCH_MODELS = {"gpt-4o", "gpt-4o-mini"}


def clean(user_id: str) -> None:
    """Очистить историю разговора для конкретного пользователя."""
    if user_id in user_last_response_id:
        del user_last_response_id[user_id]


async def generate_text(
    user_id: str,
    content: str,
    model: str = "gpt-4o-mini",
    developer_message: Optional[Dict] = None,
    use_web_search: bool = False,
) -> str:
    """
    Generate text response while maintaining conversation history for a specific user.

    Args:
        user_id: user id to maintain separate conversation history
        content: User's message content
        model: OpenAI model to use
        developer_message: Optional system message to set context
        use_web_search: Whether to enable web search tool for the request

    Returns:
        str containing the model's response text
    """
    client = get_client()

    # Формируем input
    input_content = []

    # Добавляем системное сообщение если есть
    if developer_message:
        input_content.append(
            {"role": "system", "content": developer_message.get("content", "")}
        )

    # Добавляем пользовательское сообщение
    input_content.append({"role": "user", "content": content})

    # Получаем предыдущий response_id для продолжения разговора
    previous_response_id = user_last_response_id.get(user_id)

    # Проверяем поддержку reasoning_effort
    reasoning_effort = None
    if model in REASONING_MODELS:
        reasoning_effort = "high"

    # Подготавливаем инструменты
    tools = []
    if use_web_search:
        if model in WEB_SEARCH_MODELS:
            tools.append({"type": "web_search"})
        else:
            logging.warning(f"Веб-поиск запрошен, но модель {model} его не поддерживает. Используйте gpt-4o или gpt-4o-mini.")

    try:
        # Формируем параметры запроса
        request_params = {
            "model": model,
            "input": input_content if not previous_response_id else content,
            "store": True,
        }

        if previous_response_id:
            request_params["previous_response_id"] = previous_response_id

        if reasoning_effort:
            request_params["reasoning_effort"] = reasoning_effort

        if tools:
            request_params["tools"] = tools

        response = await client.responses.create(**request_params)

        # Сохраняем ID ответа для следующего запроса
        user_last_response_id[user_id] = response.id

        # Извлекаем текст ответа
        response_text = ""
        for output in response.output:
            if hasattr(output, "content") and output.content:
                for content_item in output.content:
                    if hasattr(content_item, "text"):
                        response_text += content_item.text

        logging.info(
            f"Запрос к {response.model} использовал {response.usage.total_tokens} токенов"
        )
        return response_text

    except Exception as e:
        logging.error(f"Ошибка при обращении к OpenAI API: {e}")
        raise


async def audio_to_text(audio_file: BinaryIO) -> str:
    client = get_client()
    transcription = await client.audio.transcriptions.create(
        model="whisper-1", file=audio_file, response_format="text"
    )
    return transcription


async def text_to_audio(text: str, response_format: str = "mp3") -> BinaryIO:
    client = get_client()
    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format=response_format,  # type: ignore
    )
    return response.read()  # type: ignore


async def get_answer_from_friend(
    user_id: str, content: str, model: str = "gpt-4o-mini"
) -> str:
    prompt = """You are an american man. We are in a friendly dialogue.
    You can express your opinion and use informal phrases.
    Sometimes you can make jokes or ironical tone. 
    """
    developer_message = {"role": "system", "content": prompt}
    return await generate_text(user_id, content, model, developer_message)


async def get_english_teacher_comment(
    user_id: str, content: str, model: str = "gpt-4o-mini"
) -> str:
    prompt = """You are a helpful english teacher. 
    Please help to improve grammar, vocabulary and naturalness of this speech.
    Make verbose comment about errors in this areas.
    """
    developer_message = {"role": "system", "content": prompt}
    return await generate_text(user_id, content, model, developer_message)


async def generate_text_with_web_search(
    user_id: str, content: str, model: str = "gpt-4o"
) -> str:
    """
    Generate text response with web search capability.

    Args:
        user_id: user id to maintain separate conversation history
        content: User's message content
        model: OpenAI model to use (should be gpt-4o or gpt-4o-mini for web search)

    Returns:
        str containing the model's response text with web search results
    """
    return await generate_text(user_id, content, model, use_web_search=True)


async def improve_transcript_by_gpt(transcript: str) -> str:
    system_prompt = """
    You are a helpful assistant. Your task is to correct any spelling discrepancies in the transcribed text.
    Only add necessary punctuation such as periods, commas, and capitalization, and use only the context provided.
    """

    try:
        client = get_client()
        response = await client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            store=False,
        )

        # Извлекаем текст ответа
        response_text = ""
        for output in response.output:
            if hasattr(output, "content") and output.content:
                for content_item in output.content:
                    if hasattr(content_item, "text"):
                        response_text += content_item.text

        return response_text

    except Exception as e:
        logging.error(f"Ошибка при улучшении транскрипта: {e}")
        raise


class GPTModel(StrEnum):
    gpt_4o_mini = "gpt-4o-mini"
    gpt_41_mini = "gpt-4.1-mini"
    gpt_41_nano = "gpt-4.1-nano"
    o3_mini = "o3-mini"
    o4_mini = "o4-mini"
    # требуют верификации личности на 15.06.2025 (ее не пройти с российским паспортом):
    # o3 = "o3"
    # o3_pro = "o3-pro-2025-06-10"


def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=token,
        organization="org-ivGGIRGxUk5rZmvxkoypdUUy",
        project="proj_t7kgt6Awz7m2knmH4gL0xeh2",
    )
