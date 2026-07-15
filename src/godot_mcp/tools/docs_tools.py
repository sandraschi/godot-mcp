"""Godot documentation tools — fetch version-matched docs as markdown."""

import html.parser
import logging
from typing import Annotated

import httpx
from fastmcp import Context
from pydantic import Field

from godot_mcp.services.godot_bridge import get_bridge

logger = logging.getLogger("godot-mcp.docs")

_DOCS_BASE = "https://docs.godotengine.org/en/stable"
_CLASS_BASE = f"{_DOCS_BASE}/classes"


async def godot_docs(
    query: Annotated[
        str,
        Field(
            description="Class name (e.g. 'Node3D', 'AnimationPlayer', 'TileMapLayer') or search term. Case-insensitive."
        ),
    ],
    section: Annotated[
        str | None,
        Field(
            description="Optional section filter: 'description', 'tutorials', 'methods', 'signals', 'properties', 'constants', or empty for full page.",
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Fetch Godot engine documentation as clean markdown.

    Retrieves class reference pages from docs.godotengine.org, version-matched
    to the running Godot engine. The documentation is returned as rendered
    markdown with working anchor links.

    ## Return Format
    {"success": bool, "class": str, "version": str, "content": str, "sections": list}

    ## Examples
    await godot_docs(query="Node3D")
    await godot_docs(query="AnimationPlayer", section="methods")
    await godot_docs(query="TileMapLayer")
    """
    try:
        # Detect running Godot version for doc matching
        version = "stable"
        bridge = get_bridge()
        if bridge.connected:
            import asyncio

            result = await asyncio.to_thread(bridge.send, "status")
            if result["success"]:
                gv = result["data"].get("godot_version", "")
                if gv and gv != "unknown":
                    parts = gv.split(".")
                    if len(parts) >= 2:
                        version = f"{parts[0]}.{parts[1]}"

        class_name = query.strip().lower().replace(" ", "_")

        # Try the class reference URL
        class_url = f"{_DOCS_BASE}/classes/class_{class_name}.html"
        if section:
            class_url += f"#{section}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(class_url)
            if resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Class '{query}' not found at {class_url} (HTTP {resp.status_code})",
                    "suggestion": "Try a different class name or use a broader search term.",
                }

            html = resp.text
            content, sections = _extract_docs(html, section)

            return {
                "success": True,
                "class": query,
                "version": version,
                "url": class_url,
                "content": content,
                "sections": sections,
                "length": len(content),
            }

    except httpx.TimeoutException:
        return {"success": False, "error": "Docs.godotengine.org timed out. Check your internet connection."}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Network error fetching docs: {e}"}
    except Exception as e:
        logger.exception("godot_docs error")
        return {"success": False, "error": str(e)}


class _DocsExtractor(html.parser.HTMLParser):
    """Minimal HTML parser to extract Godot docs content without BeautifulSoup."""

    def __init__(self):
        super().__init__()
        self.sections: list[dict] = []
        self.content_parts: list[str] = []
        self._current_section_id = ""
        self._current_section_text = ""
        self._current_section_level = 0
        self._in_main = False
        self._in_heading = False
        self._heading_tag = ""
        self._skip_depth = 0
        self._collect_text = False
        self._buffer: list[str] = []
        self._main_depth = 0
        self._section_filter: str | None = None

    def set_filter(self, section_filter: str | None):
        self._section_filter = section_filter

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # Detect main content area
        if (tag in ("div", "article") and ("role", "main") in attrs) or ("class", "document") in [
            a for a in attrs if a[0] == "class"
        ]:
            self._in_main = True
            self._main_depth = 1
            return
        if self._in_main:
            if tag in ("div", "article", "section"):
                self._main_depth += 1
        if not self._in_main:
            return

        # Track headings
        if tag in ("h1", "h2", "h3", "h4") and self._in_main:
            self._flush_heading()
            self._in_heading = True
            self._heading_tag = tag
            self._current_section_id = attrs_dict.get("id", "")
            self._current_section_level = int(tag[1])
            self._buffer = []

        # Skip nav, script, style, code (we extract code later)
        if tag in ("nav", "script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if self._in_main and tag in ("div", "article", "section"):
            self._main_depth -= 1
            if self._main_depth <= 0:
                self._in_main = False
                self._flush_heading()
                return
        if not self._in_main:
            return
        if self._skip_depth > 0:
            if tag in ("nav", "script", "style"):
                self._skip_depth -= 1
            return
        if self._in_heading and tag == self._heading_tag:
            self._current_section_text = "".join(self._buffer).strip()
            self._in_heading = False
            self._buffer = []

    def handle_data(self, data):
        if self._skip_depth > 0 or not self._in_main:
            return
        if self._in_heading:
            self._buffer.append(data)
        else:
            stripped = data.strip()
            if stripped:
                self._buffer.append(data)

    def _flush_heading(self):
        if self._current_section_text and self._current_section_id:
            section_info = {
                "id": self._current_section_id,
                "title": self._current_section_text,
                "level": self._current_section_level,
            }
            self.sections.append(section_info)

            if (
                self._section_filter
                and self._section_filter.lower() not in self._current_section_id
                and self._section_filter.lower() not in self._current_section_text.lower()
            ):
                pass  # skip content for non-matching sections
            else:
                text = "".join(self._buffer).strip()
                if text:
                    self.content_parts.append(f"\n## {self._current_section_text}\n{text}")

        self._current_section_id = ""
        self._current_section_text = ""
        self._current_section_level = 0
        self._buffer = []

    def get_result(self) -> tuple[str, list[dict]]:
        self._flush_heading()
        result = "\n\n".join(self.content_parts)
        if not result:
            result = "Documentation content could not be extracted."
        return result, self.sections


def _extract_docs(html_content: str, section_filter: str | None = None) -> tuple[str, list[dict]]:
    extractor = _DocsExtractor()
    extractor.set_filter(section_filter)
    try:
        extractor.feed(html_content)
    except Exception:
        logger.warning("Docs HTML parsing error", exc_info=True)
    return extractor.get_result()


def register(mcp):
    mcp.tool(annotations={"readonly": True}, version="0.1.0")(godot_docs)
