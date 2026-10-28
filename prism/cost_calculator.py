"""Cost calculation utility for Prism Gateway.
Calculates token pricing based on data/model_pricing.json.
"""

from prism.config import config


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    is_cache_hit: bool = False
) -> float:
    """Calculates request cost in USD.
    Returns 0.0 for cache hits.
    """
    if is_cache_hit:
        return 0.0

    pricing = config.get_pricing(model)
    if not pricing:
        return 0.0

    input_rate = pricing.get("input_per_1m", 0.0) / 1_000_000.0
    output_rate = pricing.get("output_per_1m", 0.0) / 1_000_000.0

    cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
    return round(cost, 6)
