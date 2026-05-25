# { "Seq": [] }
# sentiment_tracker.py
# GenLayer Intelligent Contract — AI-powered Sentiment Tracker
#
# This contract lets anyone submit a topic (e.g. "Bitcoin", "Nigeria economy",
# "OpenAI GPT-5") and have the LLM analyze current public sentiment by fetching
# live web content. Results are stored on-chain with full history.
#
# Features used:
#   - gl.vm.run_nondet_unsafe()         → custom consensus validator
#   - gl.nondet.web.render()            → live web data access
#   - gl.nondet.exec_prompt()           → LLM sentiment analysis
#   - DynArray / TreeMap storage        → on-chain history per topic

from genlayer import *
from dataclasses import dataclass


# ─────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────

@allow_storage
@dataclass
class SentimentEntry:
    """A single sentiment analysis result."""
    topic: str
    sentiment: str        # "positive" | "negative" | "neutral" | "mixed"
    score: u256           # 0-100 (0=very negative, 50=neutral, 100=very positive)
    summary: str          # 1-sentence AI summary
    source_url: str       # URL that was analyzed
    submitted_by: str     # wallet address of requester
    timestamp: u256       # block timestamp


# ─────────────────────────────────────────────
# Main Contract
# ─────────────────────────────────────────────

class SentimentTracker(gl.Contract):
    """
    On-chain AI Sentiment Tracker.

    Anyone can:
      - submit a topic + URL for real-time sentiment analysis
      - query the current sentiment for any topic
      - read the full history of analyses per topic
      - get aggregated stats (avg score, total analyses)
    """

    # topic_name -> list of SentimentEntry
    history: TreeMap[str, DynArray[SentimentEntry]]

    # topic_name -> latest SentimentEntry index
    latest_index: TreeMap[str, u256]

    # total number of analyses run
    total_analyses: u256

    def __init__(self) -> None:
        self.total_analyses = u256(0)

    # ─────────────────────────────────────────
    # WRITE: Analyze sentiment for a topic
    # ─────────────────────────────────────────

    @gl.public.write
    def analyze(self, topic: str, source_url: str) -> None:
        """
        Fetch live content from source_url and ask the LLM to analyze
        sentiment about `topic`. Result is stored on-chain.

        Args:
            topic:      The subject to analyze (e.g. "Bitcoin", "AI regulation")
            source_url: A URL with content relevant to the topic
        """

        def leader_fn() -> dict:
            # 1. Fetch live web content
            page_content = gl.nondet.web.render(source_url, mode="text")
            page_content = page_content[:4000] if len(page_content) > 4000 else page_content

            # 2. Classify sentiment
            classification_prompt = (
                f"You are a professional sentiment analyst. Read the following web content "
                f"and analyze the public sentiment about \"{topic}\".\n\n"
                f"Web content:\n---\n{page_content}\n---\n\n"
                f"Based ONLY on the content above, classify the sentiment about \"{topic}\" as one of:\n"
                f"- positive\n- negative\n- neutral\n- mixed\n\n"
                f"Respond with ONLY one of these four words. No explanation. No punctuation."
            )

            sentiment = gl.nondet.exec_prompt(classification_prompt).strip().lower()
            valid_sentiments = {"positive", "negative", "neutral", "mixed"}
            if sentiment not in valid_sentiments:
                sentiment = "neutral"

            # 3. Score (0-100)
            score_prompt = (
                f"You are a sentiment scoring model. Based on this content about \"{topic}\":\n"
                f"---\n{page_content}\n---\n\n"
                f"Give a single integer score from 0 to 100 where:\n"
                f"  0 = extremely negative\n  50 = neutral\n  100 = extremely positive\n\n"
                f"Respond with ONLY the integer. No words, no explanation."
            )

            score_str = gl.nondet.exec_prompt(score_prompt).strip()
            try:
                score_int = max(0, min(100, int(score_str)))
            except ValueError:
                score_int = 50

            # 4. One-sentence summary
            summary_prompt = (
                f"In exactly one sentence, summarize the sentiment about \"{topic}\" based on this content:\n"
                f"---\n{page_content}\n---\n\n"
                f"Write the sentence directly. No quotes, no preamble."
            )
            summary = gl.nondet.exec_prompt(summary_prompt).strip()

            return {"sentiment": sentiment, "score": score_int, "summary": summary}

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                try:
                    leader_fn()
                    return False  # leader errored but validator succeeded — disagree
                except Exception:
                    return True   # both errored — agree on failure

            validator_result = leader_fn()
            leader_sentiment = leaders_res.calldata.get("sentiment", "")
            validator_sentiment = validator_result.get("sentiment", "")

            # Sentiment label must match exactly
            if leader_sentiment != validator_sentiment:
                return False

            # Score must be within +-20 points
            leader_score = leaders_res.calldata.get("score", 50)
            validator_score = validator_result.get("score", 50)
            if abs(leader_score - validator_score) > 20:
                return False

            return True

        data = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        sentiment = data["sentiment"]
        score = u256(data["score"])
        summary = data["summary"]

        # Parse block datetime into Unix timestamp (pure math — no restricted stdlib imports)
        dt_str = gl.message_raw['datetime']
        year   = int(dt_str[0:4])
        month  = int(dt_str[5:7])
        day    = int(dt_str[8:10])
        hour   = int(dt_str[11:13])
        minute = int(dt_str[14:16])
        second = int(dt_str[17:19])

        days_in_months = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        days = 0
        for y in range(1970, year):
            if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0):
                days += 366
            else:
                days += 365
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if is_leap:
            days_in_months[2] = 29
        for m in range(1, month):
            days += days_in_months[m]
        days += (day - 1)
        tx_timestamp = days * 86400 + hour * 3600 + minute * 60 + second

        # Build and store entry on-chain
        entry = SentimentEntry(
            topic=topic,
            sentiment=sentiment,
            score=score,
            summary=summary,
            source_url=source_url,
            submitted_by=str(gl.message.sender_address),
            timestamp=u256(tx_timestamp),
        )

        if topic not in self.history:
            self.history[topic] = []

        self.history[topic].append(entry)
        self.latest_index[topic] = u256(len(self.history[topic]) - 1)
        self.total_analyses = u256(int(self.total_analyses) + 1)

    # ─────────────────────────────────────────
    # READ: Latest sentiment for a topic
    # ─────────────────────────────────────────

    @gl.public.view
    def get_latest(self, topic: str) -> SentimentEntry | None:
        """
        Returns the most recent sentiment analysis for a given topic.
        Returns None if no analysis exists yet.
        """
        if topic not in self.history or len(self.history[topic]) == 0:
            return None
        idx = int(self.latest_index[topic])
        return self.history[topic][idx]

    # ─────────────────────────────────────────
    # READ: Full history for a topic
    # ─────────────────────────────────────────

    @gl.public.view
    def get_history(self, topic: str) -> list[SentimentEntry]:
        """
        Returns all historical sentiment entries for a topic.
        Returns empty list if topic has never been analyzed.
        """
        if topic not in self.history:
            return []
        return list(self.history[topic])

    # ─────────────────────────────────────────
    # READ: Average score for a topic
    # ─────────────────────────────────────────

    @gl.public.view
    def get_average_score(self, topic: str) -> u256:
        """
        Returns the average sentiment score (0-100) across all analyses for a topic.
        Returns 50 (neutral) if no data exists.
        """
        if topic not in self.history or len(self.history[topic]) == 0:
            return u256(50)

        entries = self.history[topic]
        total = sum(int(e.score) for e in entries)
        avg = total // len(entries)
        return u256(avg)

    # ─────────────────────────────────────────
    # READ: Count of analyses per topic
    # ─────────────────────────────────────────

    @gl.public.view
    def get_analysis_count(self, topic: str) -> u256:
        """Returns the total number of analyses run for a given topic."""
        if topic not in self.history:
            return u256(0)
        return u256(len(self.history[topic]))

    # ─────────────────────────────────────────
    # READ: Global stats
    # ─────────────────────────────────────────

    @gl.public.view
    def get_total_analyses(self) -> u256:
        """Returns the total number of sentiment analyses performed by this contract."""
        return self.total_analyses
