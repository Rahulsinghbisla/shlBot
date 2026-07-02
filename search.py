import json
import re
from rank_bm25 import BM25Okapi

# ──────────────────────────────────────────────────────────────
# Step 1: Load catalog (strict=False handles stray control chars
# that sometimes sneak into scraped description fields)
# ──────────────────────────────────────────────────────────────
with open("data.json", "r", encoding="utf-8") as f:
    RAW_CATALOG = [item for item in json.load(f, strict=False) if item.get("status") == "ok"]

# Fast lookup: entity_id -> full original item (this is your "source of truth")
CATALOG_LOOKUP = {item["entity_id"]: item for item in RAW_CATALOG}


# ──────────────────────────────────────────────────────────────
# Step 2: Tokenizer
# ──────────────────────────────────────────────────────────────
def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9\+\#\.]+", text.lower())


# ──────────────────────────────────────────────────────────────
# Step 3: Build searchable corpus once at startup (not per query)
# ──────────────────────────────────────────────────────────────
CATALOG_IDS: list[str] = []      # parallel list of entity_ids, same order as CORPUS_TOKENS
CORPUS_TOKENS: list[list[str]] = []

for item in RAW_CATALOG:
    searchable_text = " ".join([
        item.get("name", ""),
        item.get("description", ""),
        item.get("job_levels_raw", ""),
        " ".join(item.get("keys", [])),
        item.get("duration_raw", ""),
    ])
    CATALOG_IDS.append(item["entity_id"])
    CORPUS_TOKENS.append(tokenize(searchable_text))

bm25 = BM25Okapi(CORPUS_TOKENS)


# ──────────────────────────────────────────────────────────────
# Step 4: Search function
# Returns FULL original catalog items (never partial/vector-only data)
# ──────────────────────────────────────────────────────────────
def search_catalog(query: str, job_level: str | None = None, limit: int = 5) -> list[dict]:
    tokens = tokenize(query)
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)

    # Rank entity_ids by score (descending)
    ranked_ids = sorted(
        zip(scores, CATALOG_IDS),
        key=lambda x: x[0],
        reverse=True,
    )

    def fetch_full(entity_id: str) -> dict:
        # Always pull the complete, authoritative record from CATALOG_LOOKUP
        return CATALOG_LOOKUP[entity_id]

    results = []
    for score, entity_id in ranked_ids:
        if score <= 0:
            continue
        item = fetch_full(entity_id)
        if job_level and job_level.lower() not in item.get("job_levels_raw", "").lower():
            continue
        results.append(item)
        if len(results) >= limit:
            break

    # Fallback: if job_level filter wiped out all results, drop the filter
    if not results:
        results = [
            fetch_full(entity_id)
            for score, entity_id in ranked_ids
            if score > 0
        ][:limit]

    return results


# ──────────────────────────────────────────────────────────────
# Optional: direct ID lookup (handy for tests / debugging / when
# the LLM references an assessment by name and you want to verify it)
# ──────────────────────────────────────────────────────────────
def get_by_id(entity_id: str) -> dict | None:
    return CATALOG_LOOKUP.get(entity_id)


def get_by_name(name: str) -> dict | None:
    for item in RAW_CATALOG:
        if item["name"].lower() == name.lower():
            return item
    return None