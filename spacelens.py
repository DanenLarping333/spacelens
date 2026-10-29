"""SpaceLens: read-only folder analysis with a standalone HTML report."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import heapq
from html import escape
import os
from pathlib import Path
import stat
import sys


def human(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:,.1f} {unit}"
        value /= 1024


def is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & 0x400
    )


def scan(folder, top=20):
    """Count logical file sizes, without opening file contents or following links."""
    if not 1 <= top <= 100:
        raise ValueError("Top must be between 1 and 100.")
    root = Path(os.path.abspath(os.path.expanduser(str(folder))))
    if is_link(root.lstat()):
        raise ValueError("Choose a real folder, not a symlink or junction.")
    if not root.is_dir():
        raise ValueError("The selected path is not a folder.")
    types, groups = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    largest, errors, stack = [], [], [root]
    total = count = skipped = error_count = directories = 0
    while stack:
        current = stack.pop()
        try:
            # Recheck queued directories; a changing filesystem is not a snapshot.
            if is_link(current.lstat()):
                skipped += 1
                continue
            with os.scandir(current) as entries:
                directories += 1
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if is_link(info):
                            skipped += 1
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            stack.append(Path(entry.path))
                            continue
                        if not stat.S_ISREG(info.st_mode):
                            skipped += 1
                            continue
                        relative = Path(entry.path).relative_to(root)
                        name = relative.as_posix()
                        size = info.st_size
                        kind = relative.suffix.lower() or "(no extension)"
                        group = relative.parts[0] if len(relative.parts) > 1 else "(root files)"
                        total += size
                        count += 1
                        for mapping, key in ((types, kind), (groups, group)):
                            mapping[key][0] += size
                            mapping[key][1] += 1
                        item = (size, name)
                        if len(largest) < top:
                            heapq.heappush(largest, item)
                        elif item > largest[0]:
                            heapq.heapreplace(largest, item)
                    except OSError as exc:
                        error_count += 1
                        if len(errors) < 25:
                            errors.append(f"{Path(entry.path).relative_to(root)}: {exc.strerror or type(exc).__name__}")
        except OSError as exc:
            error_count += 1
            if len(errors) < 25:
                errors.append(f"{current.relative_to(root)}: {exc.strerror or type(exc).__name__}")
    return dict(name=root.name or str(root), total=total, count=count,
                directories=directories, skipped=skipped, error_count=error_count,
                errors=errors, types=dict(types), groups=dict(groups),
                largest=sorted(largest, reverse=True),
                created=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"))


def report(data):
    def bars(mapping):
        rows = []
        for name, (size, count) in sorted(mapping.items(), key=lambda item: (-item[1][0], item[0]))[:15]:
            pct = size / data["total"] * 100 if data["total"] else 0
            rows.append(f'<div class="row"><div class="row-label"><span>{escape(name)}</span><b>{human(size)}</b></div>'
                        f'<div class="track"><div style="width:{pct:.3f}%"></div></div>'
                        f'<small>{count:,} files · {pct:.1f}% of total</small></div>')
        return "".join(rows) or '<p class="muted">No files found.</p>'

    files = "".join(f'<tr><td class="rank">{i:02}</td><td>{escape(name)}</td><td class="size">{human(size)}</td></tr>'
                    for i, (size, name) in enumerate(data["largest"], 1))
    errors = "".join(f"<li>{escape(e)}</li>" for e in data["errors"])
    warnings = (f'<section class="panel"><h2>Could not read {data["error_count"]:,} entries</h2>'
                f'<p>Totals are partial. Up to 25 details are shown.</p><ul>{errors}</ul></section>') if data["error_count"] else ""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>SpaceLens — Folder report</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#11181d;color:#e1e9ec;font:15px/1.6 system-ui,Segoe UI,sans-serif}
main{max-width:1120px;margin:auto;padding:36px 32px 60px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2a363e;padding-bottom:24px}
.logo{font-size:24px;letter-spacing:-1px;font-weight:700}.logo span{color:#91bfff;margin-right:10px}.badge{font-size:11px;color:#a4b9c7;border:1px solid #32414b;border-radius:30px;padding:5px 12px}
.hero{padding:38px 0 28px}.eyebrow{font-size:10px;letter-spacing:2px;color:#91bfff}h1{font-size:38px;letter-spacing:-1.5px;margin:8px 0;overflow-wrap:anywhere}p{color:#9eb0bc;margin:8px 0}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:26px}.card,.panel{background:#19232b;border:1px solid #2b3943;border-radius:12px}.card{padding:21px}.card strong{display:block;font-size:27px;font-weight:550;color:#c8defb}.card span{font-size:12px;color:#9eb0bc}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.panel{padding:26px;margin-bottom:22px}h2{font-size:17px;font-weight:600;margin:0 0 6px}.sub{font-size:12px;margin-bottom:25px}
.row{margin:20px 0}.row-label{display:flex;gap:16px;justify-content:space-between;font-size:13px}.row-label span{overflow-wrap:anywhere}.row-label b{white-space:nowrap;font-weight:500}
.track{height:7px;border-radius:5px;background:#2a3843;margin:9px 0 3px;overflow:hidden}.track div{height:100%;background:#8bb9f5;border-radius:5px}small{font-size:11px;color:#8ca3b3}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:14px 10px;text-align:left;border-bottom:1px solid #2b3943}td{overflow-wrap:anywhere}th{font-size:10px;letter-spacing:1px;color:#9eb0bc;font-weight:500}.rank{color:#7d94a5;width:45px}.size{white-space:nowrap;text-align:right}
footer{font-size:12px;color:#8ca3b3;border-top:1px solid #2a363e;padding-top:20px}.muted{color:#9eb0bc}li{overflow-wrap:anywhere}
@media(max-width:700px){main{padding:22px 16px}.cards{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.panel{padding:18px}h1{font-size:30px}.card strong{font-size:23px}}
@media print{body{background:white;color:black}.panel,.card{background:white;border-color:#bbb}p,small,footer,.card span,th{color:#444}.card strong{color:black}}
</style></head><body><main>""" + f"""
<header><div class="logo"><span>◫</span>SpaceLens</div><span class="badge">LOCAL FOLDER REPORT</span></header>
<section class="hero"><div class="eyebrow">SEE WHERE YOUR SPACE GOES</div><h1>{escape(data["name"])}</h1><p>Folder overview · {escape(data["created"])}</p></section>
<div class="cards"><div class="card"><strong>{human(data["total"])}</strong><span>Logical file size</span></div>
<div class="card"><strong>{data["count"]:,}</strong><span>Files counted</span></div>
<div class="card"><strong>{data["directories"]:,}</strong><span>Folders visited</span></div>
<div class="card"><strong>{data["skipped"]:,}</strong><span>Links / special entries skipped</span></div></div>
<div class="grid"><section class="panel"><h2>Where it lives</h2><p class="sub">Largest 15 immediate folders · Includes all their descendants</p>{bars(data["groups"])}</section>
<section class="panel"><h2>What takes up space</h2><p class="sub">Largest 15 file extensions · Based on names, not contents</p>{bars(data["types"])}</section></div>
<section class="panel"><h2>Largest files</h2><p class="sub">Top {len(data["largest"])} files · Paths relative to the selected folder</p>
<table><thead><tr><th>#</th><th>FILE</th><th class="size">SIZE</th></tr></thead><tbody>{files or '<tr><td colspan="3">No files found.</td></tr>'}</tbody></table></section>
{warnings}<footer>Generated by SpaceLens · No file contents read · No uploads<br>
Logical sizes may differ from disk usage. Hard links count once per path. Files may change during a scan.
Reports include file and folder names; review them before sharing.</footer></main></body></html>"""


def choose_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        window = tk.Tk()
        window.withdraw()
        try:
            return filedialog.askdirectory(title="SpaceLens — Choose a folder")
        finally:
            window.destroy()
    except (ImportError, RuntimeError) as exc:
        raise ValueError("Folder picker unavailable. Pass a folder path on the command line.") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", help="Folder to scan; omit to use a folder picker")
    parser.add_argument("-o", "--output", type=Path, help="New HTML file to create (never overwrites)")
    parser.add_argument("--top", type=int, default=20, choices=range(1, 101), metavar="1-100")
    args = parser.parse_args(argv)
    try:
        folder = args.folder or choose_folder()
        if not folder:
            print("No folder selected.")
            return 0
        output = args.output or Path.cwd() / ("spacelens-report-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".html")
        if output.suffix.lower() != ".html":
            raise ValueError("Output filename must end in .html.")
        if output.exists():
            raise ValueError("Output already exists. Choose a new filename.")
        print("Scanning folder metadata… Large folders may take a while. Ctrl+C cancels.")
        data = scan(folder, args.top)
        page = report(data)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(page)
        print(f"Counted {data['count']:,} files / {human(data['total'])}.")
        print(f"Report: {output.absolute()}")
        if data["error_count"]:
            print(f"Partial result: {data['error_count']} unreadable entries. See report.")
        return 0
    except KeyboardInterrupt:
        print("\nScan cancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"SpaceLens: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
