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
}
