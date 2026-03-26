# -*- coding: utf-8 -*-
"""Groq API integration for natural language explanations."""

import logging
from typing import Optional
from config import get_settings
from schemas.affordability import AffordabilityResponse

logger = logging.getLogger(__name__)

# Rupee sign as unicode escape — avoids CP1252 UnicodeEncodeError on Windows
_SYM = "\u20b9"


async def generate_explanation(result: AffordabilityResponse) -> str:
    """Generate a plain-English explanation of the affordability decision using Groq API."""
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        return _generate_fallback_explanation(result)

    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)

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

        chat_completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return _generate_fallback_explanation(result)


async def generate_negotiation_email(
    result: AffordabilityResponse,
    counterparty: str,
    deferral_days: int,
) -> str:
    """Generate a professional negotiation email to defer an obligation."""
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        return _generate_fallback_email(counterparty, deferral_days, result)

    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)

        # Find the revised date from the result or forecast
        revised_date = result.recommended_date if hasattr(result, 'recommended_date') else "N/A"

        prompt = f"""Write a professional, courteous business email requesting to reschedule a payment. The tone should be warm but professional, suitable for an existing business relationship.

Details:
- Recipient/Vendor: {counterparty} (e.g., Shop Rent Landlord)
- Obligation to defer: {counterparty}
- Amount: {_SYM}{result.expense_amount:,.2f}
- Requested delay: {deferral_days} days
- Revised payment date: {revised_date}
- Reason: The business is managing a temporary liquidity constraint but expects the situation to resolve by the revised date based on forecasted receivables.
- Assurance: Full payment will be made by {revised_date}.

Write only the email body (no subject line). Keep it under 150 words."""

        chat_completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API error for email: {e}")
        return _generate_fallback_email(counterparty, deferral_days, result)


async def generate_borrowing_email(
    result: AffordabilityResponse,
    borrowing_amount: float,
    borrowing_cost: float,
    purpose: str,
) -> str:
    """Generate a professional email to a lender for short-term borrowing."""
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        return _generate_fallback_borrowing_email(borrowing_amount, borrowing_cost, purpose)

    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)

        prompt = f"""Write a professional and confident business email to a lender or relevant party requesting a short-term borrowing arrangement.

Details:
- Borrowing requirement: {_SYM}{borrowing_amount:,.2f}
- Purpose of funds: {purpose}
- Repayment timeline: 30 days
- Interest/Cost accounted for: {_SYM}{borrowing_cost:,.2f}
- Reason: The business has a high-priority investment and is looking to leverage short-term liquidity.

Write only the email body (no subject line). Keep it under 150 words."""

        chat_completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API error for borrowing email: {e}")
        return _generate_fallback_borrowing_email(borrowing_amount, borrowing_cost, purpose)


def _generate_fallback_borrowing_email(amount: float, cost: float, purpose: str) -> str:
    """Generate a basic borrowing email without Groq API."""
    return f"""Dear Lender,

I am writing to formally request a short-term borrowing arrangement for my business in the amount of {_SYM}{amount:,.2f}. 

These funds will be specifically used for {purpose}. We have carefully reviewed our financial projections and have accounted for the borrowing cost of {_SYM}{cost:,.2f}. We are confident in our ability to repay this amount in full within the next 30 days.

I would appreciate the opportunity to discuss the terms of this arrangement further.

Best regards"""


def _generate_fallback_explanation(result: AffordabilityResponse) -> str:
    """Generate explanation without Groq API (encoding-safe)."""
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


def _generate_fallback_email(counterparty: str, deferral_days: int, result: AffordabilityResponse) -> str:
    """Generate a basic negotiation email without Groq API."""
    return f"""Dear {counterparty},

I hope this message finds you well. I am writing to request a brief extension on our upcoming payment.

Due to an urgent {result.expense_category} expense that requires immediate attention, I would like to request a {deferral_days}-day extension on our scheduled payment. I want to assure you that this is a temporary adjustment and the full payment will be processed within {deferral_days} days of the original due date.

We greatly value our business relationship and appreciate your understanding in this matter. Please let me know if this arrangement works for you, or if you would like to discuss alternatives.

Thank you for your continued partnership.

Best regards"""
