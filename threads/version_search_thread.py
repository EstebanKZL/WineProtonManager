import json
from urllib.request import urlopen, Request, HTTPError
from PyQt5.QtCore import QThread, pyqtSignal

class VersionSearchThread(QThread):
    progress = pyqtSignal(int) 
    new_release = pyqtSignal(str, str, str, object, str) 
    error = pyqtSignal(str) 

    def __init__(self, repo_type: str, repositories: list[dict]):
        super().__init__()
        self.repo_type = repo_type
        self.repositories = repositories

    def run(self):
        fetched_count = 0
        total_repos = len(self.repositories)

        for i, repo in enumerate(self.repositories):
            if not repo.get("enabled", True):
                fetched_count += 1
                self.progress.emit(int(fetched_count * 100 / total_repos))
                continue

            url = repo["url"]
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0 WineProtonManager'}) 
                with urlopen(req, timeout=10) as response:
                    if response.getcode() != 200:
                        raise HTTPError(url, response.getcode(), response.reason, response.headers, None)

                    releases = json.loads(response.read().decode())

                    for release in releases:
                        if release.get("draft", False) or release.get("prerelease", False):
                            continue 

                        version = release["tag_name"]
                        assets = [a for a in release["assets"] if any(a["name"].endswith(ext) for ext in ['.tar.gz', '.tar.xz', '.zip', '.tar.bz2', '.tar.zst'])]

                        if not assets:
                            continue 

                        release_name = release.get("name", version)
                        published_at = release.get("published_at", "")

                        self.new_release.emit(self.repo_type, release_name, version, assets, published_at)

            except HTTPError as e:
                self.error.emit(f"Error HTTP del repositorio '{repo['name']}': {e.code} - {e.reason}")
            except Exception as e:
                self.error.emit(f"Error obteniendo versiones de '{repo['name']}': {str(e)}")
            finally:
                fetched_count += 1
                self.progress.emit(int(fetched_count * 100 / total_repos))
