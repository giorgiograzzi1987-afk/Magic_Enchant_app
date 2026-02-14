from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "database" / "magic_enchant.db"
SCHEMA_PATH = BASE_DIR.parent / "database" / "database.sql"

BASE_URL = "https://dungeonedraghi.it/compendio/incantesimi/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


def init_db(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def extract_section(soup: BeautifulSoup, title: str) -> Optional[str]:
    header = soup.find(lambda tag: tag.name in {"h2", "h3"} and tag.get_text(strip=True) == title)
    if not header:
        return None
    texts: List[str] = []
    for sibling in header.find_next_siblings():
        if sibling.name in {"h2", "h3"}:
            break
        text = sibling.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return "\n".join(texts).strip() if texts else None


def get_links_from_page(url: str) -> List[str]:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if is_spell_detail_link(href):
            links.append(href)
    return links


def get_spell_links() -> List[str]:
    resp = requests.get(BASE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if is_spell_detail_link(href):
            links.append(href)

    page_links = [a["href"] for a in soup.find_all("a", href=True) if "/compendio/incantesimi/page/" in a["href"]]
    max_page = 1
    for link in page_links:
        m = re.search(r"/compendio/incantesimi/page/(\d+)/?", link)
        if m:
            max_page = max(max_page, int(m.group(1)))

    for page in range(2, max_page + 1):
        page_url = f"{BASE_URL.rstrip('/')}/page/{page}/"
        links.extend(get_links_from_page(page_url))

    unique = sorted(set(links))
    return unique


def is_spell_detail_link(href: str) -> bool:
    if "/compendio/incantesimi/" not in href:
        return False
    if "/compendio/incantesimi/page/" in href:
        return False
    if "?" in href or "#" in href:
        return False
    if href.rstrip("/") == BASE_URL.rstrip("/"):
        return False
    return bool(re.match(r"^https?://[^/]+/compendio/incantesimi/[^/?#]+/?$", href))


def parse_spell(url: str) -> Dict[str, Optional[str]]:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    name = soup.find("h1")
    name_text = name.get_text(strip=True) if name else ""

    level_text = extract_section(soup, "Livello") or ""
    level = 0
    m = re.search(r"(\d+)", level_text)
    if m:
        level = int(m.group(1))

    school = extract_section(soup, "Scuola di Magia")
    ritual = extract_section(soup, "Rituale")
    casting_time = extract_section(soup, "Tempo di Lancio")
    spell_range = extract_section(soup, "Gittata")
    components = extract_section(soup, "Componenti")
    duration = extract_section(soup, "Durata")
    effect = extract_section(soup, "Effetto")
    higher = extract_section(soup, "Ai Livelli Superiori")

    concentration = extract_section(soup, "Concentrazione")
    classes = extract_section(soup, "Classe") or extract_section(soup, "Classi")

    material = None
    if components and "(" in components and ")" in components:
        material = components[components.find("(") + 1 : components.rfind(")")]

    return {
        "name": name_text,
        "level": level,
        "school": school,
        "ritual": ritual,
        "casting_time": casting_time,
        "range": spell_range,
        "components": components,
        "material": material,
        "duration": duration,
        "classes": classes,
        "description": effect,
        "higher_level": higher,
        "concentration": concentration,
        "url": url,
        "source": "dungeonedraghi.it",
    }


def normalize_bool(value: Optional[str]) -> int:
    if not value:
        return 0
    return 1 if value.strip().lower() in {"si", "sì", "yes", "true"} else 0


def upsert_spell(conn: sqlite3.Connection, data: Dict[str, Optional[str]]) -> None:
    conn.execute(
        """
        INSERT INTO spells (
            name, level, school, ritual, concentration, casting_time, range,
            components, material, duration, classes, description, higher_level,
            source, url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            name = excluded.name,
            level = excluded.level,
            school = excluded.school,
            ritual = excluded.ritual,
            concentration = excluded.concentration,
            casting_time = excluded.casting_time,
            range = excluded.range,
            components = excluded.components,
            material = excluded.material,
            duration = excluded.duration,
            classes = excluded.classes,
            description = excluded.description,
            higher_level = excluded.higher_level,
            source = excluded.source
        """,
        (
            data.get("name"),
            data.get("level"),
            data.get("school"),
            normalize_bool(data.get("ritual")),
            normalize_bool(data.get("concentration")),
            data.get("casting_time"),
            data.get("range"),
            data.get("components"),
            data.get("material"),
            data.get("duration"),
            data.get("classes"),
            data.get("description"),
            data.get("higher_level"),
            data.get("source"),
            data.get("url"),
        ),
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    links = get_spell_links()
    for idx, link in enumerate(links, 1):
        data = parse_spell(link)
        upsert_spell(conn, data)
        if idx % 25 == 0:
            conn.commit()
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
