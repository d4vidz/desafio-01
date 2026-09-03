"""Shared, auditable narrative components for the Marimo notebooks.

The component makes explanatory context part of the same change as a chart or
table.  It intentionally keeps the information required to interpret an
output in the static document; accordions contain only optional detail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class EvidenceStatus(StrEnum):
    """Maturity of a notebook result; it is not a measure of effect strength."""

    INFRASTRUCTURE = "infraestrutura"
    PROTOTYPE = "protótipo"
    COMPLETE_EXPERIMENT = "experimento_completo"
    VALIDATED_EVIDENCE = "evidência_validada"


@dataclass(frozen=True)
class NarrativeSection:
    """Required communication contract for one primary analytical output."""

    title: str
    question: str
    population: str
    unit: str
    method: str
    how_to_read: str
    denominator: str
    result: str
    interpretation: str
    use: str
    limitation: str
    status: EvidenceStatus
    terms: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = (
            "title",
            "question",
            "population",
            "unit",
            "method",
            "how_to_read",
            "denominator",
            "result",
            "interpretation",
            "use",
            "limitation",
        )
        missing = [name for name in required if not getattr(self, name).strip()]
        if missing:
            raise ValueError(f"NarrativeSection fields cannot be empty: {', '.join(missing)}")
        if not isinstance(self.terms, Mapping):
            raise TypeError("NarrativeSection.terms must map each term to its contextual definition")


def render_narrative_section(mo: Any, section: NarrativeSection) -> Any:
    """Render the required narrative plus optional progressive detail."""

    kind = {
        EvidenceStatus.INFRASTRUCTURE: "info",
        EvidenceStatus.PROTOTYPE: "warn",
        EvidenceStatus.COMPLETE_EXPERIMENT: "neutral",
        EvidenceStatus.VALIDATED_EVIDENCE: "success",
    }[section.status]
    overview = mo.md(
        f"""
### {section.title}

**Pergunta.** {section.question}

**População e unidade.** {section.population} Cada observação representa {section.unit}.

**Método.** {section.method}

**Como ler.** {section.how_to_read}

**Amostra/denominador.** {section.denominator}
"""
    )
    finding = mo.callout(
        mo.md(
            f"""
**Resultado desta execução.** {section.result}

**Interpretação.** {section.interpretation}
"""
        ),
        kind=kind,
        title=f"Status: {section.status.value.replace('_', ' ')}",
    )
    boundary = mo.md(
        f"""
**Como isto será usado.** {section.use}

**Limite.** {section.limitation}
"""
    )
    items = [overview, finding, boundary]
    if section.terms:
        detail = "\n\n".join(f"**{term}.** {definition}" for term, definition in section.terms.items())
        items.append(mo.accordion({"Termos desta seção": mo.md(detail)}))
    return mo.vstack(items)
