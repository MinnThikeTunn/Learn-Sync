from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class BKTParameters(BaseModel):
    """
    Standard Bayesian Knowledge Tracing parameters:
    - p_l0: Prior initial probability of knowing the KC (default 0.10)
    - p_transit: Probability of transitioning from unmastered to mastered state after practice (default 0.15)
    - p_guess: Probability of guessing correctly without knowing the KC (default 0.20)
    - p_slip: Probability of making an accidental mistake despite knowing the KC (default 0.10)
    """
    p_l0: float = Field(default=0.10, ge=0.0, le=1.0)
    p_transit: float = Field(default=0.15, ge=0.0, le=1.0)
    p_guess: float = Field(default=0.20, ge=0.0, le=1.0)
    p_slip: float = Field(default=0.10, ge=0.0, le=1.0)
    mastery_threshold: float = Field(default=0.85, ge=0.50, le=1.0)


class StudentKCMasteryModel(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: UUID
    kc_id: UUID
    p_l: float = Field(default=0.10, ge=0.0, le=1.0, description="Current posterior probability P(L_t)")
    p_transit: float = Field(default=0.15, ge=0.0, le=1.0)
    p_guess: float = Field(default=0.20, ge=0.0, le=1.0)
    p_slip: float = Field(default=0.10, ge=0.0, le=1.0)
    total_attempts: int = Field(default=0, ge=0)
    correct_attempts: int = Field(default=0, ge=0)
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class BKTUpdateRequest(BaseModel):
    user_id: UUID
    kc_id: UUID
    is_correct: bool = Field(..., description="Observation O_t in {0, 1}")
    params: Optional[BKTParameters] = None
    current_p_l: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class BKTUpdateResponse(BaseModel):
    user_id: UUID
    kc_id: UUID
    observation: int = Field(..., ge=0, le=1, description="1 if correct, 0 if incorrect")
    prior_p_l: float = Field(..., ge=0.0, le=1.0)
    posterior_p_l: float = Field(..., ge=0.0, le=1.0, description="P(L_t | O_t)")
    updated_p_l: float = Field(..., ge=0.0, le=1.0, description="Projected state P(L_{t+1}) after transition")
    is_mastered: bool
    total_attempts: int
    correct_attempts: int
    delta: float = Field(..., description="updated_p_l - prior_p_l")
