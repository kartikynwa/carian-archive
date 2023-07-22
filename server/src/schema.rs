// id INTEGER PRIMARY KEY,
// game_id INTEGER NOT NULL,
// entry_type INTEGER NOT NULL CHECK(entry_type >= 0 AND entry_type <= 7),
// title TEXT,
// info TEXT,
// parent_id INTEGER

// (0, 'accessories'),
// (1, 'arts'       ),
// (2, 'dialogues'  ),
// (3, 'gems'       ),
// (4, 'goods'      ),
// (5, 'npcs'       ),
// (6, 'protectors' ),
// (7, 'weapons'    )

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, sqlx::FromRow, Debug)]
pub struct CarianArchiveRow {
    pub id: i64,
    pub game_id: i64,
    pub entry_type: i64,
    pub title: Option<String>,
    pub info: Option<String>,
    pub parent_id: Option<i64>,
    pub parent_title: Option<String>,
    pub sprite_id: Option<i64>,
}

pub struct CarianArchiveEntry {
    pub id: i64,
    pub game_id: i64,
    pub entry_type_id: i64,
    pub entry_type: String,
    pub title: Option<String>,
    pub info: Option<String>,
    pub parent_id: Option<i64>,
    pub parent_title: Option<String>,
    pub sprite_id: Option<i64>,
}

impl CarianArchiveEntry {
    pub fn from_row(row: CarianArchiveRow) -> Self {
        let entry_type = match row.entry_type {
            0 => "Talisman".to_string(),
            1 => "Unique Weapon Skill".to_string(),
            2 => "Dialogue".to_string(),
            3 => "Ash of War".to_string(),
            4 => "Item".to_string(),
            5 => "NPC".to_string(),
            6 => "Armour".to_string(),
            7 => "Weapon".to_string(),
            _ => format!("Unknown entry type (id={})", row.entry_type),
        };
        CarianArchiveEntry {
            id: row.id,
            game_id: row.game_id,
            entry_type_id: row.entry_type,
            entry_type,
            title: row.title,
            info: row.info,
            parent_id: row.parent_id,
            parent_title: row.parent_title,
            sprite_id: row.sprite_id,
        }
    }
}
