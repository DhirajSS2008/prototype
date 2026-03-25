"""Expense profiler service using pandas and scikit-learn."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session

from models.transaction import Transaction
from models.cash_balance import CashBalanceSnapshot

logger = logging.getLogger(__name__)


def get_transaction_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    """Load all transactions for a user into a pandas DataFrame."""
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if not transactions:
        return pd.DataFrame()

    data = [t.to_dict() for t in transactions]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def compute_category_averages(df: pd.DataFrame) -> dict:
    """Compute average monthly spend per category.

    Returns dict: {category: {"avg_monthly": float, "total": float, "count": int}}
    """
    if df.empty:
        return {}

    # Filter to expenses (negative amounts)
    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return {}

    expenses["abs_amount"] = expenses["amount"].abs()
    expenses["month"] = expenses["date"].dt.to_period("M")

    # Number of unique months in dataset
    n_months = max(expenses["month"].nunique(), 1)

    result = {}
    for category, group in expenses.groupby("category"):
        total = group["abs_amount"].sum()
        result[category] = {
            "avg_monthly": round(total / n_months, 2),
            "total": round(total, 2),
            "count": len(group),
            "avg_per_transaction": round(group["abs_amount"].mean(), 2),
        }

    return result


def classify_recurring_transactions(df: pd.DataFrame, db: Session, user_id: int) -> dict:
    """Classify transactions as recurring vs one-time using clustering.

    Uses features: frequency of counterparty, amount consistency, regularity of dates.
    Returns summary stats.
    """
    if df.empty or len(df) < 5:
        return {"recurring_count": 0, "one_time_count": len(df)}

    expenses = df[df["amount"] < 0].copy()
    if len(expenses) < 5:
        return {"recurring_count": 0, "one_time_count": len(expenses)}

    # Build features per counterparty/category group
    expenses["abs_amount"] = expenses["amount"].abs()
    expenses["month"] = expenses["date"].dt.to_period("M")

    # Group by counterparty + category
    group_key = expenses.apply(
        lambda r: f"{r.get('counterparty', 'unknown')}|{r['category']}", axis=1
    )
    expenses["group_key"] = group_key

    features_list = []
    group_ids = []

    for gk, group in expenses.groupby("group_key"):
        frequency = len(group)
        amount_std = group["abs_amount"].std() if len(group) > 1 else group["abs_amount"].iloc[0]
        amount_mean = group["abs_amount"].mean()
        cv = (amount_std / amount_mean) if amount_mean > 0 else 1.0  # coefficient of variation
        months_active = group["month"].nunique()
        n_months_total = max(expenses["month"].nunique(), 1)
        month_coverage = months_active / n_months_total

        features_list.append([frequency, cv, month_coverage])
        group_ids.append(gk)

    if len(features_list) < 2:
        return {"recurring_count": 0, "one_time_count": len(expenses)}

    features = np.array(features_list)

    # Normalize features
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # KMeans with 2 clusters: recurring vs one-time
    n_clusters = min(2, len(features_scaled))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    # The cluster with higher frequency/month_coverage is likely recurring
    cluster_means = {}
    for label in range(n_clusters):
        mask = labels == label
        cluster_means[label] = features[mask][:, 2].mean()  # month_coverage

    recurring_label = max(cluster_means, key=cluster_means.get)

    # Update transactions in DB
    recurring_groups = set()
    one_time_groups = set()
    for i, gk in enumerate(group_ids):
        if labels[i] == recurring_label:
            recurring_groups.add(gk)
        else:
            one_time_groups.add(gk)

    # Bulk update (only for this user's transactions)
    for tx in db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.amount < 0).all():
        gk = f"{tx.counterparty or 'unknown'}|{tx.category}"
        tx.is_recurring = gk in recurring_groups
    db.commit()

    return {
        "recurring_count": sum(1 for l in labels if l == recurring_label),
        "one_time_count": sum(1 for l in labels if l != recurring_label),
        "recurring_groups": list(recurring_groups),
    }


def compute_burn_rate(db: Session, user_id: int, df: pd.DataFrame) -> float:
    """Compute monthly burn rate as difference between first and last row balance.

    Burn rate = (first_row_balance - last_row_balance) / number_of_months
    This gives a clear picture of how much cash was burned over the statement period.
    """
    if df.empty:
        return 0.0

    # Filter rows that have a balance value
    with_balance = df[df["balance"].notna()].copy()
    
    if with_balance.empty:
        # Fallback: sum expenses if no balance column
        expenses = df[df["amount"] < 0].copy()
        if expenses.empty:
            return 0.0
        expenses["abs_amount"] = expenses["amount"].abs()
        expenses["month"] = expenses["date"].dt.to_period("M")
        n_months = max(expenses["month"].nunique(), 1)
        return round(expenses["abs_amount"].sum() / n_months, 2)

    # Sort by date then by row order (id)
    with_balance = with_balance.sort_values(["date", "id"])

    first_balance = float(with_balance.iloc[0]["balance"])
    last_balance = float(with_balance.iloc[-1]["balance"])

    # Burn = first - last (positive means money was spent)
    total_burn = first_balance - last_balance

    # Calculate the time span in months
    date_range_days = (with_balance["date"].max() - with_balance["date"].min()).days
    n_months = max(date_range_days / 30.0, 1.0)

    monthly_burn = total_burn / n_months

    return round(monthly_burn, 2)


def run_full_profile(db: Session, user_id: int) -> dict:
    """Run the full expense profile analysis.

    Returns a complete profile dict for caching and display.
    """
    df = get_transaction_dataframe(db, user_id)

    if df.empty:
        return {
            "category_averages": {},
            "recurring_classification": {"recurring_count": 0, "one_time_count": 0},
            "monthly_burn_rate": 0.0,
            "total_transactions": 0,
            "date_range": None,
        }

    category_averages = compute_category_averages(df)
    recurring_info = classify_recurring_transactions(df, db, user_id)
    burn_rate = compute_burn_rate(db, user_id, df)

    profile = {
        "category_averages": category_averages,
        "recurring_classification": recurring_info,
        "monthly_burn_rate": round(burn_rate, 2),
        "total_transactions": len(df),
        "date_range": {
            "start": df["date"].min().isoformat(),
            "end": df["date"].max().isoformat(),
        },
    }

    return profile
