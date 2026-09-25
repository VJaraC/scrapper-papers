from datetime import date


def decide_paper(paper: dict) -> dict:
    """Decide paper inclusion using explicit metadata rules."""
    current_year = date.today().year
    year_limit = current_year - 5
    expanded_scope = paper.get("categoria") in {
        "MAS-DESPACHO-MINERO",
        "MAS-DESPACHO-MINERO-LLM",
    }
    is_preprint = paper.get("is_preprint") is True
    preprint_exclusion_applies = is_preprint and not expanded_scope
    year = paper.get("year")
    is_too_old = year is not None and year < year_limit
    mas_is_false = paper.get("mas") is False
    mas_exclusion_applies = mas_is_false and not expanded_scope

    relevance_score = sum(
        paper.get(axis) is True
        for axis in ("mas", "scheduling", "llm", "mineria")
    )

    pending_reasons = []
    conference_pending_applies = (
        paper.get("venue_type") == "conference" and not expanded_scope
    )
    if conference_pending_applies:
        pending_reasons.append("venue_type=conference")
    if paper.get("mas") is None:
        pending_reasons.append("mas=None")
    if paper.get("categoria") == "NO_CLASIFICABLE":
        pending_reasons.append("categoria=NO_CLASIFICABLE")
    if year is None:
        pending_reasons.append("year=None")

    if preprint_exclusion_applies or is_too_old or mas_exclusion_applies:
        decision = "excluido"
        exclusion_reasons = []
        if preprint_exclusion_applies:
            exclusion_reasons.append("is_preprint=True")
        if is_too_old:
            exclusion_reasons.append(f"year={year} < {year_limit}")
        if mas_exclusion_applies:
            exclusion_reasons.append("mas=False")
        conclusion = "excluido por " + ", ".join(exclusion_reasons)
    elif pending_reasons:
        decision = "pendiente"
        conclusion = "pendiente por " + ", ".join(pending_reasons)
    else:
        decision = "incluido"
        conclusion = "incluido: no se activaron criterios de exclusión o pendiente"

    omitted_reasons = []
    if expanded_scope and is_preprint:
        omitted_reasons.append(
            "se omitio exclusion por is_preprint=True por categoria de alcance ampliado"
        )
    if expanded_scope and paper.get("venue_type") == "conference":
        omitted_reasons.append(
            "se omitio pendiente por venue_type=conference por categoria de alcance ampliado"
        )
    if expanded_scope and mas_is_false:
        omitted_reasons.append(
            "se omitio exclusion por mas=False por categoria de alcance ampliado"
        )

    justification = "; ".join(
        [
            f"preprint={'si' if is_preprint else 'no'}",
            f"antiguedad={'excede el limite' if is_too_old else 'dentro del limite o sin año'}",
            f"mas={'true' if paper.get('mas') is True else 'false' if mas_is_false else 'none'}",
            f"venue_type={paper.get('venue_type')!r}",
            f"categoria={paper.get('categoria')!r}",
            f"year={year!r}",
            *omitted_reasons,
            conclusion,
        ]
    )

    return {
        "relevance_score": relevance_score,
        "decision": decision,
        "justification": justification,
    }