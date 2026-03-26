# -*- coding: utf-8 -*-
"""Claude API integration for natural language explanations."""

import logging
from typing import Optional
from config import get_settings
from schemas.affordability import AffordabilityResponse

logger = logging.getLogger(__name__)

# Rupee sign as unicode escape — avoids CP1252 UnicodeEncodeError on Windows
_SYM = "\u20b9"


async def generate_explanation(result: AffordabilityResponse) -> str:
    """Generate a plain-English explanation of the affordability decision using Claude API."""
    settings = get_settings()

    if not settings.ANTHROPIC_API_KEY:
        return _generate_fallback_explanation(result)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return _generate_fallback_explanation(result)


async def generate_negotiation_email(
    result: AffordabilityResponse,
    counterparty: str,
    deferral_days: int,
) -> str:
    """Generate a professional negotiation email to defer an obligation."""
    settings = get_settings()

    if not settings.ANTHROPIC_API_KEY:
        return _generate_fallback_email(counterparty, deferral_days, result)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""Write a professional, courteous business email requesting to reschedule a payment. The tone should be warm but professional, suitable for an existing business relationship.

Details:
- Recipient/Vendor: {counterparty}
- Payment to defer: related to a {result.expense_category} obligation
- Requested delay: {deferral_days} days
- Reason: The business needs to cover a high-priority {result.expense_category} expense of {_SYM}{result.expense_amount:,.2f}
- Assurance: Full payment will be made within {deferral_days} days

Write only the email body (no subject line). Keep it under 150 words."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Claude API error for email: {e}")
        return _generate_fallback_email(counterparty, deferral_days, result)


def _generate_fallback_explanation(result: AffordabilityResponse) -> str:
    """Generate explanation without Claude API (encoding-safe)."""
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
    """Generate a basic negotiation email without Claude API."""
    return f"""Dear {counterparty},

I hope this message finds you well. I am writing to request a brief extension on our upcoming payment.

Due to an urgent {result.expense_category} expense that requires immediate attention, I would like to request a {deferral_days}-day extension on our scheduled payment. I want to assure you that this is a temporary adjustment and the full payment will be processed within {deferral_days} days of the original due date.

We greatly value our business relationship and appreciate your understanding in this matter. Please let me know if this arrangement works for you, or if you would like to discuss alternatives.

Thank you for your continued partnership.

Best regards"""
