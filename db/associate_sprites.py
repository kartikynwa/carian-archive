import sqlite3
from pathlib import Path
import re
import sys

write_changes = False
if len(sys.argv) >= 2 and sys.argv[1] == "-w":
    print("Writing changes to the database")
    write_changes = True

def sanitize_search_input(input: str, exact=True) -> str:
    if exact:
        return f"\"title\": ^\"{input}\""
    else:
        return f"\"title\": \"{input}\""
    # return " ".join(f"\"{i}\"" for i in input.split())

def normalize_text(input: str) -> str:
    input = input.lower()
    input = re.sub(r'[^a-z0-9]+', ' ', input)
    return input.strip()

def search(basename: str, exact=True):
    search_input = basename.replace('"', '')
    # if category == "Paintings":
    #     search_input += " Painting"
    search_input = sanitize_search_input(search_input, exact)
    try:
        cur.execute(
            """
            SELECT c.id, c.title FROM carian_archive c
            JOIN carian_archive_fts c_fts ON c.id=c_fts.rowid
            WHERE carian_archive_fts MATCH (?)
            ORDER by c_fts.title = ? DESC, rank LIMIT 1
            -- ORDER by rank LIMIT 1
            """,
            # (search_input,)
            (search_input, basename)
        )
    except Exception:
        print(search_input)
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
        return c_id

def set_sprite(cur, carian_archive_id: int, sprite_id: int):
    print(f"ASSOCIATING SPRITE: sprite_id={sprite_id}, carian_archive_id={carian_archive_id}")
    if write_changes:
        cur.execute("UPDATE carian_archive SET sprite_id=? WHERE id=?", (sprite_id, carian_archive_id))

db_path = "../server/elden_ring.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()
sprites_dir = "../sprites"
sprites_dir = Path(__file__).parent / sprites_dir

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

bell_bearing_prefix = "Bell Bearing - "
note_prefix = "Note - "

for category in try_categories:
    cur.execute("SELECT id, basename FROM sprites WHERE category=?", (category,))
    resp = cur.fetchall()
    for id, basename in resp:
        if basename.startswith(note_prefix):
            for note_name in basename[len(note_prefix):].split(","):
                carian_archive_id = search(f"Note: {note_name}")
                if carian_archive_id:
                    set_sprite(cur, carian_archive_id, id)
        elif basename.startswith(bell_bearing_prefix):
            for bell_bearing_owner in basename[len(bell_bearing_prefix):].split(","):
                carian_archive_id = search(f"{bell_bearing_owner} Bell Bearing", exact=False)
                if carian_archive_id:
                    set_sprite(cur, carian_archive_id, id)
        else:
            carian_archive_id = search(basename)
            if carian_archive_id:
                set_sprite(cur, carian_archive_id, id)

conn.commit()
cur.close()
conn.close()
