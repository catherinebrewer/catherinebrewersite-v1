#!/usr/bin/env python3
"""
Build script for daily writing.
Converts all .md files in daily/ to HTML and generates an index.

Usage: python build.py
"""

import re
from pathlib import Path
from datetime import datetime
import markdown

# HTML template for individual posts
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>{title} - Catherine Brewer</title>
    <link rel="stylesheet" href="../../style.css">
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="theme-icon">◐</span>
    </button>

    <main class="container">
        <div class="post-header">
            <div class="post-date-header">{date_formatted}</div>
            <h1 class="post-title">{title}</h1>
        </div>

        <div class="post-content">
{content}
        </div>

        <div class="back-link">
            <a href="index.html">← Back to daily writing</a>
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
</html>
"""

# HTML template for index page
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Daily Writing - Catherine Brewer</title>
    <link rel="stylesheet" href="../../style.css">
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="theme-icon">◐</span>
    </button>

    <main class="container">
        <h1>Daily Writing</h1>
        <p class="subtitle">A collection of daily thoughts and notes</p>

        <ul class="post-list">
{post_links}
        </ul>

        <div class="back-link">
            <a href="../../index.html">← Back to home</a>
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
</html>
"""


def parse_frontmatter(content):
    """Extract YAML frontmatter and content from markdown."""
    frontmatter = {}
    
    # Check for frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Parse frontmatter
            fm_lines = parts[1].strip().split('\n')
            for line in fm_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            content = parts[2].strip()
    
    return frontmatter, content


def extract_title(content):
    """Extract title from first H1 in markdown."""
    # Look for # Title at start of line
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Untitled"


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def process_markdown_file(md_path):
    """Convert a markdown file to HTML and return metadata."""
    content = md_path.read_text(encoding='utf-8')
    
    # Parse frontmatter
    frontmatter, content = parse_frontmatter(content)
    
    # Extract title from content
    title = extract_title(content)
    
    # Get date from frontmatter or use file modification time
    if 'date' in frontmatter:
        date_str = frontmatter['date']
        date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        # Fallback to file modification time
        timestamp = md_path.stat().st_mtime
        date = datetime.fromtimestamp(timestamp)
        date_str = date.strftime('%Y-%m-%d')
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'nl2br'])
    html_content = md.convert(content)
    
    # Format date for display
    date_formatted = date.strftime('%B %d, %Y')
    
    # Generate output filename
    slug = md_path.stem  # Use the markdown filename as slug
    output_filename = f"{slug}.html"
    
    return {
        'title': title,
        'date': date,
        'date_str': date_str,
        'date_formatted': date_formatted,
        'content': html_content,
        'output_filename': output_filename,
        'slug': slug
    }


def build():
    """Main build function."""
    daily_dir = Path('daily')
    output_dir = daily_dir / '_output'
    output_dir.mkdir(exist_ok=True)
    
    # Find all markdown files
    md_files = list(daily_dir.glob('*.md'))
    
    if not md_files:
        print("No markdown files found in daily/")
        return
    
    # Process all markdown files
    posts = []
    for md_path in md_files:
        print(f"Processing {md_path.name}...")
        post_data = process_markdown_file(md_path)
        posts.append(post_data)
        
        # Write HTML file
        html = POST_TEMPLATE.format(**post_data)
        output_path = output_dir / post_data['output_filename']
        output_path.write_text(html, encoding='utf-8')
        print(f"  → {output_path}")
    
    # Sort posts by date (newest first)
    posts.sort(key=lambda p: p['date'], reverse=True)
    
    # Generate index
    post_links = []
    for post in posts:
        link = f'''            <li>
                <span class="post-date">{post['date_str']}</span>
                <a href="{post['output_filename']}">{post['title']}</a>
            </li>'''
        post_links.append(link)
    
    index_html = INDEX_TEMPLATE.format(post_links='\n'.join(post_links))
    index_path = output_dir / 'index.html'
    index_path.write_text(index_html, encoding='utf-8')
    print(f"\nGenerated index: {index_path}")
    print(f"\nBuilt {len(posts)} posts!")


if __name__ == '__main__':
    build()
