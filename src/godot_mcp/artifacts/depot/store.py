"""
Local filesystem artifact depot. Stores artifact metadata as JSON
and associated files in a structured depot directory.
"""

import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from godot_mcp.artifacts.models import Artifact, ArtifactSearchResult, ArtifactType

DEPOT_DIR = Path(os.getenv("GODOT_MCP_DEPOT", str(Path.home() / ".godot-mcp" / "depot")))


class ArtifactDepot:
    def __init__(self, base_dir: Path = DEPOT_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "files").mkdir(exist_ok=True)
        (self.base_dir / "thumbs").mkdir(exist_ok=True)
        self._index_file = self.base_dir / "index.json"
        self._index: dict[str, Artifact] = {}
        self._load_index()

    def _load_index(self):
        if self._index_file.exists():
            raw = json.loads(self._index_file.read_text())
            for k, v in raw.items():
                self._index[k] = Artifact(**v)

    def _save_index(self):
        raw = {k: v.model_dump() for k, v in self._index.items()}
        self._index_file.write_text(json.dumps(raw, indent=2, default=str))

    def list(self, artifact_type: ArtifactType | None = None, skip: int = 0, limit: int = 50) -> ArtifactSearchResult:
        items = list(self._index.values())
        if artifact_type:
            items = [a for a in items if a.artifact_type == artifact_type]
        total = len(items)
        items = items[skip : skip + limit]
        return ArtifactSearchResult(total=total, results=items)

    def get(self, artifact_id: str) -> Artifact | None:
        return self._index.get(artifact_id)

    def search(self, query: str, artifact_type: ArtifactType | None = None) -> ArtifactSearchResult:
        q = query.lower()
        items = [
            a
            for a in self._index.values()
            if q in a.name.lower() or q in a.description.lower() or any(q in t.lower() for t in a.tags)
        ]
        if artifact_type:
            items = [a for a in items if a.artifact_type == artifact_type]
        return ArtifactSearchResult(total=len(items), results=items)

    def put(self, artifact: Artifact, source_path: Path | None = None) -> Artifact:
        if not artifact.id:
            artifact.id = str(uuid.uuid4())[:8]
        if not artifact.created_at:
            artifact.created_at = datetime.now(UTC).isoformat()
        artifact.updated_at = datetime.now(UTC).isoformat()
        if source_path and source_path.exists():
            dest = self.base_dir / "files" / f"{artifact.id}_{source_path.name}"
            shutil.copy2(source_path, dest)
            artifact.file_path = str(dest)
            artifact.file_size = dest.stat().st_size
            artifact.download_url = f"/api/v1/artifacts/{artifact.id}/download"
        self._index[artifact.id] = artifact
        self._save_index()
        return artifact

    def delete(self, artifact_id: str) -> bool:
        if artifact_id not in self._index:
            return False
        artifact = self._index[artifact_id]
        if artifact.file_path:
            Path(artifact.file_path).unlink(missing_ok=True)
        del self._index[artifact_id]
        self._save_index()
        return True

    def list_by_type(self, artifact_type: ArtifactType) -> ArtifactSearchResult:
        return self.list(artifact_type=artifact_type)


# Module singleton
_depot = ArtifactDepot()


def get_depot() -> ArtifactDepot:
    return _depot
