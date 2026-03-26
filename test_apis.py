"""Quick standalone test: Gemini drafts an email, Resend sends it."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
RESEND_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


async def draft_with_gemini() -> dict:
    """Use Gemini to draft a reminder email."""
    print(f"[1/2] Gemini key: {GEMINI_KEY[:12]}...")
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = (
        "Write a short professional payment reminder email for a vendor named "
        "'ABC Suppliers' with an outstanding ₹25,000. "
        "First line must be 'Subject: <your subject>'. Keep body under 80 words."
    )

    resp = model.generate_content(prompt)
    text = resp.text.strip()
    print(f"Gemini raw output:\n{text}\n")

    lines = text.split("\n", 1)
    subject = "Payment Reminder"
    body = text
    if lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    return {"subject": subject, "body": body}


async def send_with_resend(subject: str, body: str) -> bool:
    """Send the drafted email via Resend."""
    print(f"[2/2] Resend key: {RESEND_KEY[:12]}...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"LiquiSense <{RESEND_FROM}>",
                "to": ["delivered@resend.dev"],
                "subject": subject,
                "text": body,
            },
        )
    print(f"Resend status: {resp.status_code}")
    print(f"Resend response: {resp.text}")
    return resp.status_code in (200, 201)


async def main():
    print("=" * 50)
    print("  GEMINI → RESEND PIPELINE TEST")
    print("=" * 50)

    # Step 1: Gemini drafts
    email = await draft_with_gemini()
    print(f"✏️  Subject: {email['subject']}")
    print(f"✏️  Body: {email['body'][:120]}...\n")

    # Step 2: Resend sends
    ok = await send_with_resend(email["subject"], email["body"])
    print()
    print(f"{'✅ PIPELINE SUCCESS' if ok else '❌ PIPELINE FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
