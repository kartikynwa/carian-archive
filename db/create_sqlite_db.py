import os
import sqlite3
from pathlib import Path
import json
from typing import Dict, Any
import re

db_path = "../server/elden_ring.db"

try:
    os.unlink(db_path)
except Exception:
    pass

conn = sqlite3.connect("../server/elden_ring.db")
cur = conn.cursor()

with open("./schema.sql") as f:
    schema = f.read()

cur.executescript(schema);

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
                print("SKIPPING:", game_id)
                continue
        if entry_type == "npcs":
            query = f"INSERT INTO carian_archive (game_id, entry_type, title) VALUES (?, ?, ?)"
            cur.execute(query, (game_id, type_id, data))
        else:
            name = data.get("name")
            if name:
                name = name.strip()
                if upgraded_item_regex.search(name):
                    print("skipping:", name)
                    continue
            caption = data.get("caption")
            query = f"INSERT INTO carian_archive (game_id, entry_type, title, info) VALUES (?, ?, ?, ?)"
            cur.execute(query, (game_id, type_id, name, caption))

    # if "dialogues" in str(json_file):
    #     continue
    # with open(json_file, "r") as f:
    #     json_dump: Dict[Any, Any] = json.load(f)
    # table_name = json_file.stem
    # cur.execute(f"DROP TABLE IF EXISTS {table_name};")
    # if table_name == "npcs":
    #     create_table_query = create_npc_table_query
    # else:
    #     create_table_query = create_table_template.format(table_name=table_name)
    # cur.executescript(create_table_query)
    # for npc_id, data in json_dump.items():
    #     npc_id = int(npc_id)
    #     if table_name == "npcs":
    #         query = f"INSERT INTO npcs (id, name) VALUES (?, ?)"
    #         cur.execute(query, (npc_id, data))
    #     else:
    #         name = data.get("name")
    #         if name:
    #             name = name.strip()
    #             if upgraded_item_regex.search(name):
    #                 print("skipping:", name)
    #                 continue
    #         caption = data.get("caption")
    #         query = f"INSERT INTO {table_name} (id, name, caption) VALUES (?, ?, ?)"
    #         cur.execute(query, (npc_id, name, caption))

# dialogues_file = json_dir / "dialogues.json"
# with open(dialogues_file, "r") as f:
#     json_dump = json.load(f)
#
# entry_type = "dialogues"
# cur.execute(f"DROP TABLE IF EXISTS {entry_type};")
# create_table_query = f"""
#     CREATE TABLE IF NOT EXISTS {entry_type} (
#         id INTEGER PRIMARY KEY,
#         npc_id INTEGER,
#         section INTEGER NOT NULL,
#         dialogue TEXT NOT NULL
#     );
#
#     CREATE VIRTUAL TABLE {entry_type}_fts
#     USING fts5(
#         dialogue,
#         content={entry_type},
#         content_rowid=id
#     );
#
#     CREATE TRIGGER {entry_type}_ai AFTER INSERT ON {entry_type} BEGIN
#         INSERT INTO {entry_type}_fts(rowid, dialogue) VALUES (new.id, new.dialogue);
#     END;
#
#     CREATE TRIGGER {entry_type}_ad AFTER DELETE ON {entry_type} BEGIN
#         INSERT INTO {entry_type}_fts({entry_type}_fts, rowid, dialogue) VALUES('delete', old.id, old.dialogue);
#     END;
#
#     CREATE TRIGGER {entry_type}_au AFTER UPDATE ON {entry_type} BEGIN
#         INSERT INTO {entry_type}_fts({entry_type}_fts, rowid, dialogue) VALUES('delete', old.id, old.dialogue);
#         INSERT INTO {entry_type}_fts(rowid, dialogue) VALUES (new.id, new.dialogue);
#     END;
# """
# cur.executescript(create_table_query)
#
# for npc_id, data in json_dump.items():
#     npc_id = int(npc_id)
#     name = data.pop("name", None)
#     if name:
#         name = name.strip()
#     for section_id, dialogue_lines in data.items():
#         section_id = int(section_id)
#         dialogue = "\n".join(dialogue_lines)
#         insert_query = f"""
#             INSERT INTO {entry_type} (npc_id, section, dialogue)
#             VALUES (?, ?, ?);
#         """
#         cur.execute(insert_query, (npc_id, section_id, dialogue))

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
cur.close()
conn.close()
