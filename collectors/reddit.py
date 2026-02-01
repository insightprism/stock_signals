"""Reddit collector using PRAW + VADER sentiment analysis."""

import logging
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from collectors.base import BaseCollector
from config.drivers import DRIVER_KEYWORDS
from config.settings import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_POST_LIMIT,
    REDDIT_SUBREDDITS,
    REDDIT_USER_AGENT,
)

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self):
        super().__init__()
        self._reddit = None

    def _get_reddit(self):
        """Lazy-init PRAW Reddit instance."""
        if self._reddit is not None:
            return self._reddit
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not set")
            return None
        try:
            import praw
            self._reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
            )
            return self._reddit
        except Exception as e:
            logger.error("PRAW init failed: %s", e)
            return None

    def _fetch_posts(self, subreddit_name: str,
                      limit: int = REDDIT_POST_LIMIT) -> List[dict]:
        """Fetch recent posts from a subreddit."""
        reddit = self._get_reddit()
        if reddit is None:
            return []
        try:
            sub = reddit.subreddit(subreddit_name)
            posts = []
            for post in sub.new(limit=limit):
                posts.append({
                    "title": post.title,
                    "selftext": post.selftext or "",
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": datetime.fromtimestamp(
                        post.created_utc, tz=timezone.utc
                    ),
                })
            return posts
        except Exception as e:
            logger.error("Reddit fetch %s failed: %s", subreddit_name, e)
            return []

    def _analyze_sentiment(self, texts: List[str]) -> Optional[float]:
        """Compute average VADER sentiment for a list of texts."""
        try:
            from processors.sentiment_nlp import analyze_sentiment_batch
            return analyze_sentiment_batch(texts)
        except Exception as e:
            logger.error("Sentiment analysis failed: %s", e)
            return None

    def _filter_by_keywords(self, posts: List[dict],
                             keywords: List[str]) -> List[dict]:
        """Filter posts matching any of the keywords."""
        kw_lower = [k.lower() for k in keywords]
        matched = []
        for post in posts:
            text = f"{post['title']} {post['selftext']}".lower()
            if any(kw in text for kw in kw_lower):
                matched.append(post)
        return matched

    def collect(self, target_date: date, drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}

        reddit = self._get_reddit()
        if reddit is None:
            return results

        # Collect posts from all configured subreddits
        all_posts = []
        for sub_name in REDDIT_SUBREDDITS:
            posts = self._fetch_posts(sub_name)
            all_posts.extend(posts)
            logger.info("Reddit r/%s: fetched %d posts", sub_name, len(posts))

        if not all_posts:
            return results

        # For each driver, filter posts by keywords and compute sentiment
        for driver, keywords in DRIVER_KEYWORDS.items():
            if drivers and driver not in drivers:
                continue
            if driver == "spec_positioning":
                continue

            matched = self._filter_by_keywords(all_posts, keywords)
            if not matched:
                continue

            texts = [f"{p['title']}. {p['selftext']}" for p in matched]
            avg_sentiment = self._analyze_sentiment(texts)
            if avg_sentiment is None:
                continue

            # Also compute buzz volume (number of matching posts)
            buzz_volume = len(matched)

            signals = [{
                "source": "reddit_vader",
                "series_name": f"{driver}_reddit_sentiment",
                "raw_value": avg_sentiment,
                "metadata": {
                    "matched_posts": buzz_volume,
                    "total_posts_scanned": len(all_posts),
                    "invert": False,
                },
            }]

            # Buzz volume as separate signal for investment_demand
            if driver == "investment_demand":
                signals.append({
                    "source": "reddit_vader",
                    "series_name": f"{driver}_reddit_buzz",
                    "raw_value": float(buzz_volume),
                    "metadata": {"invert": False},
                })

            results[driver] = signals
            logger.info("Reddit %s: sentiment=%.3f from %d posts",
                        driver, avg_sentiment, buzz_volume)

        return results
