import time
import arxiv
import requests
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from src.core.database import get_db, SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent

class ContentAcquisitionAgent(BaseAgent):
    """
    Fetches content from configured sources (arXiv, News) and stores 'RawContent' in DB.
    Deduplicates based on URL.
    """
    
    ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "stat.ML"]
    
    def _execute(self):
        """
        Main execution flow:
        1. Fetch X latest papers from arXiv.
        2. (Future) Fetch news.
        3. Deduplicate and store.
        """
        self.logger.info("Starting Content Acquisition...")
        
        # Using a fresh session for this execution
        with SessionLocal() as db:
            new_count = 0
            
            # --- 1. Fetch arXiv ---
            try:
                arxiv_papers = self.fetch_arxiv()
                for paper in arxiv_papers:
                    if self.save_content(db, paper):
                        new_count += 1
            except Exception as e:
                self.logger.error(f"Failed to fetch arXiv: {e}")
            
            # --- 2. Fetch News (Placeholder for now) ---
            # news_items = self.fetch_news()
            # for item in news_items:
            #     if self.save_content(db, item):
            #         new_count += 1

            db.commit()
            self.logger.info(f"Acquisition complete. Saved {new_count} new items.")
            return new_count

    def fetch_arxiv(self, max_results=20) -> List[dict]:
        """
        Fetch latest papers from arXiv.
        """
        query = " OR ".join([f"cat:{cat}" for cat in self.ARXIV_CATEGORIES])
        
        # Sort by SubmittedDate (newest first)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        results = []
        client = arxiv.Client()
        
        for result in client.results(search):
            # Check if published in last 24h? Or just rely on DB dedup? 
            # Rely on DB dedup for simplicity + "fetching content newer than last run" logic 
            # is implicitly handled by "max_results" + deduplication.
            
            results.append({
                "source": "arxiv",
                "type": "research",
                "title": result.title,
                "url": result.pdf_url, # Or result.entry_id
                "published_at": result.published,
                "abstract_or_body": result.summary,
                "authors": [a.name for a in result.authors]
            })
        
        return results

    def save_content(self, db: Session, item: dict) -> bool:
        """
        Save content to DB if URL doesn't exist.
        Returns True if saved, False if duplicate.
        """
        exists = db.query(Content).filter(Content.url == item["url"]).first()
        if exists:
            self.logger.debug(f"Duplicate content skipped: {item['url']}")
            return False
        
        new_content = Content(
            source=item["source"],
            type=item["type"],
            title=item["title"],
            url=item["url"],
            published_at=item["published_at"],
            abstract_or_body=item["abstract_or_body"],
            authors=item["authors"],
            # Initialize other fields
            fetched_at=datetime.utcnow()
        )
        db.add(new_content)
        return True

if __name__ == "__main__":
    # Test run
    agent = ContentAcquisitionAgent("test_acquisition")
    agent.run()
