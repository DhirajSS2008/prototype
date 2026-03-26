"""Priority mapping model — maps expense categories to priority tiers."""

from sqlalchemy import Column, Integer, String, Float
from database import Base


class PriorityMapping(Base):
    __tablename__ = "priority_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), unique=True, nullable=False, index=True)
    priority_tier = Column(String(10), nullable=False)  # HIGH, MID, LOW
    flexibility_score = Column(Float, default=0.5)  # 0=rigid, 1=very flexible
    penalty_rate = Column(Float, default=0.0)  # cost of deferral

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "priority_tier": self.priority_tier,
            "flexibility_score": self.flexibility_score,
            "penalty_rate": self.penalty_rate,
        }


# Default priority mappings to seed the database
DEFAULT_PRIORITY_MAPPINGS = [
    # HIGH priority — critical, non-deferrable
    {"category": "Health & Medical", "priority_tier": "HIGH", "flexibility_score": 0.1, "penalty_rate": 0.0},
    {"category": "Legal & Compliance", "priority_tier": "HIGH", "flexibility_score": 0.1, "penalty_rate": 0.15},
    {"category": "Critical Operations", "priority_tier": "HIGH", "flexibility_score": 0.2, "penalty_rate": 0.10},
    {"category": "Tax & Government", "priority_tier": "HIGH", "flexibility_score": 0.1, "penalty_rate": 0.18},
    # MID priority — important but deferrable
    {"category": "Equipment & Tools", "priority_tier": "MID", "flexibility_score": 0.5, "penalty_rate": 0.05},
    {"category": "Travel & Transport", "priority_tier": "MID", "flexibility_score": 0.6, "penalty_rate": 0.02},
    {"category": "Vendor Advances", "priority_tier": "MID", "flexibility_score": 0.5, "penalty_rate": 0.03},
    {"category": "Marketing", "priority_tier": "MID", "flexibility_score": 0.7, "penalty_rate": 0.01},
    {"category": "Rent & Lease", "priority_tier": "MID", "flexibility_score": 0.3, "penalty_rate": 0.08},
    {"category": "Loan EMI", "priority_tier": "MID", "flexibility_score": 0.2, "penalty_rate": 0.12},
    {"category": "Supplier Payments", "priority_tier": "MID", "flexibility_score": 0.4, "penalty_rate": 0.05},
    # LOW priority — discretionary
    {"category": "Office Supplies", "priority_tier": "LOW", "flexibility_score": 0.9, "penalty_rate": 0.0},
    {"category": "Subscriptions", "priority_tier": "LOW", "flexibility_score": 0.8, "penalty_rate": 0.0},
    {"category": "Upgrades", "priority_tier": "LOW", "flexibility_score": 0.9, "penalty_rate": 0.0},
    {"category": "Discretionary", "priority_tier": "LOW", "flexibility_score": 1.0, "penalty_rate": 0.0},
    {"category": "Entertainment", "priority_tier": "LOW", "flexibility_score": 1.0, "penalty_rate": 0.0},
    {"category": "Other", "priority_tier": "LOW", "flexibility_score": 0.8, "penalty_rate": 0.0},
]
