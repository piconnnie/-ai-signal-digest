---
name: web-scraping
description: Best practices and patterns for scraping AI news and arXiv papers.
---

# Web Scraping for AI Signal Digest

## Core Libraries
- **Requests**: For HTTP requests.
- **BeautifulSoup4**: For parsing HTML.
- **Arxiv**: Official Python library for arXiv API.

## Content Acquisition Patterns

### 1. arXiv Fetching
Use the `arxiv` library to fetch papers by category.
```python
import arxiv

client = arxiv.Client()
search = arxiv.Search(
    query = "cat:cs.AI OR cat:cs.CL",
    max_results = 100,
    sort_by = arxiv.SortCriterion.SubmittedDate
)

for result in client.results(search):
    print(result.title, result.published, result.pdf_url)
```

### 2. News Scraping
For news sites, use `requests` with a proper User-Agent header.
```python
import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (compatible; AI_Signal_Digest/1.0)'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract title
title = soup.find('h1').text.strip()
# Extract text (simplified)
text = '\n'.join([p.text for p in soup.find_all('p')])
```

## Anti-Blocking
- Respect `robots.txt`.
- Add delays between requests (`time.sleep(1)`).
- Use `fake-useragent` if needed, but prefer identifying your bot.

## Error Handling
- Wrap requests in `try-except` blocks.
- Handle timeouts (`requests.get(..., timeout=10)`).
- Check `response.status_code` before parsing.
