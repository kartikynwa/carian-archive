import sqlite3
from pathlib import Path
import json
from typing import Dict, Any
import re

conn = sqlite3.connect("db")
cur = conn.cursor()

upgraded_item_regex = re.compile(r"\+\s?\d+$")

create_table_template_1 = """
    CREATE TABLE {table_name} (
        id INTEGER PRIMARY KEY,
        name TEXT,
        caption TEXT
    );
"""

json_dir = Path(__file__).parent / "json"
for json_file in json_dir.glob("*.json"):
    if "npc_dialogues" in str(json_file):
        continue
    with open(json_file, "r") as f:
        json_dump: Dict[Any, Any] = json.load(f)
    table_name = json_file.stem
    cur.execute(f"DROP TABLE IF EXISTS {table_name};")
    create_table_query = create_table_template_1.format(table_name=table_name)
    cur.execute(create_table_query)
    for id, data in json_dump.items():
        id = int(id)
        name = data.get("name")
        if name:
            name = name.strip()
            if upgraded_item_regex.search(name):
                print("skipping:", name)
                continue
        caption = data.get("caption")
        query = f"INSERT INTO {table_name} (id, name, caption) VALUES (?, ?, ?)"
        cur.execute(query, (id, name, caption))

dialogues_file = json_dir / "npc_dialogues.json"
with open(dialogues_file, "r") as f:
    json_dump = json.load(f)

table_name = "npc_dialogue"
cur.execute(f"DROP TABLE IF EXISTS {table_name};")
create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        npc_id INTEGER,
        npc_name TEXT,
        section INTEGER NOT NULL,
        dialogue TEXT NOT NULL
    );
"""
cur.execute(create_table_query)

for id, data in json_dump.items():
    id = int(id)
    name = data.pop("name", None)
    if name:
        name = name.strip()
    for section_id, dialogue_lines in data.items():
        section_id = int(section_id)
        dialogue = "\n".join(dialogue_lines)
        insert_query = f"""
            INSERT INTO {table_name} (npc_id, npc_name, section, dialogue)
            VALUES (?, ?, ?, ?);
        """
        cur.execute(insert_query, (id, name, section_id, dialogue))

conn.commit()
cur.close()
conn.close()
