from __future__ import annotations

from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import httpx

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedService:
    """Fetches papers from PubMed via NCBI E-utilities API.

    Flow: esearch → get PMIDs → efetch → parse XML → structured paper dicts
    Papers are identified as pmid_{pmid} to avoid clashing with static data.
    """

    def _base_params(self) -> dict:
        p: dict = {"db": "pubmed"}
        if settings.PUBMED_API_KEY:
            p["api_key"] = settings.PUBMED_API_KEY
        return p

    async def search(self, query: str, max_results: int | None = None) -> List[Dict]:
        """Search PubMed and return structured paper dicts ready for vector store."""
        if not settings.PUBMED_ENABLED:
            return []

        n = max_results or settings.PUBMED_MAX_RESULTS

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                verify=not settings.DISABLE_SSL_VERIFY,
            ) as client:
                pmids = await self._esearch(client, query, n)
                if not pmids:
                    logger.info("pubmed_no_results", query=query[:80])
                    return []

                papers = await self._efetch(client, pmids)
                logger.info("pubmed_fetched", query=query[:80], count=len(papers))
                return papers

        except Exception as exc:
            logger.warning("pubmed_fetch_failed", query=query[:80], error=str(exc))
            return []

    async def _esearch(
        self, client: httpx.AsyncClient, query: str, max_results: int
    ) -> List[str]:
        params = {
            **self._base_params(),
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        resp = await client.get(f"{_NCBI_BASE}/esearch.fcgi", params=params)
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])

    async def _efetch(
        self, client: httpx.AsyncClient, pmids: List[str]
    ) -> List[Dict]:
        params = {
            **self._base_params(),
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        resp = await client.get(f"{_NCBI_BASE}/efetch.fcgi", params=params)
        resp.raise_for_status()
        return self._parse_articles(resp.text)

    def _parse_articles(self, xml_text: str) -> List[Dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.error("pubmed_xml_parse_error", error=str(exc))
            return []

        papers = []
        for elem in root.findall(".//PubmedArticle"):
            try:
                paper = self._extract(elem)
                if paper:
                    papers.append(paper)
            except Exception as exc:
                logger.warning("pubmed_article_skipped", error=str(exc))
        return papers

    def _extract(self, article: ET.Element) -> Optional[Dict]:
        pmid = article.findtext(".//PMID") or ""
        if not pmid:
            return None

        # Title — itertext() handles italic/bold markup tags
        title_elem = article.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""

        # Abstract — may have multiple labeled sections
        parts: List[str] = []
        for at in article.findall(".//AbstractText"):
            text = "".join(at.itertext()).strip()
            if text:
                label = at.get("Label")
                parts.append(f"{label}: {text}" if label else text)
        abstract = " ".join(parts)

        # Authors
        authors: List[str] = []
        for author in article.findall(".//Author"):
            lastname = author.findtext("LastName") or ""
            forename = author.findtext("ForeName") or ""
            collective = author.findtext("CollectiveName") or ""
            if lastname:
                authors.append(f"{lastname}, {forename}".strip(", "))
            elif collective:
                authors.append(collective)

        # Journal
        journal = (
            article.findtext(".//Journal/Title")
            or article.findtext(".//MedlineTA")
            or ""
        )

        # Year — PubDate can be Year/Month/Day or a free-text MedlineDate
        year_raw = (
            article.findtext(".//PubDate/Year")
            or (article.findtext(".//MedlineDate") or "2024")[:4]
        )
        try:
            year = int(year_raw)
        except ValueError:
            year = 2024

        # DOI
        doi = ""
        for eid in article.findall(".//ELocationID"):
            if eid.get("EIdType") == "doi":
                doi = eid.text or ""
                break

        # Keywords → fall back to MeSH headings
        keywords: List[str] = [
            kw.text for kw in article.findall(".//Keyword") if kw.text
        ]
        if not keywords:
            keywords = [
                mh.findtext("DescriptorName") or ""
                for mh in article.findall(".//MeshHeading")
            ]
        keywords = [k for k in keywords if k][:15]

        return {
            "id": f"pmid_{pmid}",
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "journal": journal,
            "year": year,
            "doi": doi,
            "abstract": abstract,
            "keywords": keywords,
            "publication_date": f"{year}-01-01",
            "source": "pubmed",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }


pubmed_service = PubMedService()
