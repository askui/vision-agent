from fastapi import APIRouter, HTTPException, Request, status

from askui.chat.api.chat_completions.dependencies import ChatCompletionServiceDep
from askui.chat.api.chat_completions.service import (  # ChatCompletionRequest,
    ChatCompletion,
    ChatCompletionService,
)

router = APIRouter(prefix="/chat/completions", tags=["chat"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chat_completion(
    request: Request,
    chat_completion_service: ChatCompletionService = ChatCompletionServiceDep,
) -> ChatCompletion:
    """Create a new chat completion.

    Args:
        request: Chat completion request
        chat_completion_service: Service for managing chat completions

    Returns:
        ChatCompletion object

    Raises:
        HTTPException: If thread or assistant doesn't exist
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    try:
        print(await request.json())
        raise HTTPException(status_code=400, detail="Not implemented")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
