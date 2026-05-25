# 📊 SentimentTracker — GenLayer Intelligent Contract

An **AI-powered, on-chain sentiment tracker** built on [GenLayer](https://genlayer.com).

Submit any topic + a web URL, and the contract will:
1. **Fetch live web content** from the URL
2. **Ask an LLM** to analyze sentiment about the topic
3. **Store the result on-chain** — permanently, tamper-proof

---

## 🚀 What It Does

| Action | Type | Description |
|---|---|---|
| `analyze(topic, url)` | **Write** | Fetches URL, runs AI analysis, stores result |
| `get_latest(topic)` | **Read** | Returns most recent sentiment for a topic |
| `get_history(topic)` | **Read** | Returns all historical analyses for a topic |
| `get_average_score(topic)` | **Read** | Returns average sentiment score (0–100) |
| `get_analysis_count(topic)` | **Read** | Returns how many times a topic was analyzed |
| `get_total_analyses()` | **Read** | Returns total analyses across all topics |

---

## 📦 Sentiment Entry Format

Each analysis returns a `SentimentEntry` with:

```json
{
  "topic": "Bitcoin",
  "sentiment": "positive",     // positive | negative | neutral | mixed
  "score": 72,                 // 0 (very negative) → 100 (very positive)
  "summary": "Public sentiment around Bitcoin remains optimistic...",
  "source_url": "https://bitcoin.org",
  "submitted_by": "0xYourWallet",
  "timestamp": 1714652400
}
```

---

## 🛠️ Setup & Installation

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **Docker** (for local GenLayer node)

### 1. Install GenLayer CLI

```bash
npm install -g genlayer
```

### 2. Initialize & Start Local Node

```bash
genlayer init
genlayer up
```

### 3. Install Python testing tools

```bash
pip install genlayer-test pytest
```

---

## 🧪 Running Tests

```bash
# From the root of this repository
pytest tests/test_sentiment_tracker.py -v
```

Expected output:
```
tests/test_sentiment_tracker.py::TestInitialState::test_total_analyses_starts_at_zero  PASSED
tests/test_sentiment_tracker.py::TestInitialState::test_unknown_topic_returns_none     PASSED
tests/test_sentiment_tracker.py::TestSingleAnalysis::test_analyze_stores_entry        PASSED
...
```

---

## 🚀 Deploying

### Deploy to Localnet

```bash
genlayer deploy contracts/sentiment_tracker.py
```

### Deploy to Testnet

```bash
genlayer network set testnet
genlayer deploy contracts/sentiment_tracker.py
```

---

## 📡 Interacting with the Contract

Replace `<CONTRACT_ADDRESS>` with your deployed address.

### Analyze a Topic

```bash
genlayer write --contract <CONTRACT_ADDRESS> analyze "Bitcoin" "https://bitcoin.org"
```

```bash
genlayer write --contract <CONTRACT_ADDRESS> analyze "Nigeria economy" "https://en.wikipedia.org/wiki/Economy_of_Nigeria"
```

```bash
genlayer write --contract <CONTRACT_ADDRESS> analyze "Artificial Intelligence" "https://openai.com"
```

### Read Results

```bash
# Get latest sentiment for a topic
genlayer call --contract <CONTRACT_ADDRESS> get_latest "Bitcoin"

# Get full history
genlayer call --contract <CONTRACT_ADDRESS> get_history "Bitcoin"

# Get average sentiment score
genlayer call --contract <CONTRACT_ADDRESS> get_average_score "Bitcoin"

# Get analysis count
genlayer call --contract <CONTRACT_ADDRESS> get_analysis_count "Bitcoin"

# Get total analyses ever run
genlayer call --contract <CONTRACT_ADDRESS> get_total_analyses
```

---

## 🧠 How It Works (GenLayer Features Used)

| Feature | Used For |
|---|---|
| `gl.get_webpage(url)` | Fetching live web content from any URL |
| `gl.exec_prompt_non_comparative()` | Deterministic LLM outputs (classification + scoring) |
| `TreeMap[str, DynArray[SentimentEntry]]` | Efficient on-chain storage per topic |
| `gl.message.sender_address` | Recording who submitted each analysis |
| `gl.message.timestamp` | Recording when each analysis was submitted |
| `@gl.public.write` | State-changing transactions (requires validators) |
| `@gl.public.view` | Read-only queries (free, instant) |

---

## 💡 Example Use Cases

- **Crypto Traders** — Track sentiment around coins before making trades
- **Brand Managers** — Monitor public sentiment about a company or product
- **News Analysts** — Archive the AI's interpretation of news articles over time
- **DAO Governance** — Use objective sentiment data to inform proposals
- **Research** — Build a verifiable, on-chain sentiment dataset

---

## 📁 Project Structure

```
contracts/
  sentiment_tracker.py          # Main intelligent contract
  deploy_sentiment_tracker.py   # Deploy script

tests/
  test_sentiment_tracker.py     # Direct-mode test suite

README.md                       # This file
```

---

## 🔗 Resources

- [GenLayer Docs](https://docs.genlayer.com)
- [GenLayer SDK Reference](https://sdk.genlayer.com)
- [GenLayer Studio](https://studio.genlayer.com) — browser-based IDE
- [Intelligent Contract Examples](https://docs.genlayer.com/developers/intelligent-contracts/examples)
