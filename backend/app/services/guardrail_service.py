from __future__ import annotations
import re
from typing import Dict, List, Optional
from app.utils.logging import get_logger
from app.services.pii_service import pii_service

logger = get_logger(__name__)

_HARMFUL = [
    re.compile(r'\b(how to (make|build|synthesize) (a )?(weapon|explosive|poison|bomb))\b', re.I),
    re.compile(r'\b(instruction|guide|steps) (to|for) (kill|harm|attack|hurt)\b', re.I),
]
_MEDICAL_CLAIM = re.compile(r'\b(you should|you must|must take|prescrib|diagnos)\b', re.I)
_MEDICAL_DISCLAIMER = re.compile(r'\b(not medical advice|consult (a )?(doctor|physician|healthcare|professional)|seek professional)\b', re.I)
_CITATION_REF = re.compile(r'\b(paper_\w+|pmid_\d+|\[\d+\]|according to|based on the (study|research|paper))\b', re.I)

# Off-topic domain patterns — queries matching these are outside life sciences scope
_OFF_TOPIC_DOMAINS: List[re.Pattern] = [
    re.compile(r'\b(movie|film|cinema|actor|actress|director|hollywood|box office|oscar|emmy)\b', re.I),
    re.compile(r'\b(sport|football|soccer|basketball|cricket|tennis|baseball|nfl|nba|fifa|ipl|premier league)\b', re.I),
    re.compile(r'\b(news|politics|election|politician|president|prime minister|government|parliament|congress|senate)\b', re.I),
    re.compile(r'\b(stock market|cryptocurrency|bitcoin|ethereum|forex|trading|investment|mutual fund)\b', re.I),
    re.compile(r'\b(recipe|cooking|food|restaurant|chef|cuisine|meal|diet plan|weight loss tips)\b', re.I),
    re.compile(r'\b(travel|tourism|hotel|flight|vacation|holiday|destination|visa|passport)\b', re.I),
    re.compile(r'\b(music|song|album|artist|band|concert|spotify|youtube|playlist)\b', re.I),
    re.compile(r'\b(game|gaming|video game|esports|playstation|xbox|nintendo|fortnite|minecraft)\b', re.I),
]

_LIFE_SCI_KEYWORDS = re.compile(
    r'\b(gene|protein|cell|cancer|disease|therapy|drug|clinical|trial|pathogen|virus|bacteria|'
    r'neuron|brain|dna|rna|crispr|mrna|vaccine|immune|tumor|mutation|genomic|biomarker|'
    r'enzyme|receptor|antibody|molecular|biology|chemistry|pharmacology|biochemistry|'
    r'metabolic|cardiovascular|neurodegeneration|oncology|immunotherapy|stem cell|'
    r'microbiome|epigenetic|transcription|sequencing|proteomics|metabolomics|'
    r'hypothesis|research|study|paper|literature|mechanism|pathway|signaling)\b', re.I
)

class GuardrailService:
    """Responsible AI output validation using rule-based checks."""

    def is_on_topic(self, query: str) -> tuple[bool, str]:
        """Return (True, '') if query is life-sciences related, else (False, reason)."""
        for pat in _OFF_TOPIC_DOMAINS:
            m = pat.search(query)
            if m:
                # Allow if it also contains life-sci context (e.g. "cancer diet")
                if _LIFE_SCI_KEYWORDS.search(query):
                    return True, ""
                domain_word = m.group()
                return False, (
                    f"Query appears to be about '{domain_word}', which is outside the life sciences "
                    f"research scope of BioMind AI. Please ask about biology, medicine, genomics, "
                    f"drug development, or related scientific topics."
                )
        return True, ""

    def validate(
        self,
        output: str,
        query: str = "",
        context_paper_ids: Optional[List[str]] = None,
        agent_name: str = "unknown",
    ) -> Dict:
        checks: Dict[str, bool] = {}
        violations: List[str] = []

        # 1. Content safety
        harmful = any(p.search(output) for p in _HARMFUL)
        checks["content_safe"] = not harmful
        if harmful:
            violations.append("Potentially harmful content detected")

        # 2. PII leakage in output
        pii_entities = pii_service.analyze(output)
        checks["no_pii_leakage"] = len(pii_entities) == 0
        if pii_entities:
            types = sorted({e["entity_type"] for e in pii_entities})
            violations.append(f"PII detected in output: {', '.join(types)}")

        # 3. Medical disclaimer
        if _MEDICAL_CLAIM.search(output) and not _MEDICAL_DISCLAIMER.search(output):
            checks["medical_disclaimer"] = False
            violations.append("Medical claim without disclaimer")
        else:
            checks["medical_disclaimer"] = True

        # 4. Citation grounding (when context papers provided)
        if context_paper_ids:
            checks["citation_grounding"] = bool(_CITATION_REF.search(output))
            if not checks["citation_grounding"]:
                violations.append("Response lacks source citations")
        else:
            checks["citation_grounding"] = True

        passed = len(violations) == 0
        return {
            "passed": passed,
            "checks": checks,
            "violations": violations,
            "agent": agent_name,
            "pii_in_output": pii_entities,
            "recommendation": "Approved" if passed else "; ".join(violations),
        }

guardrail_service = GuardrailService()
