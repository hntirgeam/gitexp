import argparse
import os
import subprocess
from pathlib import Path

from git import Repo


class CommitImporterService:
    def __init__(self, target_repo: Path, author: str) -> None:
        self.target_repo = Repo(target_repo)
        self.target_repo_commits = self._get_repository_commits(source_repo=self.target_repo)
        self.author = author

    @staticmethod
    def get_repositories(path: Path) -> list[str]:
        cmd = f"find {path} -name .git -type d -prune"
        output = subprocess.getoutput(cmd=cmd)
        return output.split()

    def _get_repository_commits(self, source_repo: Repo) -> None:
        return set(source_repo.iter_commits())

    def export_commits(self, repository: Path):
        existing_hashes = {i.message.strip() for i in self.target_repo_commits}

        commits_to_create = dict()
        source_repo = Repo(repository)
        commits = self._get_repository_commits(source_repo)
        for commit in commits:
            if commit.hexsha not in existing_hashes and self.author in (commit.committer.email, commit.committer.name):
                commits_to_create[commit.hexsha] = commit.committed_datetime

        for hash, date in commits_to_create.items():
            date = str(date)
            os.environ["GIT_AUTHOR_DATE"] = date
            os.environ["GIT_COMMITTER_DATE"] = date
            self.target_repo.git.commit("-m", hash, "--allow-empty")

        print(f"Done exporting {len(commits_to_create)} commits from {source_repo.remotes.origin.url.split("/")[-1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("source", help="Directory where to find source repositories", type=Path)
    parser.add_argument("target", help="Directory where to import commits", type=Path)
    parser.add_argument("author", help="Username/email of commit that script will be looking for", type=str)

    args = parser.parse_args()

    service = CommitImporterService(target_repo=args.target, author=args.author)
    repositories = CommitImporterService.get_repositories(path=args.source)
    for repository in repositories:
        service.export_commits(repository)
    print('Go to target repo and run "git push"')
