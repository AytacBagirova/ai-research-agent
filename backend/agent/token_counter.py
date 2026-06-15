"""
Token sayma modulu — tiktoken istifadə edir.
Agent hər addımda neçə token işlətdiyini hesablayır.
"""
import tiktoken


# Claude modelleri ucun cl100k_base encoding istifade edirik
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Bir mətnin token sayını hesablayır.
    text → sayılacaq mətn
    """
    if not text:
        return 0
    return len(_ENCODING.encode(text))


def count_messages_tokens(messages: list[dict]) -> int:
    """
    Bir neçə mesajın ümumi token sayını hesablayır.
    messages → Claude-a göndəriləcək mesaj siyahısı
    """
    total = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += count_tokens(str(block.get("content", "")))
                    total += count_tokens(str(block.get("text", "")))
    return total


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-haiku"
) -> float:
    """
    Token sayına görə təxmini xərci hesablayır (USD).
    Qiymətlər 1M token üçündür.
    """
    prices = {
        "claude-haiku": {"input": 0.80, "output": 4.00},
        "claude-sonnet": {"input": 3.00, "output": 15.00},
    }

    model_key = "claude-haiku" if "haiku" in model else "claude-sonnet"
    price = prices.get(model_key, prices["claude-haiku"])

    input_cost = (input_tokens / 1_000_000) * price["input"]
    output_cost = (output_tokens / 1_000_000) * price["output"]

    return round(input_cost + output_cost, 6)


def format_token_summary(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-haiku"
) -> str:
    """
    Token statistikasını oxunaqlı formata çevirir.
    """
    total = input_tokens + output_tokens
    cost = estimate_cost(input_tokens, output_tokens, model)
    return (
        f"Tokens: {total:,} total "
        f"({input_tokens:,} input + {output_tokens:,} output) | "
        f"Cost: ~${cost:.4f}"
    )