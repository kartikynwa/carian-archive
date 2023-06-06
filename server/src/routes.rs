use actix_web::{get, web, HttpResponse, Responder};
use askama::Template;
use serde::Deserialize;
use sqlx::query_builder::QueryBuilder;

use crate::schema::CarianArchiveRow;
use crate::AppState;

#[derive(Template)]
#[template(path = "base.html")]
struct BaseTemplate {}

#[derive(Template)]
#[template(path = "entry.html")]
struct EntryTemplate<'a> {
    entry: &'a CarianArchiveRow,
    entry_type: String,
}

impl<'a> EntryTemplate<'_> {
    fn from_row(row: &'a CarianArchiveRow) -> Self {
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
        EntryTemplate {
            entry: row,
            entry_type,
        }
    }
}

#[get("/style.css")]
pub async fn style() -> impl Responder {
    let res = include_str!("../static/style.css").to_string();
    HttpResponse::Ok()
        .insert_header(("content-type", "text/css"))
        .insert_header(("cache-control", "public, max-age=1209600, s-maxage=86400"))
        .body(res)
}

#[derive(Deserialize)]
pub struct SearchQuery {
    term: String,
    limit: Option<u32>,
    offset: Option<u32>,
    entry_type: Option<Vec<u8>>,
}

#[get("/")]
pub async fn home() -> impl Responder {
    let s = BaseTemplate {};
    HttpResponse::Ok()
        .content_type("text/html")
        .body(s.render().unwrap())
}

#[get("/entry/{entry_id}")]
pub async fn get_entry(data: web::Data<AppState>, path: web::Path<(i64,)>) -> impl Responder {
    let (entry_id,) = path.into_inner();
    let entry = sqlx::query_as!(
        CarianArchiveRow,
        "
        SELECT c1.*, c2.title AS parent_title
        FROM carian_archive c1
        LEFT JOIN carian_archive c2 ON c1.parent_id=c2.game_id AND c2.entry_type=5
        WHERE c1.id=?
        ",
        entry_id
    )
    .fetch_optional(&data.db)
    .await
    .unwrap();
    match entry {
        Some(entry) => {
            let body = EntryTemplate::from_row(&entry).render().unwrap();
            HttpResponse::Ok()
                .insert_header(("content-type", "text/html"))
                .body(body)
        }
        _ => HttpResponse::NotFound().body("Unknown entry"),
    }
}

#[get("/search")]
pub async fn search(data: web::Data<AppState>, query: web::Query<SearchQuery>) -> impl Responder {
    let mut sql_query_builder = QueryBuilder::new(
        "
        SELECT c1.*, c2.title AS parent_title FROM carian_archive c1
        JOIN carian_archive_fts c_fts ON c1.id=c_fts.rowid
        LEFT JOIN carian_archive c2 ON c1.parent_id=c2.game_id AND c2.entry_type=5
        ",
    );

    let search_query: String = query
        .term
        .split_whitespace()
        .map(|t| format!("\"{t}\""))
        .collect::<Vec<String>>()
        .join(" ");
    sql_query_builder.push("WHERE carian_archive_fts MATCH ");
    sql_query_builder.push_bind(search_query);

    if let Some(entry_types) = &query.entry_type {
        if !entry_types.is_empty() {
            sql_query_builder.push("AND (FALSE ");
            for entry_type in entry_types {
                sql_query_builder.push("OR entry_type = ");
                sql_query_builder.push_bind(entry_type);
            }
            sql_query_builder.push(") ");
        }
    }

    if let Some(l) = query.limit {
        sql_query_builder.push("LIMIT ");
        sql_query_builder.push_bind(l);
    }
    if let Some(o) = query.offset {
        sql_query_builder.push("OFFSET ");
        sql_query_builder.push_bind(o);
    }
    let results: Result<Vec<CarianArchiveRow>, _> =
        sql_query_builder.build_query_as().fetch_all(&data.db).await;
    match results {
        Ok(r) => HttpResponse::Ok().body(format!("{:?}", r)),
        Err(e) => HttpResponse::InternalServerError().body(format!("Request failed: {:?}", e)),
    }
}
