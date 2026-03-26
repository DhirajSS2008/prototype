# -*- coding: utf-8 -*-
"""AI-powered explanations and email drafting — Gemini primary, Groq fallback."""

import logging
import httpx
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)

_SYM = "\u20b9"

# Tone templates for different relationship types
TONE_INSTRUCTIONS = {
    "local_vendor": "Use a warm, friendly, and relationship-preserving tone. This is a local vendor with whom the business has a personal relationship.",
    "bank": "Use a formal, structured tone. Reference financial terms appropriately. This is a communication with a banking institution.",
    "supplier": "Use a professional, partnership-focused tone. Emphasize the ongoing business relationship and mutual benefit.",
    "landlord": "Use a respectful, lease-aware tone. Acknowledge the rental agreement and maintain a cordial relationship.",
    "tax_authority": "Use a highly formal, compliance-citing tone. Reference intent to comply with all regulations and statutory obligations.",
}

# ─── AI Backend Abstraction ──────────────────────────────────────


async def _call_ai(prompt: str) -> Optional[str]:
    """Call Gemini first; if it fails (quota, error), fall back to Groq.

    Returns the generated text or None.
    """
    settings = get_settings()

    # Attempt 1 — Gemini
    if settings.GEMINI_API_KEY:
        text = await _call_gemini(prompt, settings)
        if text:
            return text
        logger.warning("Gemini failed — trying Groq fallback")

    # Attempt 2 — Groq
    if settings.GROQ_API_KEY:
        text = await _call_groq(prompt, settings)
        if text:
            return text
        logger.warning("Groq fallback also failed")

    return None


async def _call_gemini(prompt: str, settings) -> Optional[str]:
    """Generate content via Gemini REST API (no deprecated SDK)."""
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
        if resp.status_code == 200:
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if text:
                logger.info("Gemini generated content OK")
                return text.strip()
        else:
            logger.error(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")
            return None
    except Exception as e:
        logger.error(f"Gemini exception: {e}")
        return None


async def _call_groq(prompt: str, settings) -> Optional[str]:
    """Generate content via Groq chat completion API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 600,
                    "temperature": 0.7,
                },
            )
        if resp.status_code == 200:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            logger.info("Groq generated content OK (fallback)")
            return text.strip()
        else:
            logger.error(f"Groq HTTP {resp.status_code}: {resp.text[:300]}")
            return None
    except Exception as e:
        logger.error(f"Groq exception: {e}")
        return None


# ─── Parse helpers ──────────────────────────────────────────────

def _parse_email(text: str, default_subject: str) -> dict:
    """Parse 'Subject: ...\n<body>' format into {subject, body}."""
    lines = text.split("\n", 1)
    subject = default_subject
    body = text
    if lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
    return {"subject": subject, "body": body}


# ─── Public API ─────────────────────────────────────────────────


async def generate_explanation(result) -> str:
    """Generate a plain-English explanation of the affordability decision."""
    prompt = f"""You are a financial advisor for a small business owner. Based on the following affordability analysis, provide a clear 2-3 sentence explanation of the decision. Reference specific numbers. Be direct and actionable.

Expense: {result.expense_name}
Amount: {_SYM}{result.expense_amount:,.2f}
Category: {result.expense_category}
Priority: {result.priority_tier}
Decision: {result.decision}
Reason: {result.reason_code}
Current Balance: {_SYM}{result.current_balance:,.2f}
Projected Balance at Expense Date: {_SYM}{result.projected_balance_at_date:,.2f}
Monthly Burn Rate: {_SYM}{result.monthly_burn_rate:,.2f}
Deferral Days: {result.deferral_days or 'N/A'}
Recommended Date: {result.recommended_date or 'N/A'}

{"Alternative paths available:" if result.alternative_paths else ""}
{chr(10).join(f"- {ap.description}" for ap in result.alternative_paths) if result.alternative_paths else ""}"""

    text = await _call_ai(prompt)
    if text:
        return text
    return _generate_fallback_explanation(result)


async def generate_negotiation_email(
    result,
    vendor_name: str,
    relationship_type: str,
    deferral_days: int,
    business_name: str = "Our Business",
    outstanding_amount: Optional[float] = None,
) -> dict:
    """Generate a tone-aware professional negotiation email.

    Returns dict with 'subject' and 'body' keys.
    """
    amount = outstanding_amount or result.expense_amount
    revised_date = result.recommended_date if hasattr(result, 'recommended_date') else "N/A"
    tone = TONE_INSTRUCTIONS.get(relationship_type, TONE_INSTRUCTIONS["local_vendor"])

    prompt = f"""Write a professional email requesting to reschedule a payment obligation.

CONTEXT:
- Sender: {business_name}
- Recipient: {vendor_name}
- Relationship type: {relationship_type}
- Outstanding amount: {_SYM}{amount:,.2f}
- Requested deferral: {deferral_days} days
- Proposed revised payment date: {revised_date}
- Reason: The business is managing a temporary liquidity constraint but expects the situation to resolve by the revised date based on forecasted receivables.
- Do NOT disclose internal financial forecasts or sensitive data.

TONE INSTRUCTIONS:
{tone}

OUTPUT FORMAT:
Write the subject line on the first line prefixed with "Subject: "
Then write the email body. Keep it under 200 words.
"""

    text = await _call_ai(prompt)
    if text:
        return _parse_email(text, "Payment Deferral Request")
    return _generate_fallback_negotiation(vendor_name, relationship_type, deferral_days, amount, revised_date, business_name)


async def generate_borrowing_email(
    result,
    borrowing_amount: float,
    borrowing_cost: float,
    purpose: str,
    business_name: str = "Our Business",
) -> dict:
    """Generate a professional borrowing request email.

    Returns dict with 'subject' and 'body' keys.
    """
    prompt = f"""Write a professional and confident business email to a lender requesting a short-term borrowing arrangement.

CONTEXT:
- Sender: {business_name}
- Borrowing requirement: {_SYM}{borrowing_amount:,.2f}
- Purpose of funds: {purpose}
- Repayment timeline: 30 days
- Interest/Cost accounted for: {_SYM}{borrowing_cost:,.2f}
- Reason: The business has a high-priority obligation and is looking to leverage short-term liquidity.

TONE: Formal and confident. Reference financial terms appropriately.

OUTPUT FORMAT:
Write the subject line on the first line prefixed with "Subject: "
Then write the email body. Keep it under 200 words.
"""

    text = await _call_ai(prompt)
    if text:
        return _parse_email(text, "Short-Term Borrowing Request")
    return _generate_fallback_borrowing(borrowing_amount, borrowing_cost, purpose, business_name)


async def generate_reminder_email(
    vendor_name: str,
    outstanding_amount: float,
    contact_person: Optional[str] = None,
    business_name: str = "Our Business",
) -> dict:
    """Generate a friendly but firm payment reminder.

    Returns dict with 'subject' and 'body' keys.
    """
    recipient = contact_person or vendor_name

    prompt = f"""Write a professional payment reminder email.

CONTEXT:
- Sender: {business_name}
- Recipient: {recipient}
- Outstanding Balance: {_SYM}{outstanding_amount:,.2f}
- Purpose: A friendly follow-up regarding an unpaid balance.

TONE: Professional, polite, yet clear about the requirement for payment.

OUTPUT FORMAT:
Write an automated, compelling subject line on the first line prefixed with "Subject: "
Then write the email body. Keep it short (under 100 words).
"""

    text = await _call_ai(prompt)
    if text:
        return _parse_email(text, f"Follow-up: Outstanding Payment for {business_name}")
    return _generate_fallback_reminder(recipient, outstanding_amount, business_name)


# ─── Fallbacks ──────────────────────────────────────────────────

def _generate_fallback_explanation(result) -> str:
    s = _SYM
    if result.decision == "APPROVE":
        return (
            f"Your expense of {s}{result.expense_amount:,.2f} for {result.expense_name} is affordable. "
            f"With a current balance of {s}{result.current_balance:,.2f} and projected balance of "
            f"{s}{result.projected_balance_at_date:,.2f} at the expense date, you have sufficient liquidity."
        )
    elif result.decision == "DEFER":
        return (
            f"The expense of {s}{result.expense_amount:,.2f} for {result.expense_name} would strain your liquidity. "
            f"Your projected balance of {s}{result.projected_balance_at_date:,.2f} against a monthly burn of "
            f"{s}{result.monthly_burn_rate:,.2f} suggests deferring by {result.deferral_days} days "
            f"to {result.recommended_date}."
        )
    else:
        return (
            f"The expense of {s}{result.expense_amount:,.2f} for {result.expense_name} creates a critical liquidity conflict. "
            f"However, as a {result.priority_tier}-priority expense, we've identified alternative paths to proceed. "
            f"Review the options below."
        )


def _generate_fallback_negotiation(vendor_name, relationship_type, deferral_days, amount, revised_date, business_name):
    return {
        "subject": f"Payment Deferral Request — {business_name}",
        "body": f"""Dear {vendor_name},

I hope this message finds you well. I am writing on behalf of {business_name} to request a brief extension on our upcoming payment of {_SYM}{amount:,.2f}.

Due to a temporary liquidity adjustment, I would like to request a {deferral_days}-day extension. The full payment will be processed by {revised_date}.

We greatly value our business relationship and appreciate your understanding in this matter. Please let me know if this arrangement works for you.

Thank you for your continued partnership.

Best regards,
{business_name}"""
    }


def _generate_fallback_borrowing(amount, cost, purpose, business_name):
    return {
        "subject": f"Short-Term Borrowing Request — {business_name}",
        "body": f"""Dear Lender,
 
I am writing on behalf of {business_name} to formally request a short-term borrowing arrangement of {_SYM}{amount:,.2f}.
 
These funds will be specifically used for {purpose}. We have carefully reviewed our financial projections and have accounted for the borrowing cost of {_SYM}{cost:,.2f}. We are confident in our ability to repay this amount in full within the next 30 days.
 
I would appreciate the opportunity to discuss the terms of this arrangement further.
 
Best regards,
{business_name}"""
    }


def _generate_fallback_reminder(recipient, amount, business_name):
    return {
        "subject": f"Reminder: Outstanding Payment - {business_name}",
        "body": f"Hello {recipient},\n\nThis is a friendly reminder regarding the outstanding balance of {_SYM}{amount:,.2f} on your account with {business_name}.\n\nBest regards,\nFinance Team"
    }
