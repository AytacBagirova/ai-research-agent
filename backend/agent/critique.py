import anthropic
from backend.config import settings
from backend.agent.prompts import CRITIQUE_PROMPT


class SelfCritique:
    """
    Agent öz hesabatını yoxlayır.
    Zəif cəhətlər varsa — əlavə araşdırma lazım olduğunu bildirir.
    Hesabat yetərlidirsə — "REPORT_APPROVED" qaytarır.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def evaluate(self, topic: str, report: str) -> tuple[bool, str]:
        """
        Hesabatı qiymətləndirir.

        topic  → araşdırılan mövzu
        report → agentin yazdığı hesabat

        Qaytarır:
        (True, "REPORT_APPROVED")        → hesabat yetərlidir
        (False, "çatışmayan hissələr...") → əlavə araşdırma lazımdır
        """
        # Claude-a göndəriləcək mesaj
        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",  # critique üçün sürətli model kifayətdir
            max_tokens=500,                      # qısa cavab lazımdır
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{CRITIQUE_PROMPT}\n\n"
                        f"Topic: {topic}\n\n"
                        f"Report:\n{report}"
                    )
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # "REPORT_APPROVED" varsa — hesabat yetərlidir
        if "REPORT_APPROVED" in response_text:
            return True, response_text

        # Yoxdursa — əlavə araşdırma lazımdır
        return False, response_text