#!/usr/bin/env python3
"""Regenerate the tool sections of docs/api/*.md from razorpay-mcp-server source.

Usage:
    git clone --depth 1 https://github.com/razorpay/razorpay-mcp-server.git /tmp/rzp-mcp
    python scripts/refresh_tool_docs.py /tmp/rzp-mcp

Everything above the `<!-- GENERATED` marker in each docs/api file is hand-written and kept.
Everything below it is rebuilt from the Go tool definitions (name, description, params, constraints).
Toolset / R-W / remote / REST columns come from the table in REFERENCE.md, so a tool that exists in
source but not in REFERENCE.md aborts the run: classify it there first.
"""
import glob
import os
import re
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {  # docs/api file -> toolsets it covers
    "payments": ["payments"], "orders": ["orders"], "payment_links": ["payment_links"],
    "refunds": ["refunds"], "qr_codes": ["qr_codes"], "settlements": ["settlements"],
    "payouts": ["payouts"], "recurring": ["registration_links"],
    "checkout_integration": ["checkout_integration"],
}
STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"|`([^`]*)`')
PARAM_RE = re.compile(r'mcpgo\.With(String|Number|Boolean|Object|Array|Integer)\(\s*"([^"]+)",(.*?)\n\t\t\),', re.S)
TOOL_RE = re.compile(r'mcpgo\.NewTool\(\s*"([^"]+)",\s*(.*?),\s*(?://[^\n]*)?\n\s*parameters,', re.S)
ROW_RE = re.compile(r"\| `([a-z_]+)` \| ([a-z_]+) \| (R|W)[^|]*\| (✅|❌) \| (.*?) \| (.*?) \|$")


def go_string(expr):
    parts = []
    for m in STR_RE.finditer(expr):
        if m.group(1) is not None:
            parts.append(m.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\'))
        else:
            parts.append(m.group(2))
    return "".join(parts)


def parse_params(body):
    params = []
    for m in PARAM_RE.finditer(body):
        typ, name, rest = m.groups()
        d = re.search(r'mcpgo\.Description\((.*?)\),?[ \t]*(?://[^\n]*)?\n', rest + '\n', re.S)
        cons = ["REQUIRED"] if 'mcpgo.Required()' in rest else []
        for c in ['Min', 'Max', 'Pattern', 'Enum', 'DefaultValue', 'MaxProperties']:
            cons += [f"{c}={cm.group(1).strip()}" for cm in re.finditer(r'mcpgo\.' + c + r'\(([^)]*)\)', rest)]
        params.append((name, typ.lower(), cons, re.sub(r'\s+', ' ', go_string(d.group(1)) if d else "")))
    return params


def parse_tools(src_root):
    pkg = os.path.join(src_root, "pkg", "razorpay")
    files = sorted(f for f in glob.glob(pkg + "/*.go") + glob.glob(pkg + "/integrations/*.go")
                   if not f.endswith("_test.go"))
    tools = []
    for f in files:
        src = open(f, encoding="utf-8").read()
        starts = [m.start() for m in re.finditer(r'^func ', src, re.M)] + [len(src)]
        for a, b in zip(starts, starts[1:]):
            fn = src[a:b]
            m = TOOL_RE.search(fn)
            if m:
                tools.append({"tool": m.group(1), "desc": re.sub(r'[ \t]+', ' ', go_string(m.group(2))).strip(),
                              "params": parse_params(fn)})
    return tools


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src_root = sys.argv[1]
    commit = subprocess.run(["git", "-C", src_root, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    meta = {}
    for line in open(os.path.join(SKILL, "REFERENCE.md"), encoding="utf-8"):
        m = ROW_RE.match(line.strip())
        if m:
            meta[m.group(1)] = m.groups()[1:5]
    tools = parse_tools(src_root)
    names = {t["tool"] for t in tools}
    if names - meta.keys():
        sys.exit(f"New tools not in REFERENCE.md — add rows first: {sorted(names - meta.keys())}")
    if meta.keys() - names:
        print(f"WARNING: REFERENCE.md lists tools no longer in source: {sorted(meta.keys() - names)}")

    for fname, toolsets in FILES.items():
        path = os.path.join(SKILL, "docs", "api", f"{fname}.md")
        head = open(path, encoding="utf-8").read().split("<!-- GENERATED")[0].rstrip() + "\n\n"
        out = [f"<!-- GENERATED from razorpay-mcp-server@{commit} by scripts/refresh_tool_docs.py — "
               "edit the hand-written part above this line only. -->", ""]
        for t in (t for t in tools if meta[t["tool"]][0] in toolsets):
            _, rw, remote, rest = meta[t["tool"]]
            out += [f"## `{t['tool']}`", "", f"**{'Write' if rw == 'W' else 'Read'}** · remote {remote} · {rest}", "",
                    "> " + t["desc"].replace("\n\n", "\n>\n> ").replace("\n", "\n> "), ""]
            if t["params"]:
                out += ["| Param | Type | Constraints | Description |", "|---|---|---|---|"]
                out += [f"| `{n}` | {ty} | {'; '.join(c).replace('|', chr(92) + '|') or '—'} | "
                        f"{d.strip().replace('|', chr(92) + '|') or '—'} |" for n, ty, c, d in t["params"]]
                out.append("")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(head + "\n".join(out))
        print(f"{fname}.md: {sum(1 for t in tools if meta[t['tool']][0] in toolsets)} tools")


if __name__ == "__main__":
    main()
