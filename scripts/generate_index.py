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
    if relative_string in {
        "index.html",
        "404.html",
    }:
        continue

    if any(
        part in ignored_directories
        for part in relative.parts
    ):
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
            <div class="title">
                {escape(entry['title'])}
            </div>

            <div class="filename">
                {escape(entry['path'])}
            </div>
        </a>
    </li>
    """
    for entry in entries
)


html = f"""<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>{escape(repo_name)} – Übersicht</title>

    <style>
        :root {{
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif;

            color-scheme: light dark;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: Canvas;
            color: CanvasText;
        }}

        main {{
            width: min(760px, calc(100% - 32px));
            margin: 0 auto;
            padding: 42px 0 70px;
        }}

        header {{
            margin-bottom: 28px;
        }}

        h1 {{
            margin: 0;
            font-size: clamp(1.8rem, 5vw, 2.5rem);
            letter-spacing: -0.025em;
        }}

        .subtitle {{
            margin: 7px 0 0;
            opacity: .55;
            font-size: .95rem;
        }}

        .search-wrap {{
            margin-bottom: 24px;
        }}

        input {{
            width: 100%;
            font: inherit;
            font-size: 1rem;
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px solid color-mix(
                in srgb,
                CanvasText 18%,
                transparent
            );
            background: color-mix(
                in srgb,
                CanvasText 4%,
                Canvas
            );
            color: inherit;
            outline: none;
        }}

        input:focus {{
            border-color: color-mix(
                in srgb,
                CanvasText 45%,
                transparent
            );
        }}

        #count {{
            margin-top: 9px;
            font-size: .82rem;
            opacity: .5;
        }}

        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            gap: 9px;
        }}

        .item a {{
            display: block;
            padding: 15px 17px;
            border: 1px solid color-mix(
                in srgb,
                CanvasText 15%,
                transparent
            );
            border-radius: 13px;
            color: inherit;
            text-decoration: none;
            background: color-mix(
                in srgb,
                CanvasText 2%,
                Canvas
            );
            transition:
                background .15s ease,
                transform .15s ease;
        }}

        .item a:hover {{
            background: color-mix(
                in srgb,
                CanvasText 6%,
                Canvas
            );
        }}

        .item a:active {{
            transform: scale(.995);
        }}

        .title {{
            font-size: 1.02rem;
            font-weight: 650;
            line-height: 1.3;
        }}

        .filename {{
            margin-top: 5px;
            font-size: .75rem;
            opacity: .38;
            overflow-wrap: anywhere;
        }}

        .empty {{
            opacity: .5;
            padding: 20px 0;
        }}

        footer {{
            margin-top: 32px;
            font-size: .75rem;
            opacity: .35;
            text-align: center;
        }}

        @media (max-width: 600px) {{
            main {{
                width: min(100% - 24px, 760px);
                padding-top: 28px;
            }}

            header {{
                margin-bottom: 22px;
            }}

            .item a {{
                padding: 14px 15px;
            }}
        }}
    </style>
</head>

<body>

<main>

    <header>
        <h1>{escape(repo_name)}</h1>

        <p class="subtitle">
            Werkzeuge und HTML-Seiten
        </p>
    </header>

    <div class="search-wrap">
        <input
            id="search"
            type="search"
            placeholder="Durchsuchen …"
            autocomplete="off"
        >

        <div id="count">
            {len(entries)} Seiten
        </div>
    </div>

    <ul id="pages">
        {cards}
    </ul>

    <div
        id="empty"
        class="empty"
        hidden
    >
        Keine passenden Seiten gefunden.
    </div>

    <footer>
        Automatisch aus dem GitHub-Repository erzeugt
    </footer>

</main>

<script>
    const search =
        document.getElementById("search");

    const items =
        [...document.querySelectorAll(".item")];

    const count =
        document.getElementById("count");

    const empty =
        document.getElementById("empty");

    function update() {{
        const query =
            search.value
                .trim()
                .toLowerCase();

        let visible = 0;

        items.forEach(item => {{
            const text =
                item.textContent.toLowerCase();

            const matches =
                text.includes(query);

            item.hidden = !matches;

            if (matches) {{
                visible++;
            }}
        }});

        count.textContent =
            visible +
            (visible === 1
                ? " Seite"
                : " Seiten");

        empty.hidden =
            visible !== 0;
    }}

    search.addEventListener(
        "input",
        update
    );
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
