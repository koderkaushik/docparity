import yaml
from pathlib import Path
from src.shared.schema import Entry


def load_prompts(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_prompt(entry: Entry, strategy: str, config_path: Path = Path("configs/prompts.yaml"),
                 examples: str = "") -> str:
    """Build a prompt for the given entry using the specified strategy."""
    prompts = load_prompts(config_path)
    template = prompts[strategy]["template"]
    system = prompts[strategy]["system"]
    prompt = template.format(code=entry.code, docstring=entry.docstring, examples=examples)
    return f"System: {system}\n\n{prompt}"