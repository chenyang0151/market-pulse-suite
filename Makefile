PY ?= python3

.PHONY: market-pulse creator-consensus sim-portfolio clean

market-pulse:
	bash packages/market-pulse/scripts/daily.sh

creator-consensus:
	cd packages/creator-consensus && $(PY) generate_consensus.py --out ../../samples/creator_consensus_sample.md

sim-portfolio:
	cd packages/sim-portfolio-100k && $(PY) scripts/rebalance.py --out ../../samples/rebalance-note.txt

clean:
	rm -rf data/market-pulse/raw/* data/market-pulse/reports/* data/market-pulse/logs/*
