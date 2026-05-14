import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.mining.repo_cloner import clone_repos, load_repo_config


def test_load_repo_config():
    config = load_repo_config(Path("configs/dataset.yaml"))
    assert len(config["repos"]) >= 1
    assert config["repos"][0]["name"] == "flask"


def test_clone_repos_creates_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"repos": [{"name": "test-repo", "url": "https://github.com/octocat/Hello-World.git"}]}
        with patch("src.mining.repo_cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            clone_repos(config, Path(tmpdir))
            assert mock_run.called