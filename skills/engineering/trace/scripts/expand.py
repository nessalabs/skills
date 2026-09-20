#!/usr/bin/env python3
"""Expand one hop of a call path from the syntax tree, not from reading files.

    expand.py SYMBOL [--root DIR] [--lang LANG] [--in FILE] [--depth N] [--json]

Prints, for SYMBOL (a function name, or `Type::method` / `Class.method`):

  def   <file>:<start>-<end>   <signature line>
  the calls made in its body, in source order, each with its line, a tag
  when the callee looks like a lock, wait, handoff, spawn, or I/O, and the
  candidate definition sites of that callee in the repo.

Only the body of SYMBOL is parsed; nothing else is read. Expand the callee
you care about next by running the script again on it. `--depth N` does that
recursively for callees defined in the repo, breadth-first, bounded.

Needs ast-grep (https://ast-grep.github.io): `ast-grep` or `sg` on PATH, or
node, in which case it runs `npx -y -p @ast-grep/cli ast-grep`.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import OrderedDict

EXT_LANG = {
    ".rs": "rust", ".py": "python", ".go": "go",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx",
    ".java": "java", ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp",
    ".kt": "kotlin", ".rb": "ruby", ".cs": "csharp",
}

# How a definition named NAME looks in each language, as an ast-grep rule
# body (the `rule:` value). {name} is a regex on the identifier.
DEF_RULES = {
    "rust": lambda n: {"any": [
        {"kind": "function_item", "has": {"field": "name", "regex": n}},
        {"kind": "function_signature_item", "has": {"field": "name", "regex": n}},
    ]},
    "python": lambda n: {"kind": "function_definition", "has": {"field": "name", "regex": n}},
    "go": lambda n: {"any": [
        {"kind": "function_declaration", "has": {"field": "name", "regex": n}},
        {"kind": "method_declaration", "has": {"field": "name", "regex": n}},
    ]},
    "java": lambda n: {"any": [
        {"kind": "method_declaration", "has": {"field": "name", "regex": n}},
        {"kind": "constructor_declaration", "has": {"field": "name", "regex": n}},
    ]},
    "kotlin": lambda n: {"kind": "function_declaration", "has": {"regex": n, "kind": "simple_identifier"}},
    "ruby": lambda n: {"any": [
        {"kind": "method", "has": {"field": "name", "regex": n}},
        {"kind": "singleton_method", "has": {"field": "name", "regex": n}},
    ]},
    "csharp": lambda n: {"kind": "method_declaration", "has": {"field": "name", "regex": n}},
    "c": lambda n: {"kind": "function_definition", "has": {
        "kind": "function_declarator", "stopBy": "end", "has": {"field": "declarator", "regex": n}}},
    "cpp": lambda n: {"kind": "function_definition", "has": {
        "kind": "function_declarator", "stopBy": "end", "has": {"field": "declarator", "regex": n}}},
}
for _js in ("javascript", "typescript", "tsx"):
    DEF_RULES[_js] = lambda n: {"any": [
        {"kind": "function_declaration", "has": {"field": "name", "regex": n}},
        {"kind": "method_definition", "has": {"field": "name", "regex": n}},
        {"kind": "variable_declarator", "all": [
            {"has": {"field": "name", "regex": n}},
            {"has": {"field": "value", "any": [{"kind": "arrow_function"}, {"kind": "function_expression"}]}},
        ]},
    ]}

# Optional container (impl / class / type) that qualifies a `Type::name` lookup.
CONTAINER_RULES = {
    "rust": lambda t: {"kind": "impl_item", "has": {"field": "type", "regex": t, "stopBy": "end"}},
    "python": lambda t: {"kind": "class_definition", "has": {"field": "name", "regex": t}},
    "go": lambda t: {"kind": "method_declaration", "has": {"field": "receiver", "regex": t, "stopBy": "end"}},
    "java": lambda t: {"kind": "class_declaration", "has": {"field": "name", "regex": t}},
    "csharp": lambda t: {"kind": "class_declaration", "has": {"field": "name", "regex": t}},
    "ruby": lambda t: {"kind": "class", "has": {"field": "name", "regex": t}},
    "kotlin": lambda t: {"kind": "class_declaration", "has": {"regex": t, "kind": "type_identifier"}},
}
for _js in ("javascript", "typescript", "tsx"):
    CONTAINER_RULES[_js] = lambda t: {"kind": "class_declaration", "has": {"field": "name", "regex": t}}

# Extra things worth marking that are not calls.
MARK_RULES = {
    "rust": {"await": {"kind": "await_expression"}, "unsafe": {"kind": "unsafe_block"},
             "macro": {"kind": "macro_invocation"}, "spawn-closure": {"kind": "closure_expression"}},
    "python": {"await": {"kind": "await"}, "with": {"kind": "with_statement"}},
    "javascript": {"await": {"kind": "await_expression"}},
    "typescript": {"await": {"kind": "await_expression"}},
    "tsx": {"await": {"kind": "await_expression"}},
    "go": {"go": {"kind": "go_statement"}, "defer": {"kind": "defer_statement"},
           "select": {"kind": "select_statement"}, "chan-send": {"kind": "send_statement"}},
}

TAGS = [
    ("lock", r"(?i)(^|[._:])(lock|try_lock|rlock|wlock|acquire|mutex|guard|synchronized)(_.*)?$"),
    ("wait", r"(?i)(wait|park|sleep|block_on|join|recv|await|poll|select|timeout)"),
    ("handoff", r"(?i)(notify|wake|signal|send|unpark|post|emit|dispatch|publish|broadcast|resolve|reject)"),
    ("spawn", r"(?i)(spawn|thread::|go\b|fork|exec|run_in_executor|create_task|start)"),
    ("io", r"(?i)(^|[._:])(read|write|flush|open|close|connect|accept|fetch|request|query|exec|send_to|recv_from)(_.*)?$"),
    ("state", r"(?i)(insert|remove|push|pop|store|swap|fetch_add|fetch_sub|set_|update|clear|take|replace|reset|inc_|dec_)"),
]


def find_ast_grep():
    for name in ("ast-grep", "sg"):
        p = shutil.which(name)
        if p:
            try:
                out = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=10).stdout
                if "ast-grep" in out:
                    return [p]
            except Exception:
                pass
    if shutil.which("npx"):
        return ["npx", "-y", "-p", "@ast-grep/cli", "ast-grep"]
    sys.exit("expand.py: ast-grep not found. Install it (brew install ast-grep | cargo install ast-grep | npm i -g @ast-grep/cli) or have node on PATH.")


AG = None


def scan(rule, lang, paths, root):
    """Run one inline rule over paths; return the match list (ast-grep JSON)."""
    global AG
    AG = AG or find_ast_grep()
    spec = json.dumps({"id": "x", "language": lang, "rule": rule})
    cmd = AG + ["scan", "--inline-rules", spec, "--json=compact"] + paths
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    if p.returncode not in (0, 1) and not p.stdout.strip():
        sys.stderr.write(p.stderr)
        return []
    try:
        return json.loads(p.stdout or "[]")
    except json.JSONDecodeError:
        sys.stderr.write(p.stderr)
        return []


def lang_for(path, fallback):
    return EXT_LANG.get(os.path.splitext(path)[1], fallback)


def split_symbol(sym):
    parts = re.split(r"::|\.", sym)
    return (parts[-2] if len(parts) > 1 else None), parts[-1]


def def_rule(lang, name, container=None):
    rule = DEF_RULES[lang]("^" + re.escape(name) + "$")
    if container and lang in CONTAINER_RULES:
        crx = "^" + re.escape(container) + "(<.*>)?$"
        rule = {"all": [rule, {"inside": dict(CONTAINER_RULES[lang](crx), stopBy="end")}]}
    return rule


def find_defs(sym, lang, root, paths):
    container, name = split_symbol(sym)
    hits = scan(def_rule(lang, name, container), lang, paths, root)
    if not hits and container:
        hits = scan(def_rule(lang, name), lang, paths, root)
    out = []
    for h in hits:
        s, e = h["range"]["start"]["line"] + 1, h["range"]["end"]["line"] + 1
        sig = h["text"].split("\n", 1)[0].strip()
        out.append({"file": h["file"], "start": s, "end": e, "sig": sig})
    return out


NOISE = {
    "Ok", "Err", "Some", "None", "Box", "Vec", "String", "Arc", "Rc", "Cell", "RefCell",
    "unwrap", "expect", "unwrap_or", "unwrap_or_else", "ok_or", "ok_or_else", "map", "map_err",
    "and_then", "is_some", "is_none", "is_ok", "is_err", "is_empty", "len", "clone", "as_ref",
    "as_mut", "as_bytes", "as_bytes_mut", "as_slice", "into", "from", "to_string", "to_owned",
    "to_vec", "iter", "into_iter", "collect", "get", "cloned", "copied", "borrow", "borrow_mut",
    "deref", "eq", "ne", "cmp", "min", "max", "abs", "format", "print", "println", "len", "str",
    "int", "float", "list", "dict", "set", "tuple", "isinstance", "range", "enumerate", "zip",
    "console.log", "JSON.stringify", "JSON.parse", "Object.keys", "Array.isArray", "parseInt",
}


def is_noise(callee, resolved):
    if resolved:
        return False
    seg = last_segment(callee)
    return seg in NOISE or callee in NOISE or (seg[:1].isupper() and "::" not in callee and "." not in callee)


def tag_for(callee):
    tags = [t for t, rx in TAGS if re.search(rx, callee)]
    return tags


def callees_of(d, lang, root):
    """Calls inside definition d, in source order, deduped by callee text."""
    # ast-grep has no range filter, so scan the file and keep the definition's lines.
    hits = scan({"pattern": "$F($$$)"}, lang, [d["file"]], root)
    seen = OrderedDict()
    for h in hits:
        line = h["range"]["start"]["line"] + 1
        if not (d["start"] <= line <= d["end"]):
            continue
        f = h.get("metaVariables", {}).get("single", {}).get("F", {}).get("text")
        if not f:
            continue
        f = re.sub(r"\s+", "", f)
        if f in seen:
            continue
        seen[f] = {"callee": f, "line": line, "tags": tag_for(f)}
    marks = []
    for label, r in MARK_RULES.get(lang, {}).items():
        for h in scan(r, lang, [d["file"]], root):
            line = h["range"]["start"]["line"] + 1
            if d["start"] <= line <= d["end"]:
                marks.append({"mark": label, "line": line, "text": h["text"].split("\n", 1)[0].strip()[:80]})
    marks.sort(key=lambda m: m["line"])
    return list(seen.values()), marks


def resolve_many(names, lang, root, paths):
    """One scan for all candidate names; bucket definitions by name."""
    if not names:
        return {}
    rx = "^(" + "|".join(re.escape(n) for n in names) + ")$"
    hits = scan(DEF_RULES[lang](rx), lang, paths, root)
    by = {}
    for h in hits:
        sig = h["text"].split("\n", 1)[0].strip()
        m = re.search(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b", sig)
        if not m:
            continue
        by.setdefault(m.group(1), []).append(
            {"file": h["file"], "line": h["range"]["start"]["line"] + 1, "sig": sig[:100]})
    return by


def last_segment(callee):
    # self.config.binary.is_quit -> is_quit ; Foo::bar -> bar ; obj.method -> method
    seg = re.split(r"::|\.", callee)[-1]
    seg = re.sub(r"<.*>$", "", seg)
    return seg


def expand(sym, lang, root, paths, depth, seen, out, in_file=None):
    defs = find_defs(sym, lang, root, [in_file] if in_file else paths)
    if not defs:
        out.append({"symbol": sym, "defs": [], "note": "no definition found (external crate, trait object, macro, or dynamic dispatch)"})
        return
    for d in defs:
        key = (d["file"], d["start"])
        if key in seen:
            continue
        seen.add(key)
        calls, marks = callees_of(d, lang, root)
        names = sorted({last_segment(c["callee"]) for c in calls})
        resolved = resolve_many(names, lang, root, paths)
        kept = []
        for c in calls:
            sites = resolved.get(last_segment(c["callee"]), [])
            sites.sort(key=lambda x: (x["file"] != d["file"], os.path.dirname(x["file"]) != os.path.dirname(d["file"]), x["file"], x["line"]))
            c["defined_at"] = sites[:5]
            if not is_noise(c["callee"], sites):
                kept.append(c)
        out.append({"symbol": sym, "def": d, "calls": kept, "marks": marks})
        if depth > 1:
            for c in kept:
                for site in c["defined_at"][:1]:
                    expand(last_segment(c["callee"]), lang, root, paths, depth - 1, seen, out, in_file=site["file"])


def render(out):
    lines = []
    for e in out:
        if not e.get("def"):
            lines.append(f"{e['symbol']}: {e.get('note','')}")
            continue
        d = e["def"]
        lines.append(f"def {d['file']}:{d['start']}-{d['end']}   {d['sig']}")
        rows = [("call", c["line"], c) for c in e["calls"]] + [("mark", m["line"], m) for m in e["marks"]]
        rows.sort(key=lambda r: r[1])
        for kind, line, x in rows:
            if kind == "call":
                tag = (" [" + ",".join(x["tags"]) + "]") if x["tags"] else ""
                where = "  ".join(f"-> {s['file']}:{s['line']}" for s in x["defined_at"]) or "-> (not defined in repo: external, trait, or builtin)"
                lines.append(f"  {line:>5}  {x['callee']}{tag}")
                lines.append(f"         {where}")
            else:
                lines.append(f"  {line:>5}  ~{x['mark']}  {x['text']}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol", help="function name, or Type::method / Class.method")
    ap.add_argument("--root", default=".", help="repository root to search (default: cwd)")
    ap.add_argument("--lang", help="ast-grep language id (rust, python, typescript, go, ...); inferred from --in or the first matching file otherwise")
    ap.add_argument("--in", dest="in_file", help="file that holds the definition, to skip the search")
    ap.add_argument("--depth", type=int, default=1, help="recursively expand callees defined in the repo (default 1)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    lang = a.lang or (lang_for(a.in_file, None) if a.in_file else None)
    if not lang:
        counts = {}
        for dp, dn, fn in os.walk(root):
            dn[:] = [x for x in dn if x not in ("node_modules", "target", ".git", "vendor", "dist", "build")]
            for f in fn:
                l = EXT_LANG.get(os.path.splitext(f)[1])
                if l:
                    counts[l] = counts.get(l, 0) + 1
        if not counts:
            sys.exit("expand.py: could not infer language; pass --lang")
        lang = max(counts, key=counts.get)
    paths = ["."]
    out = []
    expand(a.symbol, lang, root, paths, a.depth, set(), out, in_file=a.in_file)
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print(render(out))


if __name__ == "__main__":
    main()
