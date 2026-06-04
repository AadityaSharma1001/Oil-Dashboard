"""OilPrice adapter — RSS feed + scraping for oil industry news."""

import httpx
import feedparser
import structlog
from datetime import datetime
from bs4 import BeautifulSoup
from app.adapters.base import DataAdapter, AdapterResult, SourceStatus

logger = structlog.get_logger()

OILPRICE_RSS = "https://oilprice.com/rss/main"
OILPRICE_URL = "https://oilprice.com/Energy/Oil-Prices"

CATEGORY_KEYWORDS = {
    "OPEC": ["opec", "opec+", "saudi", "quota", "cut", "compliance"],
    "Geopolitical": ["iran", "russia", "sanctions", "red sea", "houthi", "war", "conflict"],
    "Demand": ["demand", "consumption", "refinery", "throughput", "imports", "china demand"],
    "Macro": ["fed", "rate", "gdp", "inflation", "dollar", "dxy", "recession", "pmi"],
}


def classify_category(text: str) -> str:
    text_lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return cat
    return "General"


class OilPriceAdapter(DataAdapter):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)

    @property
    def source_name(self) -> str:
        return "oilprice"

    async def fetch(self, params: dict) -> AdapterResult:
        articles = await self._try_rss()
        if not articles:
            articles = await self._try_scrape()
        if not articles:
            return self.get_mock_data(params)

        return AdapterResult(
            data=articles, status=SourceStatus.LIVE, source_name=self.source_name,
        )

    async def _try_rss(self) -> list[dict]:
        try:
            resp = await self.client.get(OILPRICE_RSS)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            articles = []
            for entry in feed.entries[:20]:
                articles.append({
                    "headline": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "category": classify_category(entry.get("title", "")),
                    "source": "oilprice",
                })
            return articles
        except Exception as e:
            logger.warning("oilprice_rss_error", error=str(e))
            return []

    async def _try_scrape(self) -> list[dict]:
        try:
            resp = await self.client.get(OILPRICE_URL)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "lxml")
            articles = []
            for item in soup.select("article, .articleItem, .categoryArticle")[:15]:
                title_el = item.select_one("h2, h3, .article-title, a")
                if title_el:
                    headline = title_el.get_text(strip=True)
                    link = title_el.get("href", "")
                    if headline:
                        articles.append({
                            "headline": headline,
                            "summary": "",
                            "url": link if link.startswith("http") else f"https://oilprice.com{link}",
                            "published_at": datetime.utcnow().isoformat(),
                            "category": classify_category(headline),
                            "source": "oilprice",
                        })
            return articles
        except Exception as e:
            logger.warning("oilprice_scrape_error", error=str(e))
            return []

    async def health_check(self) -> SourceStatus:
        try:
            resp = await self.client.get(OILPRICE_RSS)
            return SourceStatus.LIVE if resp.status_code == 200 else SourceStatus.DOWN
        except Exception:
            return SourceStatus.DOWN

    def get_mock_data(self, params: dict) -> AdapterResult:
        return AdapterResult(
            data=[
                {"headline": "OPEC+ considers extending voluntary cuts through Q3 2026", "category": "OPEC", "source": "oilprice", "published_at": datetime.utcnow().isoformat(), "url": "", "summary": ""},
                {"headline": "US crude inventories fall by 6.1mb — largest draw in 8 weeks", "category": "Demand", "source": "oilprice", "published_at": datetime.utcnow().isoformat(), "url": "", "summary": ""},
                {"headline": "Red Sea shipping disruptions widen Brent-Dubai EFS", "category": "Geopolitical", "source": "oilprice", "published_at": datetime.utcnow().isoformat(), "url": "", "summary": ""},
                {"headline": "China May refinery throughput drops 3.2% YoY", "category": "Demand", "source": "oilprice", "published_at": datetime.utcnow().isoformat(), "url": "", "summary": ""},
                {"headline": "Fed officials signal potential rate hold", "category": "Macro", "source": "oilprice", "published_at": datetime.utcnow().isoformat(), "url": "", "summary": ""},
            ],
            status=SourceStatus.MOCK, source_name=self.source_name,
            error_message="OilPrice feed unavailable — returning mock headlines",
        )
