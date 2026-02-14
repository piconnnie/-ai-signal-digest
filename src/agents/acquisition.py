import time
import arxiv
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from src.core.database import get_db, SessionLocal
from src.core.models import Content
from src.agents.base import BaseAgent

class ContentAcquisitionAgent(BaseAgent):
    """
    Fetches content from configured sources (arXiv, RSS Feeds) and stores 'RawContent' in DB.
    Deduplicates based on URL.
    """
    
    ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "stat.ML"]
    
    # High-signal engineering blogs
    RSS_FEEDS = [
        {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "type": "blog"},
        {"name": "Anthropic Blog", "url": "https://www.anthropic.com/index.xml", "type": "blog"},
        {"name": "Google AI Blog", "url": "http://googleaiblog.blogspot.com/atom.xml", "type": "blog"},
        {"name": "AWS Machine Learning", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "type": "blog"},
        {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss.xml", "type": "blog"},
        {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "type": "blog"},
    ]
    
    def _execute(self):
        """
        Main execution flow:
        1. Fetch X latest papers from arXiv.
        2. Fetch latest posts from RSS feeds.
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
            
            # --- 2. Fetch RSS Feeds ---
            try:
                rss_items = self.fetch_rss_feeds()
                for item in rss_items:
                    if self.save_content(db, item):
                        new_count += 1
            except Exception as e:
                self.logger.error(f"Failed to fetch RSS feeds: {e}")

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
            results.append({
                "source": "arxiv",
                "type": "research",
                "title": result.title,
                "url": result.pdf_url, # Prioritize PDF
                "published_at": result.published,
                "abstract_or_body": result.summary,
                "authors": [a.name for a in result.authors]
            })
        
        return results

    def fetch_rss_feeds(self) -> List[dict]:
        """
        Fetch items from configured RSS feeds.
        """
        results = []
        for feed_config in self.RSS_FEEDS:
            try:
                self.logger.info(f"Fetching RSS: {feed_config['name']}")
                feed = feedparser.parse(feed_config['url'])
                
                # Check for bozo error (malformed feed)
                if feed.bozo:
                    self.logger.warning(f"Malformated feed {feed_config['name']}: {feed.bozo_exception}")
                    # Continue anyway as feedparser often parses partially valid feeds

                # Process entries (limit to 5 per feed to avoid spamming)
                for entry in feed.entries[:5]: 
                    
                    # Parse Date
                    published_at = datetime.utcnow()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                         published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                         published_at = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                    
                    # Extract Summary
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = entry.summary
                    elif hasattr(entry, 'description'):
                        summary = entry.description
                    elif hasattr(entry, 'content'):
                        # Atom feeds often have content list
                        summary = entry.content[0].value
                    
                    # Extract Author
                    author = "Unknown"
                    if hasattr(entry, 'author'):
                        author = entry.author
                    
                    results.append({
                        "source": feed_config['name'],
                        "type": feed_config['type'],
                        "title": entry.title,
                        "url": entry.link,
                        "published_at": published_at,
                        "abstract_or_body": summary,
                        "authors": [author] # Adapter for schema
                    })
                    
            except Exception as e:
                self.logger.error(f"Error fetching {feed_config['name']}: {e}")
                
        return results

    def save_content(self, db: Session, item: dict) -> bool:
        """
        Save content to DB if URL doesn't exist.
        Returns True if saved, False if duplicate.
        """
        exists = db.query(Content).filter(Content.url == item["url"]).first()
        if exists:
            # self.logger.debug(f"Duplicate content skipped: {item['url']}")
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
