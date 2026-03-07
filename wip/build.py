#!/usr/bin/env python3
"""
Build WIP posts: converts .md files in wip/posts/ to HTML in wip/output/
and regenerates wip/index.html.

Usage:
    cd /path/to/repo
    python wip/build.py

Requires: pip install markdown
"""

import re
import sys
from pathlib import Path
from datetime import datetime

try:
    import markdown
except ImportError:
    print("Missing dependency: pip install markdown")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
POSTS_DIR = SCRIPT_DIR / "posts"
OUTPUT_DIR = SCRIPT_DIR / "output"
INDEX_PATH = SCRIPT_DIR / "index.html"

CAVEAT_FONT = '<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;700&display=swap" rel="stylesheet">'

POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>{title} - Catherine Brewer</title>
    <link rel="stylesheet" href="../../style.css">
    {caveat_font}
    <style>
        .post-title {{
            font-family: 'Caveat', cursive;
            font-size: 2.4rem;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="theme-icon">◐</span>
    </button>

    <main class="container">
        <div class="post-header">
            <div class="post-date-header">{date}</div>
            <h1 class="post-title">{title}</h1>
        </div>

        <div class="post-content">
{content}
        </div>

        <div class="back-link">
            <a href="../index.html">← Back to WIP</a>
        </div>
    </main>

    <script>
        function toggleTheme() {{
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme',
                document.documentElement.classList.contains('dark') ? 'dark' : 'light'
            );
        }}

        if (localStorage.getItem('theme') === 'dark' ||
            (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
            document.documentElement.classList.add('dark');
        }}
    </script>
</body>
</html>"""

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>WIP - Catherine Brewer</title>
    <link rel="stylesheet" href="../style.css">
    {caveat_font}
    <style>
        .wip-title {{
            font-family: 'Caveat', cursive;
            font-size: 2.8rem;
            font-weight: 700;
        }}
        .wip-disclaimer {{
            font-family: 'Caveat', cursive;
            font-size: 1.3rem;
            color: var(--secondary);
            margin-bottom: 2rem;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="theme-icon">◐</span>
    </button>

    <main class="container">
        <h1 class="wip-title">WIP</h1>
        <p class="wip-disclaimer">These are works in progress, drafts, or otherwise foolish posts. Inclusion doesn't imply endorsement. Also, here be dragons.</p>

        <ul class="post-list">
{post_items}
        </ul>

        <div class="back-link">
            <a href="../index.html">← Back to home</a>
        </div>
    </main>

    <script>
        function toggleTheme() {{
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme',
                document.documentElement.classList.contains('dark') ? 'dark' : 'light'
            );
        }}

        if (localStorage.getItem('theme') === 'dark' ||
            (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
            document.documentElement.classList.add('dark');
        }}
    </script>
</body>
</html>"""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip YAML frontmatter and return (fields dict, remaining text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    front = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    fields = {}
    for line in front.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields, body


def get_title(text: str, filename: str) -> str:
    """Extract title from first # heading, or use filename stem."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return Path(filename).stem


def strip_leading_h1(text: str, title: str) -> str:
    """Remove the first # heading if it matches the title (avoids duplication)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            if stripped[2:].strip() == title:
                lines.pop(i)
                break
            break  # only check the first heading
    return "\n".join(lines)


def clean_wikilinks(text: str) -> str:
    """Convert [[Link Text]] to plain text (link text only)."""
    # [[display|target]] → display, [[target]] → target
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    return text


def build():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    md_files = list(POSTS_DIR.glob("*.md"))
    if not md_files:
        print("No .md files found in wip/posts/ — nothing to build.")

    posts = []
    for md_file in md_files:
        raw = md_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(raw)
        title = get_title(body, md_file.name)
        body = strip_leading_h1(body, title)
        body = clean_wikilinks(body)

        # Date: prefer frontmatter, fall back to file mtime
        if "date" in frontmatter:
            try:
                dt = datetime.strptime(frontmatter["date"], "%Y-%m-%d")
            except ValueError:
                dt = datetime.fromtimestamp(md_file.stat().st_mtime)
        else:
            dt = datetime.fromtimestamp(md_file.stat().st_mtime)

        date_display = dt.strftime("%B %d, %Y")
        date_iso = dt.strftime("%Y-%m-%d")

        content_html = markdown.markdown(body, extensions=["extra"])

        output_filename = md_file.stem + ".html"
        output_path = OUTPUT_DIR / output_filename
        html = POST_TEMPLATE.format(
            title=title,
            date=date_display,
            content=content_html,
            caveat_font=CAVEAT_FONT,
        )
        output_path.write_text(html, encoding="utf-8")
        print(f"  Built: wip/output/{output_filename}")

        posts.append({"title": title, "date_iso": date_iso, "filename": f"output/{output_filename}"})

    # Sort newest first
    posts.sort(key=lambda p: p["date_iso"], reverse=True)

    post_items = "\n".join(
        f'            <li>\n'
        f'                <span class="post-date">{p["date_iso"]}</span>\n'
        f'                <a href="{p["filename"]}">{p["title"]}</a>\n'
        f'            </li>'
        for p in posts
    )

    index_html = INDEX_TEMPLATE.format(
        post_items=post_items,
        caveat_font=CAVEAT_FONT,
    )
    INDEX_PATH.write_text(index_html, encoding="utf-8")
    print(f"  Updated: wip/index.html ({len(posts)} post{'s' if len(posts) != 1 else ''})")


if __name__ == "__main__":
    build()
