"""PersonalProfileAgent — evaluates whether the user's answer expresses their profile.

Dimensions (each 0–100):
- profile_coverage    — does answer mention profile-relevant experiences/goals
- evidence_density    — does answer include examples, data, project details
- agency              — does answer explain what the user personally did
- original_thinking   — does answer include judgment, trade-off, opinion
- position_fit        — does answer connect to the current scene or target role
- self_expression_score — weighted composite

Also outputs:
- expressed_traits    — traits detected in the answer
- missing_traits      — profile traits not expressed
- if_i_were_you       — a personalized model answer
"""

import json
from .schemas import ProfileOutput, EvalContext


class PersonalProfileAgent:

    # ── Profile coverage ─────────────────────────────────────
    def _profile_coverage(self, text: str, profile: dict[str, str]) -> tuple[float, list[str], list[str]]:
        """Check which profile traits appear in the answer."""
        expressed: list[str] = []
        missing: list[str] = []
        keywords: list[str] = []

        # Extract keywords from profile fields
        for field in ("identity", "experiences", "strengths", "target_role"):
            raw = profile.get(field, "") or ""
            # Try JSON list first, then plain text
            try:
                items = json.loads(raw) if raw else []
                if isinstance(items, list):
                    keywords.extend(items)
                else:
                    keywords.append(str(items))
            except (json.JSONDecodeError, TypeError):
                keywords.extend(raw.split(","))

        keywords = [k.strip().lower() for k in keywords if k.strip() and len(k.strip()) > 2]
        text_lower = text.lower()

        for kw in keywords:
            if kw in text_lower:
                expressed.append(kw)
            else:
                missing.append(kw)

        if not keywords:
            return 50.0, ["(no profile set)"], []

        score = (len(expressed) / len(keywords)) * 100.0 if keywords else 50.0
        return round(score, 1), expressed, missing

    # ── Evidence density ─────────────────────────────────────
    def _evidence_density(self, text: str) -> tuple[float, str]:
        """Check for examples, data, project details."""
        indicators = [
            "example", "instance", "specifically", "for instance",
            "project", "built", "created", "launched", "led", "managed",
            "data", "percent", "%", "users", "customers", "revenue",
            "result", "outcome", "impact", "improved", "increased", "reduced",
            "learned", "shipped", "deployed", "designed", "implemented",
        ]
        text_lower = text.lower()
        found = [w for w in indicators if w in text_lower]
        density = len(found)

        if density >= 5:
            return 95.0, f"Rich with {density} evidence indicators (examples, data, actions)."
        elif density >= 3:
            return 75.0, f"Good — {density} evidence indicators found."
        elif density >= 1:
            return 50.0, f"Light — only {density} evidence indicator(s). Add examples or data."
        else:
            return 20.0, "No evidence indicators — add concrete examples, data, or project details."

    # ── Agency ───────────────────────────────────────────────
    def _agency(self, text: str) -> tuple[float, str]:
        """Check if the user describes what THEY personally did."""
        agentive = [
            "i built", "i created", "i led", "i managed", "i designed",
            "i implemented", "i launched", "i wrote", "i developed",
            "i solved", "i improved", "i decided", "i proposed", "i drove",
            "my role was", "i was responsible", "i took", "i handled",
            "i coordinated", "i delivered",
        ]
        passive = [
            "we built", "the team", "they decided", "it was done",
            "someone else", "i was told", "i had to",
        ]
        text_lower = text.lower()
        agent_count = sum(1 for w in agentive if w in text_lower)
        pass_count = sum(1 for w in passive if w in text_lower)

        if agent_count >= 3:
            return 95.0, "Strong personal agency — clearly describes your own actions."
        elif agent_count >= 1:
            return 70.0, "Some agency shown. Use more 'I did X' language."
        elif pass_count >= 2:
            return 30.0, "Answer leans passive. Use 'I built/led/designed' to show your role."
        else:
            return 50.0, "Unclear agency — be explicit about what YOU did."

    # ── Original thinking ────────────────────────────────────
    def _original_thinking(self, text: str) -> tuple[float, str]:
        """Check for judgment, trade-offs, opinions."""
        signals = [
            "trade-off", "tradeoff", "however", "on the other hand",
            "i believe", "in my opinion", "i think", "i realized",
            "lesson", "i learned", "surprisingly", "unexpectedly",
            "challenging", "difficult because", "i chose", "i decided",
            "prioritized", "balanced", "compared", "evaluated",
        ]
        text_lower = text.lower()
        found = [w for w in signals if w in text_lower]

        if len(found) >= 3:
            return 90.0, "Shows original thinking — judgment, trade-offs, and reflection."
        elif len(found) >= 1:
            return 60.0, "Some original thinking. Share more opinions and trade-offs."
        else:
            return 25.0, "Mostly factual. Add your judgment: what did you learn? What would you do differently?"

    # ── Position fit ─────────────────────────────────────────
    def _position_fit(self, text: str, ctx: EvalContext, profile: dict[str, str]) -> tuple[float, str]:
        """Check if the answer connects to the scene or target role."""
        target = (profile.get("target_role") or "").lower()
        scene = ctx.scene_type.lower()
        goal = ctx.task_goal.lower()
        text_lower = text.lower()

        score = 50.0
        reasons: list[str] = []

        # Check target role relevance
        if target and any(kw in text_lower for kw in target.split() if len(kw) > 2):
            score += 20.0
            reasons.append("mentions target role")

        # Check scene alignment
        scene_keywords = {
            "interview": ["role", "position", "team", "company", "skills", "experience", "job"],
            "pitch": ["market", "customer", "product", "solution", "growth", "revenue"],
            "meeting": ["status", "update", "blocker", "timeline", "deliverable", "next steps"],
            "restaurant": ["order", "menu", "special", "dish", "drink", "check"],
        }
        if scene in scene_keywords:
            matches = [w for w in scene_keywords[scene] if w in text_lower]
            if matches:
                score += min(20.0, len(matches) * 5.0)
                reasons.append(f"scene-relevant ({len(matches)} keywords)")

        # Check task goal alignment
        goal_words = [w for w in goal.split() if len(w) > 3]
        if goal_words:
            matches = [w for w in goal_words if w in text_lower]
            if matches:
                score += min(10.0, len(matches) * 5.0)

        score = min(100.0, score)
        reason = "; ".join(reasons) if reasons else "Could connect more to the scene context."
        return round(score, 1), reason

    # ── If I were you ────────────────────────────────────────
    def _if_i_were_you(self, text: str, ctx: EvalContext, profile: dict[str, str], missing: list[str]) -> str:
        """Generate a personalized model answer snippet."""
        target = profile.get("target_role", "professional")
        strengths_str = profile.get("strengths", "")
        experiences_str = profile.get("experiences", "")

        # Build a tailored suggestion
        parts: list[str] = []

        if missing:
            parts.append(f"I'd mention your {missing[0]} experience.")
        if "agency" not in text.lower():
            parts.append("I'd use 'I led' or 'I built' to show personal ownership.")
        if len(text.split()) < 10:
            parts.append("I'd elaborate with a concrete example or data point.")
        if target and target not in text.lower():
            parts.append(f"I'd connect this to your {target} role.")

        if not parts:
            parts.append("I'd add a specific project detail and explain what I personally learned.")

        return "Here's how I'd approach it: " + " ".join(parts)

    # ── Main evaluate ────────────────────────────────────────
    def evaluate(self, ctx: EvalContext, profile: dict[str, str] | None = None) -> ProfileOutput:
        """Run all profile evaluation dimensions."""
        if profile is None:
            profile = {}

        text = ctx.user_message

        cov_score, expressed, missing = self._profile_coverage(text, profile)
        ev_score, ev_note = self._evidence_density(text)
        ag_score, ag_note = self._agency(text)
        ot_score, ot_note = self._original_thinking(text)
        pf_score, pf_note = self._position_fit(text, ctx, profile)

        # Weighted composite
        self_expr = round(
            cov_score * 0.25 + ev_score * 0.25 + ag_score * 0.20 + ot_score * 0.15 + pf_score * 0.15,
            1,
        )

        patterns = [
            f"Profile coverage: {cov_score}/100",
            f"Evidence density: {ev_score}/100 — {ev_note}",
            f"Agency: {ag_score}/100 — {ag_note}",
            f"Original thinking: {ot_score}/100 — {ot_note}",
            f"Position fit: {pf_score}/100 — {pf_note}",
        ]

        return ProfileOutput(
            self_expression_score=self_expr,
            profile_coverage=cov_score,
            evidence_density=ev_score,
            agency=ag_score,
            original_thinking=ot_score,
            position_fit=pf_score,
            expressed_traits=expressed,
            missing_traits=missing,
            if_i_were_you=self._if_i_were_you(text, ctx, profile, missing),
            patterns=patterns,
            strengths=[f"Expressed: {', '.join(expressed)}"] if expressed else ["No profile traits expressed yet."],
            weaknesses=[f"Missing: {', '.join(missing)}"] if missing else [],
            suggestion=self._if_i_were_you(text, ctx, profile, missing),
        )
