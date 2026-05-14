from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, config: dict | None = None) -> str:
        ...


class OllamaProvider(ModelProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, config: dict | None = None) -> str:
        import ollama
        config = config or {}
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": config.get("temperature", 0)},
        )
        return response["message"]["content"]


def create_provider(provider_config: dict) -> ModelProvider:
    """Factory function to create a model provider from config."""
    provider_type = provider_config.get("provider", "ollama")
    if provider_type == "ollama":
        return OllamaProvider(model_name=provider_config["model"])
    raise ValueError(f"Unknown provider: {provider_type}")