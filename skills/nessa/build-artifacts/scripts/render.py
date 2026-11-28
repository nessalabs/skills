#!/usr/bin/env python3
"""Render a build-artifacts document (Markdown with directives) to one HTML file.

    render.py DOC.md -o OUT.html      render with the resolved theme
    render.py --voice                 print the resolved writing voice
    render.py --explain-theme         print each theme key and the layer it came from

Theme layers, lowest to highest: the Nessa default (references/template.html for
tokens, references/default-theme.toml for voice and components), the user file,
the project file, then --theme. A key a layer leaves out falls through.

User file:    $NESSA_ARTIFACTS_THEME, else ~/.nessa/artifacts/theme.toml
Project file: .nessa/artifacts/theme.toml in the nearest parent of --project
              (default: the document's folder) that has one.
Files may be .toml or .json. Python 3.11+ is needed for .toml.

Standard library only. Exit 1 on errors; warnings go to stderr.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "references"
TEMPLATE = REFS / "template.html"
DEFAULT_THEME = REFS / "default-theme.toml"
MERMAID_SRC = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"

ADDITIVE = {("voice", "add_banned_words"), ("voice", "add_rules")}
BADGES = ("sourced", "judgment", "placeholder")
PILLS = ("has", "partial", "missing")
BLOCK_DIRECTIVES = {"lead", "note", "quote", "ranked", "idea", "states", "invariants",
                    "risks", "questions", "skip", "sources", "diagram"}

warnings: list[str] = []


def warn(msg: str) -> None:
    warnings.append(msg)


class RenderError(Exception):
    pass


# ---------------------------------------------------------------- theme

def load_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    try:
        import tomllib
    except ImportError as exc:  # Python < 3.11
        raise RenderError(f"{path}: reading .toml needs Python 3.11+; use a .json theme file") from exc
    return tomllib.loads(text)


def template_tokens(template: str) -> set[str]:
    first_root = template.split(":root {", 1)[1].split("\n}", 1)[0]
    return set(re.findall(r"--([a-z0-9-]+)\s*:", first_root))


def merge(base: dict, over: dict, origin: dict, layer: str, prefix: tuple = ()) -> None:
    for key, value in over.items():
        path = prefix + (key,)
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value, origin, layer, path)
            continue
        if isinstance(value, dict):
            base[key] = {}
            merge(base[key], value, origin, layer, path)
            continue
        if path in ADDITIVE:
            base[key] = list(base.get(key, [])) + list(value)
            origin[path] = (origin.get(path, "") + " + " + layer).strip(" +")
        else:
            base[key] = value
            origin[path] = layer


def find_project_theme(start: Path) -> Path | None:
    for folder in [start, *start.parents]:
        for name in ("theme.toml", "theme.json"):
            candidate = folder / ".nessa" / "artifacts" / name
            if candidate.is_file():
                return candidate
    return None


def user_theme_path() -> Path | None:
    env = os.environ.get("NESSA_ARTIFACTS_THEME")
    if env:
        return Path(env).expanduser()
    for name in ("theme.toml", "theme.json"):
        candidate = Path.home() / ".nessa" / "artifacts" / name
        if candidate.is_file():
            return candidate
    return None


def resolve_theme(args, template: str) -> tuple[dict, dict, list[str]]:
    theme: dict = {}
    origin: dict = {}
    used: list[str] = []
    merge(theme, load_file(DEFAULT_THEME), origin, "nessa default")
    used.append(f"nessa default ({DEFAULT_THEME.name} + template.html tokens)")
    layers = []
    if not args.no_user:
        user = Path(args.user).expanduser() if args.user else user_theme_path()
        if user and user.is_file():
            layers.append(("user", user))
        elif args.user:
            raise RenderError(f"user theme not found: {args.user}")
    if not args.no_project:
        start = Path(args.project or (Path(args.doc).parent if args.doc else Path.cwd())).resolve()
        proj = find_project_theme(start)
        if proj:
            layers.append(("project", proj))
    for t in args.theme or []:
        layers.append(("--theme", Path(t)))
    allowed = template_tokens(template)
    for layer, path in layers:
        data = load_file(path)
        if "floor" in data.get("voice", {}):
            raise RenderError(f"{path}: [voice.floor] is fixed by the Nessa default and cannot be overridden")
        tokens = data.get("tokens", {})
        for key in list(tokens):
            if key == "dark":
                for dkey in list(tokens["dark"]):
                    if dkey not in allowed:
                        warn(f"{path}: unknown token tokens.dark.{dkey} ignored")
                        del tokens["dark"][dkey]
            elif key not in allowed:
                warn(f"{path}: unknown token tokens.{key} ignored (see template.html :root)")
                del tokens[key]
        # A layer that sets a light color but not its dark value takes the
        # whole color: a lower layer's dark value for it no longer applies.
        lower_dark = theme.get("tokens", {}).get("dark", {})
        for key in tokens:
            if key != "dark" and key in lower_dark and key not in tokens.get("dark", {}):
                del lower_dark[key]
                origin.pop(("tokens", "dark", key), None)
        merge(theme, data, origin, f"{layer} ({path})")
        used.append(f"{layer} ({path})")
    return theme, origin, used


def css_value(value) -> str:
    text = str(value)
    if re.search(r"[;{}<]", text):
        raise RenderError(f"token value not allowed: {text!r}")
    return text


def theme_css(theme: dict) -> str:
    tokens = dict(theme.get("tokens", {}))
    dark = tokens.pop("dark", {}) or {}
    if not tokens and not dark:
        return "/* no overrides: Nessa default tokens */"
    light = "".join(f"  --{k}: {css_value(v)};\n" for k, v in tokens.items())
    # A color set only for light mode stays in light mode; dark keeps its own
    # default unless tokens.dark sets it. Non-color tokens apply in both.
    dark_all = {k: v for k, v in tokens.items() if not k.startswith("color-")}
    dark_all.update(dark)
    dark_css = "".join(f"  --{k}: {css_value(v)};\n" for k, v in dark_all.items())
    out = f":root {{\n{light}}}\n"
    if dark_css:
        out += ("@media (prefers-color-scheme: dark) {\n:root:not([data-theme=\"light\"]) {\n"
                f"{dark_css}}}\n}}\n:root[data-theme=\"dark\"] {{\n{dark_css}}}\n")
    return out


# ---------------------------------------------------------------- inline markdown

def inline(text: str, theme: dict) -> str:
    labels = theme["components"]["labels"]
    codes: list[str] = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = html.escape(text, quote=False)

    def link(m):
        href = m.group(2).replace('"', "%22")
        return f'<a href="{href}">{m.group(1)}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", text)

    def tag(m):
        name, note = m.group(1), m.group(2)
        label = labels.get(name, name.title())
        if note:
            label = f"{label}: {note.strip()}"
        if name in PILLS:
            return f'<strong class="status status-{name}">{label}</strong>'
        return f'<span class="provenance provenance-{name}">{label}</span>'

    text = re.sub(r"\{(sourced|judgment|placeholder|has|partial|missing)(?::([^}]*))?\}", tag, text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))], quote=False)}</code>", text)
    return text


def slug(text: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", re.sub(r"\{[^}]*\}", "", text).lower()).strip("-") or "section"
    candidate, n = base, 2
    while candidate in used:
        candidate, n = f"{base}-{n}", n + 1
    used.add(candidate)
    return candidate


# ---------------------------------------------------------------- blocks

LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
FIELD_RE = re.compile(r"^([A-Z][A-Za-z' ]{0,30}):\s+(.*)$")


def parse_attrs(text: str) -> dict:
    attrs = {}
    for m in re.finditer(r'(\w[\w-]*)=(?:"([^"]*)"|(\S+))|(\w[\w-]*)', text):
        if m.group(4):
            attrs[m.group(4)] = True
        else:
            attrs[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return attrs


class Renderer:
    def __init__(self, theme: dict, source_name: str):
        self.theme = theme
        self.ids: set[str] = set()
        self.toc: list[tuple[str, str]] = []
        self.toc_all: list[tuple[int, str, str]] = []
        self.counts = {k: 0 for k in BADGES + PILLS}
        self.directives: list[str] = []
        self.has_mermaid = False
        self.source = source_name
        self.sections: list[dict] = []

    def il(self, text: str) -> str:
        for name in self.counts:
            found = len(re.findall(r"\{" + name + r"(?::[^}]*)?\}", text))
            self.counts[name] += found
            if found and name in ("sourced", "judgment", "placeholder") and self.sections:
                self.sections[-1]["labels"] += found
        return inline(text, self.theme)

    # split lines into blocks, render each
    def blocks(self, lines: list[str], base_line: int = 0) -> str:
        out: list[tuple[str, str]] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            lineno = base_line + i + 1
            if not stripped:
                i += 1
                continue
            m = re.match(r"^(`{3,})\s*([\w-]*)\s*$", stripped)
            if m:
                fence, lang = m.group(1), m.group(2)
                j = i + 1
                while j < len(lines) and lines[j].strip() != fence:
                    j += 1
                if j >= len(lines):
                    raise RenderError(f"{self.source}:{lineno}: code fence never closed")
                body = "\n".join(lines[i + 1:j])
                if lang == "mermaid":
                    out.append(("block", self.mermaid(body, None)))
                else:
                    cls = f' class="language-{lang}"' if lang else ""
                    out.append(("block", f"<pre><code{cls}>{html.escape(body)}</code></pre>"))
                i = j + 1
                continue
            m = re.match(r"^:::(\w[\w-]*)\s*(.*)$", stripped)
            if m:
                name, attrs = m.group(1), parse_attrs(m.group(2))
                if name not in BLOCK_DIRECTIVES:
                    raise RenderError(f"{self.source}:{lineno}: unknown directive :::{name}")
                depth, j = 1, i + 1
                while j < len(lines):
                    s = lines[j].strip()
                    if re.match(r"^:::\w", s):
                        depth += 1
                    elif s == ":::":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if j >= len(lines):
                    raise RenderError(f"{self.source}:{lineno}: :::{name} never closed with :::")
                self.directives.append(name)
                if self.sections:
                    self.sections[-1]["directives"].append(name)
                kind = "idea" if name == "idea" else "block"
                out.append((kind, self.directive(name, attrs, lines[i + 1:j], base_line + i + 1)))
                i = j + 1
                continue
            m = re.match(r"^::caption\s+(.*)$", stripped)
            if m:
                out.append(("block", f'<p class="caption">{self.il(m.group(1))}</p>'))
                i += 1
                continue
            m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                if level == 1:
                    warn(f"{self.source}:{lineno}: use the front matter title, not '# '; rendered as h2")
                    level = 2
                text = m.group(2)
                ident = slug(text, self.ids)
                if level in (2, 3):
                    self.toc_all.append((level, ident, re.sub(r"\s*\{[^}]*\}", "", text)))
                if level == 2:
                    self.toc.append((ident, re.sub(r"\s*\{[^}]*\}", "", text)))
                    self.sections.append({"title": text, "line": lineno, "labels": 0, "directives": []})
                out.append(("block", f'<h{level} id="{ident}">{self.il(text)}</h{level}>'))
                i += 1
                continue
            if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
                j = i
                while j < len(lines) and lines[j].strip().startswith("|"):
                    j += 1
                out.append(("block", self.table(lines[i:j])))
                i = j
                continue
            if LIST_RE.match(line):
                j = i
                while j < len(lines) and lines[j].strip() and (LIST_RE.match(lines[j]) or lines[j].startswith(("  ", "\t"))):
                    j += 1
                out.append(("block", self.list(lines[i:j])))
                i = j
                continue
            if stripped.startswith(">"):
                j = i
                while j < len(lines) and lines[j].strip().startswith(">"):
                    j += 1
                inner = [re.sub(r"^\s*>\s?", "", x) for x in lines[i:j]]
                out.append(("block", f"<blockquote>{self.blocks(inner)}</blockquote>"))
                i = j
                continue
            if re.match(r"^(-{3,}|\*{3,})$", stripped):
                out.append(("block", "<hr>"))
                i += 1
                continue
            j = i
            para = []
            while j < len(lines) and lines[j].strip() and not re.match(r"^(#{1,4}\s|:::|::caption|```|\||>)", lines[j].strip()) and not LIST_RE.match(lines[j]):
                para.append(lines[j].strip())
                j += 1
            if not para:  # a line no rule took; treat as text
                para, j = [stripped], i + 1
            out.append(("block", f"<p>{self.il(' '.join(para))}</p>"))
            i = j
        # group consecutive idea cards
        html_out, k = [], 0
        layout = self.theme["components"].get("idea_layout", "grid")
        while k < len(out):
            if out[k][0] == "idea":
                cards = []
                while k < len(out) and out[k][0] == "idea":
                    cards.append(out[k][1])
                    k += 1
                cls = "idea-grid stack" if layout == "stack" else f"idea-grid count-{len(cards)}"
                html_out.append(f'<div class="{cls}">' + "\n".join(cards) + "</div>")
            else:
                html_out.append(out[k][1])
                k += 1
        return "\n".join(html_out)

    def list(self, lines: list[str], cls: str = "") -> str:
        items: list[list[str]] = []
        ordered = None
        for line in lines:
            m = LIST_RE.match(line)
            if m and len(m.group(1)) < 2:
                if ordered is None:
                    ordered = m.group(2)[0].isdigit()
                items.append([m.group(3)])
            elif items:
                items[-1].append(line.strip())
        tagname = "ol" if ordered else "ul"
        attr = f' class="{cls}"' if cls else ""
        body = "\n".join(f"<li>{self.il(' '.join(x))}</li>" for x in items)
        return f"<{tagname}{attr}>\n{body}\n</{tagname}>"

    def table(self, lines: list[str], cls: str = "") -> str:
        def cells(row: str) -> list[str]:
            row = row.strip()
            if row.startswith("|"):
                row = row[1:]
            if row.endswith("|"):
                row = row[:-1]
            return [c.strip() for c in re.split(r"(?<!\\)\|", row)]
        head = cells(lines[0])
        rows = [cells(r) for r in lines[2:]]
        th = "".join(f'<th scope="col">{self.il(h)}</th>' for h in head)
        trs = "\n".join("<tr>" + "".join(f"<td>{self.il(c)}</td>" for c in r) + "</tr>" for r in rows)
        attr = f' class="{cls}"' if cls else ""
        return f'<div class="table-wrap"><table{attr}><thead><tr>{th}</tr></thead><tbody>\n{trs}\n</tbody></table></div>'

    def mermaid(self, body: str, caption: str | None) -> str:
        self.has_mermaid = True
        cap = f"<figcaption>{self.il(caption)}</figcaption>" if caption else ""
        return f'<figure class="diagram"><pre class="mermaid">{html.escape(body)}</pre>{cap}</figure>'

    def directive(self, name: str, attrs: dict, lines: list[str], base: int) -> str:
        tag = attrs.get("tag")
        badge = self.il("{" + tag + "}") if tag in BADGES else ""
        if tag and tag not in BADGES:
            warn(f"{self.source}:{base}: tag={tag} is not one of {', '.join(BADGES)}")
        if name == "lead":
            label = attrs.get("label", "The answer")
            return (f'<aside class="lead" aria-label="{html.escape(label)}"><p class="lead-label">'
                    f'<span class="name">{html.escape(label)}</span>{badge}</p>{self.blocks(lines, base)}</aside>')
        if name == "note":
            tone = attrs.get("tone", "info")
            label = attrs.get("label")
            head = f'<p class="note-label">{html.escape(label)} {badge}</p>' if label else ""
            return f'<aside class="note tone-{html.escape(tone)}">{head}{self.blocks(lines, base)}</aside>'
        if name == "quote":
            who = attrs.get("cite")
            if not who:
                warn(f"{self.source}:{base}: :::quote needs cite=\"who, where\"")
            parts = [f'<span class="who">{html.escape(who or "Unattributed")}</span>']
            if attrs.get("date"):
                parts.append(html.escape(attrs["date"]))
            else:
                warn(f"{self.source}:{base}: :::quote has no date=; say when it was said or read")
            if attrs.get("href"):
                parts.append(f'<a href="{html.escape(attrs["href"])}">link</a>')
            if badge:
                parts.append(badge)
            cap = ", ".join(parts)
            return f'<figure class="quote"><blockquote>{self.blocks(lines, base)}</blockquote><figcaption>{cap}</figcaption></figure>'
        if name == "idea":
            title = attrs.get("title") or "Untitled idea"
            fields: list[list[str]] = []
            for line in lines:
                m = FIELD_RE.match(line.strip())
                if m and not line.startswith((" ", "\t")):
                    fields.append([m.group(1), m.group(2)])
                elif fields and line.strip():
                    fields[-1][1] += " " + line.strip()
            if not fields:
                warn(f"{self.source}:{base}: idea '{title}' has no 'Field: value' lines")
            dl = "".join(
                f'<div class="field-{slug(k, set())}"><dt>{html.escape(k)}</dt><dd>{self.il(v)}</dd></div>'
                for k, v in fields)
            return f'<article class="idea"><header><h3>{html.escape(title)}</h3>{badge}</header><dl>{dl}</dl></article>'
        if name == "diagram":
            body = "\n".join(lines)
            body = re.sub(r"^\s*```\s*mermaid\s*\n|\n\s*```\s*$", "", body.strip() + "\n").strip()
            return self.mermaid(body, attrs.get("caption"))
        if name == "states":
            tbl = [x for x in lines if x.strip().startswith("|")]
            if len(tbl) < 3:
                raise RenderError(f"{self.source}:{base}: :::states needs a table with a header row")
            return self.table(tbl, "state-table")
        list_lines = [x for x in lines if x.strip()]
        if not list_lines or not LIST_RE.match(list_lines[0]):
            raise RenderError(f"{self.source}:{base}: :::{name} expects a list")
        cls = {"ranked": "ranked", "invariants": "invariants", "risks": "marked risks",
               "questions": "marked questions", "skip": "marked skip", "sources": "sources"}[name]
        rendered = self.list(list_lines, cls)
        if name in ("ranked", "invariants"):
            rendered = rendered.replace("<ul", "<ol", 1).replace("</ul>", "</ol>")
        else:
            rendered = rendered.replace("<ol", "<ul", 1).replace("</ol>", "</ul>")
        return rendered


# ---------------------------------------------------------------- document

def parse_front_matter(text: str) -> tuple[dict, list[str], int]:
    lines = text.splitlines()
    meta: dict = {}
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                for raw in lines[1:idx]:
                    if ":" in raw:
                        k, v = raw.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"')
                return meta, lines[idx + 1:], idx + 1
        raise RenderError("front matter opened with --- but never closed")
    return meta, lines, 0


SENTENCE_END = re.compile(r"(?<=[.!?])[\"\u201d')]?\s+(?=[A-Z0-9\"\u201c(])")


def plain_text(text: str) -> str:
    text = re.sub(r"\{[a-z]+(?::[^}]*)?\}", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    return [x for x in SENTENCE_END.split(plain_text(text)) if x]


def prose_blocks(lines: list[str], offset: int):
    """Yield (line number, text) for prose the sentence check reads: paragraphs,
    list items, captions, the lead and idea fields. Quotes, tables, code,
    diagrams and state tables are skipped."""
    skip_until_close = None
    depth = 0
    in_fence = False
    block, start = [], 0

    def flush():
        nonlocal block
        if block:
            yield_list.append((start, " ".join(block)))
        block = []

    yield_list: list[tuple[int, str]] = []
    for idx, raw in enumerate(lines):
        n = offset + idx + 1
        line = raw.strip()
        if line.startswith("```"):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^:::(\w[\w-]*)", line)
        if m:
            flush()
            if skip_until_close is None and m.group(1) in ("quote", "states", "diagram"):
                skip_until_close = depth
            depth += 1
            continue
        if line == ":::":
            flush()
            depth -= 1
            if skip_until_close is not None and depth == skip_until_close:
                skip_until_close = None
            continue
        if skip_until_close is not None:
            continue
        if not line or line.startswith(("|", "#", ">")):
            flush()
            continue
        if line.startswith("::caption"):
            flush()
            yield_list.append((n, line[len("::caption"):]))
            continue
        item = re.match(r"^(?:[-*]|\d+\.)\s+(.*)$", line) or re.match(r"^[A-Z][A-Za-z' ]{0,30}:\s+(.*)$", line)
        if item:
            flush()
            block, start = [item.group(1)], n
            continue
        if not block:
            start = n
        block.append(line)
    flush()
    return yield_list


def lint(text: str, meta: dict, r: Renderer, theme: dict, body_lines: list[str], offset: int) -> None:
    src = r.source
    if not meta.get("title"):
        warn(f"{src}: no title in front matter")
    if not meta.get("summary"):
        warn(f"{src}: no summary in front matter; say what this is and the main finding in two sentences")
    elif len(sentences(meta["summary"])) != 2:
        warn(f"{src}: the summary has {len(sentences(meta['summary']))} sentences; make it exactly two")
    limit = int(theme["voice"].get("max_sentence_words", 25))
    for n, block in prose_blocks(body_lines, offset):
        for sent in sentences(block):
            words = len(sent.split())
            if words > limit:
                warn(f"{src}:{n}: sentence of {words} words (limit {limit}): \"{' '.join(sent.split()[:8])} ...\"")
    if "lead" not in r.directives:
        warn(f"{src}: no :::lead; open with the answer in plain words")
    elif r.toc and r.directives.index("lead") > 2:
        warn(f"{src}: the :::lead comes late; put it in the first section")
    if "sources" not in r.directives:
        warn(f"{src}: no :::sources list; say what you read and what you did not")
    if r.counts["sourced"] + r.counts["judgment"] == 0:
        warn(f"{src}: no {{sourced}} or {{judgment}} labels; mark where claims came from")
    # Every section needs a sourced, judgment or placeholder label, except the
    # first section (the plain version, whose lead carries its own tag) and a
    # section holding :::sources (it is the labelling).
    for idx, sec in enumerate(r.sections):
        if idx == 0 or "sources" in sec["directives"]:
            continue
        if sec["labels"] == 0:
            warn(f"{src}:{sec['line']}: section '{sec['title']}' has no {{sourced}}, {{judgment}} or {{placeholder}} label")
    voice = theme["voice"]
    banned = [w.lower() for w in voice.get("banned_words", []) + voice.get("add_banned_words", [])]
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith(("http", "```")):
            continue
        low = line.lower()
        for word in banned:
            if re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", low):
                warn(f"{src}:{n}: avoid '{word}' (voice.banned_words)")
        if "\u2014" in line or " \u2013 " in line:
            warn(f"{src}:{n}: dash used as punctuation; use a period or a comma")


STYLE_OPTIONS = {
    # option: (Nessa default, allowed values). The defaults are the plain-text
    # treatments; the other values exist only so a theme can opt in.
    "labels": ("text", {"text", "badge"}),
    "status": ("text", {"text", "pill"}),
    "ranks": ("numeral", {"numeral", "circle"}),
    "markers": ("bullet", {"bullet", "symbol"}),
    "callout": ("border", {"border", "tint", "bar"}),
}


def style_attrs(comp: dict) -> str:
    chosen = comp.get("style", {})
    out = []
    for key, value in chosen.items():
        if key not in STYLE_OPTIONS:
            warn(f"unknown components.style.{key} ignored")
            continue
        default, allowed = STYLE_OPTIONS[key]
        if value not in allowed:
            warn(f"components.style.{key} = {value!r} is not one of {sorted(allowed)}; using {default!r}")
            continue
        if value != default:
            out.append(f' data-{key}="{html.escape(value)}"')
    return "".join(out)


def render(args) -> int:
    template = TEMPLATE.read_text(encoding="utf-8")
    theme, origin, used = resolve_theme(args, template)
    doc_path = Path(args.doc)
    text = doc_path.read_text(encoding="utf-8")
    meta, lines, offset = parse_front_matter(text)
    r = Renderer(theme, doc_path.name)
    body = r.blocks(lines, offset)
    lint(text, meta, r, theme, lines, offset)

    comp = theme["components"]
    title = meta.get("title", doc_path.stem)
    kind = meta.get("kind", "")
    kind_label = comp.get("kinds", {}).get(kind, kind.title() if kind else "")
    header = []
    if comp.get("eyebrow", True) and kind_label:
        header.append(f'<p class="eyebrow">{html.escape(kind_label)}</p>')
    header.append(f"<h1>{inline(title, theme)}</h1>")
    if meta.get("summary"):
        header.append(f'<p class="summary">{inline(meta["summary"], theme)}</p>')
    facts = [meta.get(k) for k in ("author", "date", "status") if meta.get(k)]
    if facts:
        header.append('<ul class="meta">' + "".join(f"<li>{html.escape(f)}</li>" for f in facts) + "</ul>")

    toc_mode = comp.get("toc", "left")
    if toc_mode not in ("left", "right", "inline", "off"):
        warn(f"components.toc = {toc_mode!r} is not left, right, inline or off; using 'left'")
        toc_mode = "left"
    toc = toc_side = toc_open = toc_script = layout_class = ""
    if len(r.toc) >= 3 and toc_mode == "inline":
        items = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in r.toc)
        toc = f'<nav class="toc" aria-label="Contents"><h2>Contents</h2><ol>{items}</ol></nav>'
    elif len(r.toc) >= 3 and toc_mode in ("left", "right"):
        layout_class = f" has-toc toc-{toc_mode}"
        toc_side, toc_open = sidebar(r.toc_all, toc_mode)
        toc_script = TOC_SCRIPT

    mermaid = ""
    if r.has_mermaid and comp.get("mermaid", "cdn") == "cdn":
        mermaid = MERMAID_SCRIPT.replace("{{SRC}}", MERMAID_SRC)

    name = theme.get("meta", {}).get("name", "nessa")
    footer = f"Rendered with the {html.escape(name)} theme by Nessa build-artifacts."
    counts = r.counts
    if counts["placeholder"]:
        footer += f" Contains {counts['placeholder']} placeholder value(s); check them before relying on this page."

    out = (template.replace("{{THEME_NAME}}", html.escape(name))
           .replace("{{STYLE_ATTRS}}", style_attrs(comp))
           .replace("{{TITLE}}", html.escape(re.sub(r"\{[^}]*\}", "", title).strip()))
           .replace("{{THEME_CSS}}", theme_css(theme))
           .replace("{{HEADER}}", "\n".join(header))
           .replace("{{TOC}}", toc)
           .replace("{{TOC_SIDE}}", toc_side)
           .replace("{{TOC_OPEN}}", toc_open)
           .replace("{{TOC_SCRIPT}}", toc_script)
           .replace("{{LAYOUT_CLASS}}", layout_class)
           .replace("{{BODY}}", body)
           .replace("{{FOOTER}}", footer)
           .replace("{{MERMAID}}", mermaid))
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"wrote {args.output} (theme layers: {' > '.join(reversed(used))})", file=sys.stderr)
    return 0


def sidebar(entries: list[tuple[int, str, str]], side_name: str = "left") -> tuple[str, str]:
    """The contents sidebar (left or right): h2 entries with h3 entries nested."""
    parts, open_sub = [], False
    for level, ident, text in entries:
        link = f'<a href="#{ident}">{html.escape(text)}</a>'
        if level == 2:
            if open_sub:
                parts.append("</ol>")
                open_sub = False
            if parts:
                parts.append("</li>")
            parts.append(f"<li>{link}")
        elif parts:
            if not open_sub:
                parts.append("<ol>")
                open_sub = True
            parts.append(f"<li>{link}</li>")
    if open_sub:
        parts.append("</ol>")
    if parts:
        parts.append("</li>")
    # Sidebar-panel icon: a rounded rectangle with a vertical divider. The
    # narrow column is on the left for toc=left, and mirrored for toc=right.
    divider_x = "8" if side_name == "left" else "12"
    icon = (
        '<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">'
        '<rect x="3.25" y="3.25" width="13.5" height="13.5" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        f'<path d="M{divider_x} 3.25v13.5" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        '</svg>'
    )
    side = ('<aside class="toc-side" id="toc-side" aria-labelledby="toc-title">'
            '<div class="toc-head"><p class="toc-title" id="toc-title">Contents</p>'
            '<button type="button" class="toc-btn toc-icon toc-toggle" aria-expanded="true" aria-controls="toc-list" aria-label="Hide contents" title="Hide contents" hidden>'
            f'{icon}</button>'
            '<button type="button" class="toc-btn toc-close" hidden>Close</button></div>'
            f'<nav id="toc-list" aria-labelledby="toc-title"><ol>{"".join(parts)}</ol></nav></aside>')
    at = " at-left" if side_name == "left" else ""
    opener = (f'<button type="button" class="toc-btn toc-icon toc-open{at}" aria-expanded="false" aria-controls="toc-side" aria-label="Show contents" title="Show contents" hidden>'
              f'{icon}<span class="toc-open-label">Contents</span></button>'
              '<div class="toc-scrim" hidden></div>')
    return side, opener


TOC_SCRIPT = """<script>
// Sidebar contents. Plain JS, no dependencies. Without JS the list is static.
(function () {
  var root = document.documentElement;
  var side = document.getElementById("toc-side");
  if (!side) return;
  var layout = side.parentElement;
  var list = document.getElementById("toc-list");
  var toggle = side.querySelector(".toc-toggle");
  var closeBtn = side.querySelector(".toc-close");
  var openBtn = document.querySelector(".toc-open");
  var scrim = document.querySelector(".toc-scrim");
  var wide = window.matchMedia("(min-width: 1000px)");
  var KEY = "nessa-artifact-toc-collapsed";
  var lastFocus = null;
  toggle.hidden = closeBtn.hidden = openBtn.hidden = false;

  function saved() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
  function save(v) { try { localStorage.setItem(KEY, v ? "1" : "0"); } catch (e) {} }

  function setCollapsed(collapsed) {
    var c = collapsed && wide.matches;
    layout.classList.toggle("toc-collapsed", c);
    list.hidden = c;
    toggle.setAttribute("aria-expanded", String(!c));
    var label = c ? "Show contents" : "Hide contents";
    toggle.setAttribute("aria-label", label);
    toggle.setAttribute("title", label);
  }
  toggle.addEventListener("click", function () {
    var c = !layout.classList.contains("toc-collapsed");
    save(c);
    setCollapsed(c);
  });

  function isOpen() { return root.classList.contains("toc-panel-open"); }
  function openPanel() {
    lastFocus = document.activeElement;
    root.classList.add("toc-panel-open");
    openBtn.setAttribute("aria-expanded", "true");
    side.setAttribute("role", "dialog");
    side.setAttribute("aria-modal", "true");
    scrim.hidden = false;
    closeBtn.focus();
  }
  function closePanel(returnFocus) {
    if (!isOpen()) return;
    root.classList.remove("toc-panel-open");
    openBtn.setAttribute("aria-expanded", "false");
    side.removeAttribute("role");
    side.removeAttribute("aria-modal");
    scrim.hidden = true;
    if (returnFocus !== false) (lastFocus || openBtn).focus();
  }
  openBtn.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", function () { closePanel(); });
  scrim.addEventListener("click", function () { closePanel(); });
  side.addEventListener("click", function (e) {
    if (!wide.matches && e.target.closest("a")) closePanel(false);
  });
  document.addEventListener("keydown", function (e) {
    if (!isOpen()) return;
    if (e.key === "Escape") { e.preventDefault(); closePanel(); return; }
    if (e.key === "Tab") {
      var f = side.querySelectorAll("button:not([hidden]), a[href]");
      var vis = Array.prototype.filter.call(f, function (el) { return el.offsetParent !== null; });
      if (!vis.length) return;
      var first = vis[0], last = vis[vis.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  function onMode() { closePanel(false); setCollapsed(saved()); }
  if (wide.addEventListener) wide.addEventListener("change", onMode); else wide.addListener(onMode);
  onMode();

  // Mark the section being read: the last heading above a line near the top.
  var links = Array.prototype.slice.call(list.querySelectorAll("a"));
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); });
  var ticking = false;
  function mark() {
    ticking = false;
    var line = window.innerHeight * 0.25, current = 0;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i] && heads[i].getBoundingClientRect().top <= line) current = i;
    }
    var docH = document.documentElement.scrollHeight;
    if (docH > window.innerHeight + 2 && window.innerHeight + window.scrollY >= docH - 2) current = heads.length - 1;
    links.forEach(function (a, i) {
      if (i === current) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(mark); } }, { passive: true });
  mark();
})();
</script>"""


MERMAID_SCRIPT = """<script type="module">
// Optional: the only network request. Diagrams fall back to their source text.
const toColor = (name) => {
  const probe = document.createElement("span");
  probe.style.color = `var(${name})`;
  document.body.appendChild(probe);
  const c = getComputedStyle(probe).color;
  probe.remove();
  const ctx = document.createElement("canvas").getContext("2d");
  ctx.fillStyle = c;
  return ctx.fillStyle;
};
try {
  const { default: mermaid } = await import("{{SRC}}");
  const font = getComputedStyle(document.body).fontFamily;
  mermaid.initialize({
    startOnLoad: false,
    theme: "base",
    securityLevel: "strict",
    themeVariables: {
      fontFamily: font,
      fontSize: "14px",
      background: toColor("--color-surface"),
      primaryColor: toColor("--color-surface-2"),
      primaryBorderColor: toColor("--color-muted"),
      primaryTextColor: toColor("--color-text"),
      lineColor: toColor("--color-muted"),
      textColor: toColor("--color-text"),
      secondaryColor: toColor("--color-surface"),
      tertiaryColor: toColor("--color-surface"),
      labelBackgroundColor: toColor("--color-surface"),
    },
  });
  await mermaid.run({ querySelector: "pre.mermaid" });
} catch (err) {
  console.warn("mermaid did not load; showing diagram source", err);
}
document.documentElement.dataset.rendered = "true";
</script>"""


def voice_brief(args) -> int:
    template = TEMPLATE.read_text(encoding="utf-8")
    theme, origin, used = resolve_theme(args, template)
    v = theme["voice"]
    register = {
        "plain": "Plain: follow wdym as written. Short sentences, everyday words, contractions are fine.",
        "formal": "Formal: no contractions and no asides, but still plain words and the answer first.",
        "terse": "Terse: the shortest sentences that stay exact. Lists may come earlier, never before the lead.",
    }.get(v.get("register"), f"Register: {v.get('register')}")
    person = {
        "first": "Write as 'I'. Label opinion 'my judgment'.",
        "we": "Write as 'we'. Label opinion 'our judgment'.",
        "neutral": "No first person. Label opinion 'judgment'.",
    }.get(v.get("person"), f"Person: {v.get('person')}")
    print("# Voice for this artifact")
    print(f"Layers, winning first: {' > '.join(reversed(used))}\n")
    print("Sentence rules: follow the 'Sentence rules' section of SKILL.md. They are")
    print("enough on their own. Reading the wdym skill is optional; if you read it,")
    print("it wins where the two differ.\n")
    print("## Always (fixed, no override can change these)")
    for rule in v["floor"]["rules"]:
        print(f"- {rule}")
    print("\n## This theme")
    print(f"- {register}")
    print(f"- {person}")
    print(f"- Reader: {v.get('audience')}.")
    print(f"- Split sentences longer than about {v.get('max_sentence_words')} words.")
    for rule in v.get("add_rules", []):
        print(f"- {rule}")
    banned = v.get("banned_words", []) + v.get("add_banned_words", [])
    print(f"\n## Do not use\n{', '.join(banned)}")
    return 0


def explain(args) -> int:
    template = TEMPLATE.read_text(encoding="utf-8")
    theme, origin, used = resolve_theme(args, template)
    print("Layers, winning first: " + " > ".join(reversed(used)))
    for path, layer in sorted(origin.items()):
        if path[:2] == ("voice", "floor"):
            continue
        value = theme
        for key in path:
            value = value[key]
        print(f"{'.'.join(path)} = {json.dumps(value)}   [{layer}]")
    print("Tokens not listed above use the template.html defaults.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("doc", nargs="?", help="the document, Markdown with directives")
    p.add_argument("-o", "--output", help="output HTML path (default: DOC with .html)")
    p.add_argument("--project", help="folder to search upward from for .nessa/artifacts/theme.toml")
    p.add_argument("--user", help="user theme file (default: $NESSA_ARTIFACTS_THEME or ~/.nessa/artifacts/theme.toml)")
    p.add_argument("--theme", action="append", help="extra theme file, applied last; repeatable")
    p.add_argument("--no-user", action="store_true", help="ignore the user theme")
    p.add_argument("--no-project", action="store_true", help="ignore the project theme")
    p.add_argument("--voice", action="store_true", help="print the resolved writing voice and exit")
    p.add_argument("--explain-theme", action="store_true", help="print each theme key and its layer")
    p.add_argument("--strict", action="store_true", help="exit 1 when there are warnings")
    args = p.parse_args(argv)
    try:
        if args.voice:
            code = voice_brief(args)
        elif args.explain_theme:
            code = explain(args)
        else:
            if not args.doc:
                p.error("give a document, or --voice, or --explain-theme")
            args.output = args.output or str(Path(args.doc).with_suffix(".html"))
            code = render(args)
    except RenderError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return 1 if (args.strict and warnings) else code


if __name__ == "__main__":
    sys.exit(main())
