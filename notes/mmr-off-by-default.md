# Why MMR is off by default in my RAG service

*From [agentic-rag-service](https://github.com/HarshitGadge/agentic-rag-service).*

My retrieval service used to rerank results with maximal marginal relevance (MMR). MMR trades some relevance for variety, so the top results don't all say the same thing. It's a common default, and I kept it because it sounded right.

Then I measured it. On BEIR SciFact, 300 queries, the old defaults with MMR scored **0.663** nDCG@10. Turning MMR off scored **0.713**. The 95% bootstrap confidence interval for that gain is **+3.1 to +6.9** points, so it isn't noise.

A likely reason is what SciFact asks for. Each query is a scientific claim, and the passages that support it tend to look alike. MMR treats that likeness as redundancy and pushes good passages down the list.

So I changed the default. MMR is still one setting away (`mmr_lambda`) for a corpus where near-duplicates really are a problem. The full results, with every configuration I tried, are in [`eval/results/scifact.json`](https://github.com/HarshitGadge/agentic-rag-service/blob/main/eval/results/scifact.json).

The lesson I took from it: a default that sounds sensible is still a guess until an evaluation backs it.
