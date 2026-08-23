from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

from backend.app.schemas.bkt import (
    BKTParameters,
    BKTUpdateRequest,
    BKTUpdateResponse,
    StudentKCMasteryModel,
)


class BKTService:
    """
    Bayesian Knowledge Tracing (BKT) Hidden Markov Model Engine.
    Tracks latent mastery state probability P(L_t) per Knowledge Component (KC).
    """

    DEFAULT_PARAMS = BKTParameters(
        p_l0=0.10,
        p_transit=0.15,
        p_guess=0.20,
        p_slip=0.10,
        mastery_threshold=0.85
    )

    @classmethod
    def compute_bkt_step(
        cls,
        prior_p_l: float,
        is_correct: bool,
        params: BKTParameters = DEFAULT_PARAMS,
    ) -> Tuple[float, float, bool]:
        """
        Executes single observation update step:
        Returns: (posterior_p_l, updated_p_l, is_mastered)
        """
        p_l = max(0.0, min(1.0, prior_p_l))
        p_s = params.p_slip
        p_g = params.p_guess
        p_t = params.p_transit

        eps = 1e-9

        if is_correct:
            # Observation = 1
            numerator = p_l * (1.0 - p_s)
            denominator = numerator + (1.0 - p_l) * p_g
            denominator = max(eps, denominator)
            posterior = numerator / denominator
        else:
            # Observation = 0
            numerator = p_l * p_s
            denominator = numerator + (1.0 - p_l) * (1.0 - p_g)
            denominator = max(eps, denominator)
            posterior = numerator / denominator

        posterior = max(0.0, min(1.0, posterior))

        # Transition projection to next practice opportunity
        updated_p_l = posterior + (1.0 - posterior) * p_t
        updated_p_l = max(0.0, min(1.0, updated_p_l))

        is_mastered = updated_p_l >= params.mastery_threshold

        return posterior, updated_p_l, is_mastered

    @classmethod
    def update_mastery(
        cls,
        request: BKTUpdateRequest,
        existing_model: StudentKCMasteryModel = None,
    ) -> BKTUpdateResponse:
        params = request.params or cls.DEFAULT_PARAMS
        prior_p_l = request.current_p_l if request.current_p_l is not None else (
            existing_model.p_l if existing_model else params.p_l0
        )

        posterior, updated_p_l, is_mastered = cls.compute_bkt_step(
            prior_p_l=prior_p_l,
            is_correct=request.is_correct,
            params=params,
        )

        total_att = (existing_model.total_attempts + 1) if existing_model else 1
        correct_att = ((existing_model.correct_attempts + 1) if request.is_correct else existing_model.correct_attempts) if existing_model else (1 if request.is_correct else 0)

        return BKTUpdateResponse(
            user_id=request.user_id,
            kc_id=request.kc_id,
            observation=1 if request.is_correct else 0,
            prior_p_l=round(prior_p_l, 6),
            posterior_p_l=round(posterior, 6),
            updated_p_l=round(updated_p_l, 6),
            is_mastered=is_mastered,
            total_attempts=total_att,
            correct_attempts=correct_att,
            delta=round(updated_p_l - prior_p_l, 6),
        )
