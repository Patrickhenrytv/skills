# tests/test_sentiment_tracker.py
# Direct-mode tests for the SentimentTracker Intelligent Contract
#
# Run with:
#   python -m pytest tests/test_sentiment_tracker.py -v
#

import sys
# Clear genlayer and related modules from sys.modules to ensure the correct SDK is imported
for mod in list(sys.modules.keys()):
    if mod == 'genlayer' or mod.startswith('genlayer.'):
        del sys.modules[mod]

import pytest
from gltest.direct import VMContext, deploy_contract, create_address


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def vm():
    """Create a VMContext with catch-all web and LLM mocks."""
    ctx = VMContext()
    ctx.mock_web(".*", {"body": "Mock content for testing public sentiment and trends."})
    ctx.mock_llm("classify the sentiment", "positive")
    ctx.mock_llm("integer score", '"75"')
    ctx.mock_llm("sentence, summarize", "The sentiment is positive and shows good outlook.")
    with ctx.activate():
        yield ctx


@pytest.fixture
def contract(vm):
    """Deploy the contract and return the instance."""
    return deploy_contract("contracts/sentiment_tracker.py", vm)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class TestInitialState:
    """Contract should start with zeroed counters and empty storage."""

    def test_total_analyses_starts_at_zero(self, contract, vm):
        result = contract.get_total_analyses()
        assert int(result) == 0

    def test_unknown_topic_returns_none(self, contract, vm):
        result = contract.get_latest("Bitcoin")
        assert result is None

    def test_unknown_topic_history_is_empty(self, contract, vm):
        result = contract.get_history("NonExistentTopic")
        assert result == []

    def test_unknown_topic_count_is_zero(self, contract, vm):
        result = contract.get_analysis_count("Ethereum")
        assert int(result) == 0

    def test_unknown_topic_avg_score_is_neutral(self, contract, vm):
        result = contract.get_average_score("SomeRandomTopic")
        assert int(result) == 50  # default neutral score


class TestSingleAnalysis:
    """Test a single sentiment analysis submission."""

    def test_analyze_increases_total_count(self, contract, vm):
        vm.sender = create_address("0xUserWallet1")
        contract.analyze(
            "Bitcoin",
            "https://en.wikipedia.org/wiki/Bitcoin",
        )
        result = contract.get_total_analyses()
        assert int(result) == 1

    def test_analyze_stores_entry(self, contract, vm):
        vm.sender = create_address("0xUserWallet1")
        contract.analyze(
            "Bitcoin",
            "https://en.wikipedia.org/wiki/Bitcoin",
        )
        entry = contract.get_latest("Bitcoin")
        assert entry is not None
        assert entry.topic == "Bitcoin"
        assert entry.sentiment in {"positive", "negative", "neutral", "mixed"}
        assert 0 <= int(entry.score) <= 100
        assert len(entry.summary) > 0
        assert entry.source_url == "https://en.wikipedia.org/wiki/Bitcoin"

    def test_history_has_one_entry_after_single_analysis(self, contract, vm):
        vm.sender = create_address("0xUserWallet2")
        contract.analyze(
            "Ethereum",
            "https://en.wikipedia.org/wiki/Ethereum",
        )
        history = contract.get_history("Ethereum")
        assert len(history) == 1

    def test_analysis_count_increments(self, contract, vm):
        vm.sender = create_address("0xUserWallet1")
        contract.analyze(
            "AI",
            "https://en.wikipedia.org/wiki/Artificial_intelligence",
        )
        count = contract.get_analysis_count("AI")
        assert int(count) == 1


class TestMultipleAnalyses:
    """Test multiple analyses for the same and different topics."""

    def test_multiple_analyses_same_topic(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("Bitcoin", "https://en.wikipedia.org/wiki/Bitcoin")
        vm.sender = create_address("0xB")
        contract.analyze("Bitcoin", "https://bitcoin.org")
        vm.sender = create_address("0xC")
        contract.analyze("Bitcoin", "https://coindesk.com")

        count = contract.get_analysis_count("Bitcoin")
        history = contract.get_history("Bitcoin")

        assert int(count) == 3
        assert len(history) == 3

    def test_different_topics_tracked_independently(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("Bitcoin", "https://en.wikipedia.org/wiki/Bitcoin")
        vm.sender = create_address("0xB")
        contract.analyze("Ethereum", "https://en.wikipedia.org/wiki/Ethereum")

        count_btc = contract.get_analysis_count("Bitcoin")
        count_eth = contract.get_analysis_count("Ethereum")
        total = contract.get_total_analyses()

        assert int(count_btc) == 1
        assert int(count_eth) == 1
        assert int(total) == 2

    def test_latest_returns_most_recent(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("Bitcoin", "https://en.wikipedia.org/wiki/Bitcoin")
        vm.sender = create_address("0xB")
        contract.analyze("Bitcoin", "https://bitcoin.org")

        latest = contract.get_latest("Bitcoin")

        assert latest.source_url == "https://bitcoin.org"

    def test_average_score_is_calculated(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("GenLayer", "https://genlayer.com")
        vm.sender = create_address("0xB")
        contract.analyze("GenLayer", "https://docs.genlayer.com")

        avg = contract.get_average_score("GenLayer")

        assert 0 <= int(avg) <= 100


class TestSentimentOutput:
    """Validate the LLM output format and score ranges."""

    def test_score_is_within_valid_range(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("OpenAI", "https://openai.com")
        entry = contract.get_latest("OpenAI")
        assert 0 <= int(entry.score) <= 100

    def test_sentiment_label_is_valid(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("Tesla", "https://en.wikipedia.org/wiki/Tesla,_Inc.")
        entry = contract.get_latest("Tesla")
        assert entry.sentiment in {"positive", "negative", "neutral", "mixed"}

    def test_summary_is_non_empty_string(self, contract, vm):
        vm.sender = create_address("0xA")
        contract.analyze("Climate Change", "https://en.wikipedia.org/wiki/Climate_change")
        entry = contract.get_latest("Climate Change")
        assert isinstance(entry.summary, str)
        assert len(entry.summary.strip()) > 0
