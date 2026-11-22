"""Feedback-driven strategy selection (a small contextual bandit, one bandit per task type).

Each candidate strategy is an "arm". A 1-5 rating becomes a reward in [0, 1] and updates a
Beta posterior. This changes *prompting strategy only*; it does not train the language model.

Behaviour:
* Until the rule-based default strategy has `min_samples` ratings, it is always used.
* "thompson": sample each arm's posterior and pick the max. The default arm has an optimistic
  prior and untested alternatives a sceptical one, so exploration is rare unless the default
  is rated poorly.
* "greedy": pick the arm with the best posterior mean (ties -> default).
* "off": always the default.
"""

import random
from typing import Literal

Mode = Literal["thompson", "greedy", "off"]

BASE_PRIOR = (2.0, 0.0)  # extra (alpha, beta) for the rule-based default arm
ALT_PRIOR = (0.0, 1.0)  # extra (alpha, beta) for alternatives


def reward_from_rating(rating: int) -> float:
    if not 1 <= rating <= 5:
        raise ValueError("rating must be from 1 to 5")
    return (rating - 1) / 4


def select_strategy(
    base: str,
    candidates: list[str],
    stats: dict[str, tuple[int, float]],
    *,
    mode: Mode = "thompson",
    min_samples: int = 3,
    rng: random.Random | None = None,
) -> dict:
    """`stats[strategy] = (rating_count, sum_of_rewards)`; returns the decision and its evidence."""
    rng = rng or random.Random()
    arms = list(dict.fromkeys([base, *candidates]))  # base first, no duplicates
    base_count = stats.get(base, (0, 0.0))[0]

    def arm_report(strategy: str, sampled: float | None = None) -> dict:
        count, reward_sum = stats.get(strategy, (0, 0.0))
        prior_a, prior_b = BASE_PRIOR if strategy == base else ALT_PRIOR
        alpha = 1.0 + reward_sum + prior_a
        beta = 1.0 + (count - reward_sum) + prior_b
        return {
            "strategy": strategy,
            "ratings": count,
            "avg_rating": round(1 + 4 * reward_sum / count, 2) if count else None,
            "posterior_mean": round(alpha / (alpha + beta), 3),
            "_alpha": alpha, "_beta": beta,
            "sampled": None if sampled is None else round(sampled, 3),
        }

    def finish(chosen: str, method: str, reason: str, reports: list[dict]) -> dict:
        for report in reports:
            report.pop("_alpha", None)
            report.pop("_beta", None)
        return {
            "method": method, "mode": mode, "chosen": chosen, "default": base,
            "explored": chosen != base, "reason": reason, "min_samples": min_samples,
            "arms": reports,
            "note": "Heuristic prompt-strategy selection from user ratings; the model is not fine-tuned.",
        }

    if mode == "off":
        return finish(base, "disabled", "Adaptation is turned off.", [arm_report(a) for a in arms])
    if base_count < min_samples:
        return finish(
            base, "insufficient_feedback",
            f"Default strategy has {base_count}/{min_samples} ratings; using it.",
            [arm_report(a) for a in arms],
        )

    reports = [arm_report(a) for a in arms]
    if mode == "greedy":
        best = max(reports, key=lambda r: r["posterior_mean"])  # max() keeps the first on ties
        chosen = best["strategy"]
        reason = "Highest posterior mean rating."
    else:
        for report in reports:
            report["sampled"] = round(rng.betavariate(report["_alpha"], report["_beta"]), 3)
        best = max(reports, key=lambda r: r["sampled"])
        chosen = best["strategy"]
        reason = "Thompson sample over rating posteriors."
    if chosen != base:
        reason += f" {chosen} outscored the default {base}."
    return finish(chosen, mode, reason, reports)
