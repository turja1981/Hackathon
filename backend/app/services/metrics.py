from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AdoptionCounter:
    papers_processed: int = 0
    hypotheses_generated: int = 0
    gaps_identified: int = 0
    queries_total: int = 0


adoption_counter = AdoptionCounter()
