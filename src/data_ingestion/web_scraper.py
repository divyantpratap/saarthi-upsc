"""
Web scraper for UPSC current affairs and study materials
Supports: insights.ias.in, iasbaba.com, pib.gov.in
"""
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime, timedelta

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import (
    SCRAPING_DELAY, USER_AGENT, REQUEST_TIMEOUT,
    WEB_SOURCES, PROCESSED_DATA_DIR
)


class WebScraper:
    """Web scraper for UPSC content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.output_dir = PROCESSED_DATA_DIR / "web_content"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage"""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            time.sleep(SCRAPING_DELAY)  # Respectful scraping
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def scrape_insights_ias(self, num_articles: int = 50) -> List[Dict]:
        """Scrape Insights on India current affairs"""
        logger.info("Scraping Insights on India...")
        articles = []
        
        try:
            # Main current affairs page
            base_url = WEB_SOURCES["insights_ias"]
            url = f"{base_url}/category/current-affairs/"
            
            soup = self.fetch_page(url)
            if not soup:
                return articles
            
            # Find article links
            article_links = soup.find_all('article', class_='post')[:num_articles]
            
            for article in article_links:
                try:
                    title_elem = article.find('h2', class_='entry-title')
                    if not title_elem:
                        continue
                    
                    link = title_elem.find('a')['href']
                    title = title_elem.get_text(strip=True)
                    
                    # Fetch full article
                    article_soup = self.fetch_page(link)
                    if article_soup:
                        content_div = article_soup.find('div', class_='entry-content')
                        if content_div:
                            content = content_div.get_text(separator='\n', strip=True)
                            
                            articles.append({
                                "title": title,
                                "content": content,
                                "url": link,
                                "source": "Insights on India",
                                "topic": "Current Affairs",
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
                            
                            logger.info(f"✓ Scraped: {title[:50]}...")
                
                except Exception as e:
                    logger.error(f"Error scraping article: {e}")
                    continue
            
            logger.success(f"Scraped {len(articles)} articles from Insights on India")
            
        except Exception as e:
            logger.error(f"Failed to scrape Insights on India: {e}")
        
        return articles
    
    def scrape_iasbaba(self, num_articles: int = 50) -> List[Dict]:
        """Scrape IASbaba daily current affairs"""
        logger.info("Scraping IASbaba...")
        articles = []
        
        try:
            base_url = WEB_SOURCES["iasbaba"]
            url = f"{base_url}/category/daily-current-affairs/"
            
            soup = self.fetch_page(url)
            if not soup:
                return articles
            
            # Find article cards
            article_cards = soup.find_all('div', class_='post-item')[:num_articles]
            
            for card in article_cards:
                try:
                    title_elem = card.find('h3', class_='post-title')
                    if not title_elem:
                        continue
                    
                    link = title_elem.find('a')['href']
                    title = title_elem.get_text(strip=True)
                    
                    # Fetch full article
                    article_soup = self.fetch_page(link)
                    if article_soup:
                        content_div = article_soup.find('div', class_='post-content')
                        if content_div:
                            content = content_div.get_text(separator='\n', strip=True)
                            
                            articles.append({
                                "title": title,
                                "content": content,
                                "url": link,
                                "source": "IASbaba",
                                "topic": "Current Affairs",
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
                            
                            logger.info(f"✓ Scraped: {title[:50]}...")
                
                except Exception as e:
                    logger.error(f"Error scraping article: {e}")
                    continue
            
            logger.success(f"Scraped {len(articles)} articles from IASbaba")

        except Exception as e:
            logger.error(f"Failed to scrape IASbaba: {e}")

        return articles

    def scrape_pib(self, num_articles: int = 50) -> List[Dict]:
        """Scrape PIB (Press Information Bureau) releases"""
        logger.info("Scraping PIB...")
        articles = []

        try:
            base_url = WEB_SOURCES["pib"]
            url = f"{base_url}/allRel.aspx"

            soup = self.fetch_page(url)
            if not soup:
                return articles

            # Find press releases
            release_items = soup.find_all('div', class_='content-area')[:num_articles]

            for item in release_items:
                try:
                    title_elem = item.find('h3')
                    if not title_elem:
                        continue

                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue

                    link = base_url + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    title = title_elem.get_text(strip=True)

                    # Fetch full release
                    release_soup = self.fetch_page(link)
                    if release_soup:
                        content_div = release_soup.find('div', class_='innner-page-main-about-us-content')
                        if content_div:
                            content = content_div.get_text(separator='\n', strip=True)

                            articles.append({
                                "title": title,
                                "content": content,
                                "url": link,
                                "source": "PIB",
                                "topic": "Government Updates",
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })

                            logger.info(f"✓ Scraped: {title[:50]}...")

                except Exception as e:
                    logger.error(f"Error scraping PIB release: {e}")
                    continue

            logger.success(f"Scraped {len(articles)} releases from PIB")

        except Exception as e:
            logger.error(f"Failed to scrape PIB: {e}")

        return articles

    def scrape_all(self, articles_per_source: int = 30) -> List[Dict]:
        """Scrape all configured sources"""
        logger.info("Starting comprehensive web scraping...")

        all_articles = []

        # Scrape each source
        all_articles.extend(self.scrape_insights_ias(articles_per_source))
        all_articles.extend(self.scrape_iasbaba(articles_per_source))
        all_articles.extend(self.scrape_pib(articles_per_source))

        logger.info(f"""
        ╔══════════════════════════════════════╗
        ║     Web Scraping Complete            ║
        ╠══════════════════════════════════════╣
        ║  Total Articles: {len(all_articles):<19} ║
        ╚══════════════════════════════════════╝
        """)

        return all_articles

    def save_articles(self, articles: List[Dict], filename: str = "web_articles.json"):
        """Save scraped articles to JSON"""
        import json

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)

        logger.success(f"Saved {len(articles)} articles to {output_path}")


def main():
    """Test the web scraper"""
    scraper = WebScraper()

    # Scrape all sources
    articles = scraper.scrape_all(articles_per_source=10)  # Start with 10 per source

    if articles:
        scraper.save_articles(articles)

        # Print sample
        print("\n" + "="*50)
        print("SAMPLE ARTICLE:")
        print("="*50)
        sample = articles[0]
        print(f"Title: {sample['title']}")
        print(f"Source: {sample['source']}")
        print(f"Content: {sample['content'][:200]}...")
    else:
        logger.warning("No articles scraped")


if __name__ == "__main__":
    main()

