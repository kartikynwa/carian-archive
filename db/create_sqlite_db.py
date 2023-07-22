import os
import sqlite3
from pathlib import Path
import json
from typing import Dict, Any
import re

db_path = "../server/elden_ring.db"
sprites_dir = "../server/static/sprites"

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
cookbook_regex = re.compile(r"Cookbook\s?\[(\d+)\]$")
cut_cookbook_regex = re.compile(r"Cookbook\s?\(\d+\)$")

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
                if m := cookbook_regex.search(name):
                    print(f"COOKBOOK FOUND: {name}")
                    if m.group(1) != "1":
                        continue
                    name = name[:-4]
                if cut_cookbook_regex.search(name):
                    print(f"CUT COOKBOOK FOUND: {name}")
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
        relative_path = sprite.relative_to(Path(__file__).parent / ".." / "server")
        basename = sprite.stem
        cur.execute("INSERT INTO sprites (filepath, basename, category) VALUES (?, ?, ?)", (str(relative_path), str(basename), category))

conn.commit()
cur.close()
conn.close()
