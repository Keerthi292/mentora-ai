import asyncio
from collections.abc import AsyncIterator


def generate_mock_response(system_prompt: str, user_message: str) -> str:
    """Return a predictable reply without calling any external model."""
    return (
        "Mentora AI (mock response): "
        f'I received your message: "{user_message}". '
        "Real, personalized guidance will be available once an LLM is connected."
    )


async def stream_mock_response(
    system_prompt: str, user_message: str
) -> AsyncIterator[str]:
    """Yield the mock reply a few words at a time, like a real LLM stream.

    Later, replace this with a real LLM streaming call. Keep it yielding
    text chunks so the rest of the code doesn't change.
    """
    full_text = generate_mock_response(system_prompt, user_message)
    for word in full_text.split(" "):
        yield word + " "
        await asyncio.sleep(0.05)  # simulates model latency