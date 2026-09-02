"""
Local filesystem artifact depot. Stores artifact metadata as JSON
and associated files in a structured depot directory.
"""

import json
import os
import shutil
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from godot_mcp.artifacts.models import Artifact, ArtifactSearchResult, ArtifactType

DEPOT_DIR = Path(os.getenv("GODOT_MCP_DEPOT", str(Path.home() / ".godot-mcp" / "depot")))
BACKUPS_DIR = DEPOT_DIR / "backups"


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

    def update(
        self,
        artifact_id: str,
        name: str | None = None,
        description: str | None = None,
        # Quoted forward-ref: the class already defines a method named `list` above, so an
        # unquoted `list[str]` here would resolve to THAT method (not the builtin) at
        # class-definition time and raise "'function' object is not subscriptable" - a real,
        # if obscure, Python gotcha caught while offline-testing this addition.
        tags: "list[str] | None" = None,
        author: str | None = None,
    ) -> Artifact | None:
        """Edit an artifact's metadata in place (file on disk, if any, is untouched).
        Added 2026-09-03 - no metadata-edit tool existed before this, only register+delete."""
        artifact = self._index.get(artifact_id)
        if artifact is None:
            return None
        if name is not None:
            artifact.name = name
        if description is not None:
            artifact.description = description
        if tags is not None:
            artifact.tags = tags
        if author is not None:
            artifact.author = author
        artifact.updated_at = datetime.now(UTC).isoformat()
        self._index[artifact_id] = artifact
        self._save_index()
        return artifact

    def backup(self) -> dict:
        """Zip-snapshot files/, thumbs/, and index.json into backups/<timestamp>.zip. Same
        pattern as overte-mcp/resonite-mcp's depot backup - added 2026-09-03, no backup/restore
        existed before this."""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = BACKUPS_DIR / f"godot-mcp-depot-backup-{ts}.zip"

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for sub in ("files", "thumbs"):
                d = self.base_dir / sub
                if not d.exists():
                    continue
                for fp in d.rglob("*"):
                    if fp.is_file():
                        zf.write(fp, arcname=f"{sub}/{fp.relative_to(d)}")
            if self._index_file.exists():
                zf.write(self._index_file, arcname="index.json")

        return {"name": backup_path.name, "size": backup_path.stat().st_size}

    def list_backups(self) -> "list[dict]":  # quoted - see the note on update()'s `tags` param
        if not BACKUPS_DIR.exists():
            return []
        return sorted(
            (
                {
                    "name": p.name,
                    "size": p.stat().st_size,
                    "created_at": datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(),
                }
                for p in BACKUPS_DIR.glob("*.zip")
            ),
            key=lambda x: x["created_at"],
            reverse=True,
        )

    def restore_backup(self, name: str) -> dict:
        """Restore a backup archive, OVERWRITING current files/thumbs/index.json (matching
        names only - does not delete entries the backup doesn't mention). Re-loads the index
        from disk afterward so this instance's in-memory state reflects the restore."""
        backup_path = BACKUPS_DIR / name
        if not backup_path.exists() or backup_path.suffix != ".zip":
            return {"restored": False, "error": f"Backup not found: {name}"}

        restored = 0
        with zipfile.ZipFile(backup_path, "r") as zf:
            for member in zf.namelist():
                if member == "index.json":
                    target_path = self._index_file
                else:
                    prefix, _, rel = member.partition("/")
                    if prefix not in ("files", "thumbs") or not rel:
                        continue
                    target_path = self.base_dir / prefix / rel
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(zf.read(member))
                restored += 1

        self._index = {}
        self._load_index()
        return {"restored": True, "count": restored}

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
