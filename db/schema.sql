/*
 * Files
 * - 0: accessories: Talismans
 * - 1: arts: Ashes of War
 * - 2: dialogues: Dialogues
 * - 3: gems: Also Ashes of War???????
 * - 4: goods: Items
 * - 5: npcs: NPCs in the game
 * - 6: protectors: Armours
 * - 7: weapons: Weapons
*/

CREATE TABLE entry_types (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE UNIQUE INDEX entry_types_name_idx ON entry_types (name);

INSERT INTO entry_types (id, name) VALUES
    (0, 'accessories'),
    (1, 'arts'       ),
    (2, 'dialogues'  ),
    (3, 'gems'       ),
    (4, 'goods'      ),
    (5, 'npcs'       ),
    (6, 'protectors' ),
    (7, 'weapons'    )
;

CREATE TABLE carian_archive (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    entry_type INTEGER NOT NULL CHECK(entry_type >= 0 AND entry_type <= 7),
    title TEXT,
    info TEXT,
    parent_id INTEGER,
    sprite_id INTEGER
);

CREATE INDEX carian_archive_game_id_idx ON carian_archive (game_id);
CREATE INDEX carian_archive_type_idx ON carian_archive (entry_type);

CREATE VIRTUAL TABLE carian_archive_fts
USING fts5(
    title,
    info,
    content=carian_archive,
    content_rowid=id
);

CREATE TRIGGER carian_archive_ai AFTER INSERT ON carian_archive BEGIN
    INSERT INTO carian_archive_fts(rowid, title, info) VALUES (new.id, new.title, new.info);
END;

CREATE TRIGGER carian_archive_ad AFTER DELETE ON carian_archive BEGIN
    INSERT INTO carian_archive_fts(carian_archive_fts, rowid, title, info) VALUES('delete', old.id, old.title, old.info);
END;

CREATE TRIGGER carian_archive_au AFTER UPDATE ON carian_archive BEGIN
    INSERT INTO carian_archive_fts(carian_archive_fts, rowid, title, info) VALUES('delete', old.id, old.title, old.info);
    INSERT INTO carian_archive_fts(rowid, title, info) VALUES (new.id, new.title, new.info);
END;


CREATE TABLE sprites (
  id INTEGER PRIMARY KEY,
  filepath TEXT NOT NULL,
  basename TEXT NOT NULL,
  category TEXT NOT NULL
);

CREATE VIRTUAL TABLE sprites_fts
USING fts5(
    basename,
    content=sprites,
    content_rowid=id
);

CREATE TRIGGER sprites_ai AFTER INSERT ON sprites BEGIN
    INSERT INTO sprites_fts(rowid, basename) VALUES (new.id, new.basename);
END;

CREATE TRIGGER sprites_ad AFTER DELETE ON sprites BEGIN
    INSERT INTO sprites_fts(sprites_fts, rowid, basename) VALUES('delete', old.id, old.basename);
END;

CREATE TRIGGER sprites_au AFTER UPDATE ON sprites BEGIN
    INSERT INTO sprites_fts(sprites_fts, rowid, basename) VALUES('delete', old.id, old.basename);
    INSERT INTO sprites_fts(rowid, basename) VALUES (new.id, new.basename);
END;
