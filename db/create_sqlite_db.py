import os
import sqlite3
from pathlib import Path
import json
from typing import Dict, Any
import re

def sanitize_search_input(input: str) -> str:
    return f"\"title\": ^\"{input}\""
    # return " ".join(f"\"{i}\"" for i in input.split())

def normalize_text(input: str) -> str:
    input = input.lower()
    input = re.sub(r'[^a-z ]+', '', input)
    return input

db_path = "../server/elden_ring.db"
sprites_dir = "../sprites"

try:
    os.unlink(db_path)
except Exception:
    pass

conn = sqlite3.connect(db_path)
cur = conn.cursor()

with open("./schema.sql") as f:
    schema = f.read()

cur.executescript(schema)

upgraded_item_regex = re.compile(r"\+\s?\d+$")

cur.execute("SELECT id, name FROM entry_types")
type_map = {name: id for id, name in cur.fetchall()}

json_dir = Path(__file__).parent.parent / "json"
for json_file in json_dir.glob("*.json"):
    if "dialogues" in str(json_file):
        continue
    with open(json_file, "r") as f:
        json_dump: Dict[Any, Any] = json.load(f)
    entry_type = json_file.stem
    type_id = type_map[entry_type]
    for game_id, data in json_dump.items():
        game_id = int(game_id)
        if entry_type in ("protectors", "weapons", "arts", "gems"):
            if "name" not in data or "caption" not in data:
                # print("SKIPPING:", game_id)
                continue
        if entry_type == "npcs":
            query = f"INSERT INTO carian_archive (game_id, entry_type, title) VALUES (?, ?, ?)"
            cur.execute(query, (game_id, type_id, data))
        else:
            name = data.get("name")
            if name:
                name = name.strip()
                if upgraded_item_regex.search(name):
                    # print("SKIPPING:", name)
                    continue
            caption = data.get("caption")
            query = f"INSERT INTO carian_archive (game_id, entry_type, title, info) VALUES (?, ?, ?, ?)"
            cur.execute(query, (game_id, type_id, name, caption))

dialogues_file = json_dir / "dialogues.json"
with open(dialogues_file, "r") as f:
    json_dump = json.load(f)
entry_type = "dialogues"
type_id = type_map[entry_type]

for npc_id, data in json_dump.items():
    npc_id = int(npc_id)
    for section_id, dialogue_obj in data.items():
        section_id = int(section_id)
        dialogue_id = dialogue_obj["id"]
        dialogue_lines = dialogue_obj["dialogue"]
        dialogue = "\n".join(dialogue_lines)
        insert_query = f"""
            INSERT INTO carian_archive (game_id, entry_type, info, parent_id)
            VALUES (?, ?, ?, ?);
        """
        cur.execute(insert_query, (dialogue_id, type_id, dialogue, npc_id))

conn.commit()

sprites_dir = Path(__file__).parent / sprites_dir

for subdir in sprites_dir.glob("*"):
    category = subdir.name
    for sprite in subdir.glob("*.png"):
        relative_path = sprite.relative_to(Path(__file__).parent)
        basename = sprite.stem
        cur.execute("INSERT INTO sprites (filepath, basename, category) VALUES (?, ?, ?)", (str(relative_path), str(basename), category))

conn.commit()

try_categories = set([
    "Ammunition",
    "Armor",
    "Ashes of War",
    "Bell Bearings",
    "Consumables",
    "Cookbooks",
    "Crafting Materials",
    "Crystal Tears",
    # "Cut Content", # SKIP FOREVER
    # "Gestures", # SKIP FOREVER
    "Great Runes",
    "Incantations",
    "Information",
    "Key Items",
    # "Loading Screens", # SKIP FOREVER
    "Map Fragments",
    # "Misc", # SKIP FOREVER
    "Multiplayer Items",
    "Paintings",
    "Prayer Books & Scrolls",
    "Remembrances",
    "Sorceries",
    # "Spell Emblems", # SKIP FOREVER
    "Spirit Ashes",
    "Talismans",
    # "Tools", # SKIP FOR NOW
    # "Tutorials", # SKIP FOREVER
    "Upgrade Materials",
    "Weapons",
])

for subdir in sprites_dir.glob("*"):
    category = subdir.name
    if category not in try_categories:
        continue
    cur.execute("SELECT id, basename FROM sprites WHERE category=?", (category,))
    resp = cur.fetchall()
    for id, basename in resp:
        search_input = basename
        if category == "Paintings":
            search_input += " Painting"
        search_input = sanitize_search_input(search_input)
        cur.execute(
            """
            SELECT c.id, c.title FROM carian_archive c
            JOIN carian_archive_fts c_fts ON c.id=c_fts.rowid
            WHERE carian_archive_fts MATCH ?
            ORDER by c_fts.title = ? DESC, rank LIMIT 1
            -- ORDER by rank LIMIT 1
            """,
            # (search_input,)
            (search_input, basename)
        )
        c_id, c_title = cur.fetchone() or (None, None)
        if not c_id:
            print(f"ID IS {id}, BASENAME IS {basename}")
            print(f"NO MATCH, search_input: {search_input}")
            print("")
        else:
            n_basename = normalize_text(basename)
            n_title = normalize_text(c_title)
            perfect_match = n_basename == n_title
            if not perfect_match:
                print(f"ID IS {id}, BASENAME IS {basename}")
                print(f"IMPERFECT MATCH => ID: {c_id}, TITLE: {c_title} => '{n_basename}' != '{n_title}'")
                print("")

cur.close()
conn.close()
