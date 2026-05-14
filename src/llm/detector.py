import yaml
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType
from src.llm.factory import create_provider
from src.llm.prompt_builder import build_prompt
from src.llm.response_parser import parse_response


def detect_drift(
    entries: list[Entry],
    strategy: str,
    model_config: dict,
    prompts_config: Path = Path("configs/prompts.yaml"),
    examples: str = "",
) -> list[Prediction]:
    """Run LLM drift detection on a list of entries."""
    provider = create_provider(model_config)
    predictions = []
    for entry in entries:
        prompt = build_prompt(entry, strategy, prompts_config, examples)
        raw_response = provider.generate(prompt)
        parsed = parse_response(raw_response)
        drift_type = DriftType(parsed.get("drift_type", "no-drift"))
        predictions.append(Prediction(
            entry_id=entry.entry_id,
            approach=f"llm-{strategy}",
            predicted_label=drift_type,
            predicted_details=parsed,
            raw_output=raw_response,
        ))
    return predictions