# deploy_sentiment_tracker.py
# Deploy the SentimentTracker Intelligent Contract to GenLayer
#
# Usage:
#   genlayer deploy contracts/deploy_sentiment_tracker.py
#
# Or via CLI:
#   genlayer deploy --contract contracts/sentiment_tracker.py

from genlayer import deploy

# Deploy with no constructor arguments
contract_address = deploy(
    contract_file="contracts/sentiment_tracker.py",
    constructor_args=[],
)

print(f"✅ SentimentTracker deployed at: {contract_address}")
print()
print("Next steps:")
print(f"  genlayer write --contract {contract_address} analyze 'Bitcoin' 'https://bitcoin.org'")
print(f"  genlayer call  --contract {contract_address} get_latest 'Bitcoin'")
print(f"  genlayer call  --contract {contract_address} get_total_analyses")
