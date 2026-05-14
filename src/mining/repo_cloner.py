import subprocess
from pathlib import Path
import yaml


def load_repo_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def clone_repos(config: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for repo in config["repos"]:
        name = repo["name"]
        url = repo["url"]
        dest = output_dir / name
        if dest.exists():
            print(f"Repo {name} already exists, skipping...")
            continue
        print(f"Cloning {name} from {url}...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, str(dest)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Failed to clone {name}: {result.stderr}")
        else:
            print(f"Cloned {name} successfully.")


if __name__ == "__main__":
    config = load_repo_config(Path("configs/dataset.yaml"))
    clone_repos(config, Path("data/repos"))