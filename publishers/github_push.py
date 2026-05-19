import os

os.environ.setdefault("GIT_PYTHON_GIT_EXECUTABLE", "E:/Git/bin/git.exe")
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")

from datetime import datetime
import git
from git import Repo, Actor
from config import GITHUB_REPO_PATH, REPORTS_DIR


def push_report(report: str):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}-daily-report.md"
    filepath = os.path.join(REPORTS_DIR, filename)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    repo = Repo(GITHUB_REPO_PATH)

    if repo.is_dirty(untracked_files=True):
        repo.index.add([filepath])
        author = Actor("Hotspot Agent", "agent@hotspot.local")
        repo.index.commit(
            f"docs: daily report {today}",
            author=author,
            committer=author,
        )
        origin = repo.remote("origin")
        origin.push()
