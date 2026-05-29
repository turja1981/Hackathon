from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Regex fallback patterns (used when Presidio not installed)
_REGEX_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL_ADDRESS":    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    "PHONE_NUMBER":     re.compile(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "US_SSN":           re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "CREDIT_CARD":      re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    "IP_ADDRESS":       re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    "DATE_OF_BIRTH":    re.compile(r'\b(0?[1-9]|1[0-2])[/\-](0?[1-9]|[12]\d|3[01])[/\-](\d{2}|\d{4})\b'),
    "US_PASSPORT":      re.compile(r'\b[A-Z]\d{8}\b'),
}

class PIIService:
    """PII detection and masking.
    Primary: Microsoft Presidio (uses spacy NER when available).
    Fallback: regex-based patterns (no model required).
    """
    def __init__(self):
        self._analyzer = None
        self._anonymizer = None
        self._backend = "uninitialized"  # "presidio" | "regex"
        self._initialized = False

    def _init(self):
        if self._initialized:
            return
        self._initialized = True
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._backend = "presidio"
            logger.info("pii_backend_presidio")
        except Exception as exc:
            self._backend = "regex"
            logger.warning("pii_backend_regex_fallback", error=str(exc))

    def analyze(self, text: str) -> List[Dict]:
        """Return list of {entity_type, start, end, score, text} dicts."""
        self._init()
        if self._backend == "presidio":
            try:
                results = self._analyzer.analyze(text=text, language="en")
                return [
                    {"entity_type": r.entity_type, "start": r.start, "end": r.end,
                     "score": float(r.score), "text": text[r.start:r.end]}
                    for r in results
                ]
            except Exception as exc:
                logger.warning("presidio_analyze_error", error=str(exc))
        # regex fallback
        entities = []
        for etype, pat in _REGEX_PATTERNS.items():
            for m in pat.finditer(text):
                entities.append({"entity_type": etype, "start": m.start(), "end": m.end(),
                                  "score": 0.85, "text": m.group()})
        return sorted(entities, key=lambda x: x["start"])

    def mask(self, text: str) -> Tuple[str, List[Dict]]:
        """Mask PII in text. Returns (masked_text, entities_found)."""
        entities = self.analyze(text)
        if not entities:
            return text, []
        if self._backend == "presidio":
            try:
                results = self._analyzer.analyze(text=text, language="en")
                anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
                return anonymized.text, entities
            except Exception as exc:
                logger.warning("presidio_anonymize_error", error=str(exc))
        # regex mask fallback: replace from right to left to preserve indices
        chars = list(text)
        for ent in sorted(entities, key=lambda x: -x["start"]):
            placeholder = list(f"<{ent['entity_type']}>")
            chars[ent["start"]:ent["end"]] = placeholder
        return "".join(chars), entities

    @property
    def backend(self) -> str:
        self._init()
        return self._backend

pii_service = PIIService()
