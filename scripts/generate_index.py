from pathlib import Path
from html.parser import HTMLParser
from html import escape
from urllib.parse import quote
import os
import re


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)

    def title(self):
        return " ".join("".join(self.parts).split()).strip()


def get_title(path):
    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )[:250000]

        parser = TitleParser()
        parser.feed(text)

        return parser.title()
    except Exception:
        return ""


def fallback_title(path):
    if path.name.lower() == "index.html":
        name = path.parent.name
    else:
        name = path.stem

    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def natural_key(text):
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", text)
    ]


repo = os.environ.get("GITHUB_REPOSITORY", "")
repo_name = repo.split("/")[-1] if repo else Path.cwd().name

entries = []

ignored_directories = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__",
}

for path in Path(".").rglob("*.html"):
    relative = path.relative_to(Path("."))
    relative_string = relative.as_posix()

    # Die automatisch erzeugte Startseite selbst nicht aufnehmen
    if relative_string in {"index.html", "404.html"}:
        continue

    if any(part in ignored_directories for part in relative.parts):
        continue

    title = get_title(path)

    if not title:
        title = fallback_title(relative)

    entries.append({
        "title": title,
        "path": relative_string,
        "url": quote(relative_string, safe="/"),
    })


entries.sort(
    key=lambda entry: (
        natural_key(entry["title"]),
        natural_key(entry["path"]),
    )
)


cards = "\n".join(
    f"""
    <li class="item">
        <a href="{escape(entry['url'])}">
            <strong>{escape(entry['title'])}</strong>
            <span>{escape(entry['path'])}</span>
        </a>
    </li>
    """
    for entry in entries
)


html = f"""<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>{escape(repo_name)} – Übersicht</title>

    <style>
        :root {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                         Roboto, Helvetica, Arial, sans-serif;
            color-scheme: light dark;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px 80px;
            line-height: 1.45;
        }}

        h1 {{
            margin-bottom: 6px;
        }}

        .subtitle {{
            opacity: .65;
            margin-top: 0;
            margin-bottom: 28px;
        }}

        input {{
            width: 100%;
            font: inherit;
            padding: 12px 14px;
            border-radius: 10px;
            border: 1px solid #8885;
            margin-bottom: 12px;
        }}

        #count {{
            font-size: .9rem;
            opacity: .6;
            margin-bottom: 20px;
        }}

        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            gap: 10px;
        }}

        .item a {{
            display: block;
            padding: 14px 16px;
            border: 1px solid #8884;
            border-radius: 12px;
            color: inherit;
            text-decoration: none;
        }}

        .item a:hover {{
            background: #8881;
        }}

        .item strong {{
            display: block;
            font-size: 1rem;
        }}

        .item span {{
            display: block;
            margin-top: 4px;
            font-size: .8rem;
            opacity: .55;
        }}
    </style>
</head>

<body>

    <h1>{escape(repo_name)}</h1>

    <p class="subtitle">
        Automatische Übersicht der HTML-Seiten
    </p>

    <input
        id="search"
        type="search"
        placeholder="Seiten durchsuchen …"
        autocomplete="off"
    >

    <div id="count">{len(entries)} Seiten</div>

    <ul id="pages">
        {cards}
    </ul>

    <script>
        const search = document.getElementById("search");
        const items = [...document.querySelectorAll(".item")];
        const count = document.getElementById("count");

        search.addEventListener("input", () => {{
            const query = search.value.trim().toLowerCase();
            let visible = 0;

            items.forEach(item => {{
                const matches =
                    item.textContent.toLowerCase().includes(query);

                item.hidden = !matches;

                if (matches) visible++;
            }});

            count.textContent =
                visible + (visible === 1 ? " Seite" : " Seiten");
        }});
    </script>

</body>
</html>
"""


Path("index.html").write_text(
    html,
    encoding="utf-8"
)

print(
    f"index.html mit {len(entries)} HTML-Seiten erzeugt."
)
