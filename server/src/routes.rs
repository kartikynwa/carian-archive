use actix_files::NamedFile;
use actix_web::{
    error::{ErrorInternalServerError, ErrorNotFound},
    get, web, HttpResponse, Responder,
};
use askama::Template;
use serde::Deserialize;
use sqlx::query_builder::QueryBuilder;
use std::path::PathBuf;

use crate::schema::{CarianArchiveEntry, CarianArchiveRow};
use crate::AppState;

#[derive(Template)]
#[template(path = "home.html")]
struct HomeTemplate {}

#[derive(Template)]
#[template(path = "entry.html")]
struct EntryTemplate {
    entry: CarianArchiveEntry,
}

#[get("/style.css")]
pub async fn style() -> Result<NamedFile, actix_web::Error> {
    Ok(NamedFile::open("static/style.css")?)
}

#[derive(Deserialize)]
pub struct SearchQuery {
    term: String,
    limit: Option<u32>,
    offset: Option<u32>,
    entry_type: Option<Vec<u8>>,
    title_only: Option<bool>,
}

#[derive(Template)]
#[template(path = "search.html")]
struct SearchTemplate {
    entries: Vec<CarianArchiveEntry>,
    search_term: String,
    limit: u32,
    offset: u32,
    has_next_page: bool,
}

#[get("/")]
pub async fn home() -> impl Responder {
    let s = HomeTemplate {};
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
            let body = EntryTemplate {
                entry: CarianArchiveEntry::from_row(entry),
            }
            .render()
            .unwrap();
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

    let mut search_query: String = query
        .term
        .split_whitespace()
        .map(|t| format!("\"{t}\""))
        .collect::<Vec<_>>()
        .join(" ");
    if query.title_only.unwrap_or(false) {
        search_query = format!("\"title\": {}", search_query);
    }
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

    let limit = match query.limit {
        Some(l) if (1..=20).contains(&l) => l,
        _ => 20,
    };
    sql_query_builder.push("LIMIT ");
    sql_query_builder.push_bind(limit + 1);

    let offset = match query.offset {
        Some(o) if o > 1 => {
            sql_query_builder.push("OFFSET ");
            sql_query_builder.push_bind(o);
            o
        }
        _ => 0,
    };
    let results: Result<Vec<CarianArchiveRow>, _> =
        sql_query_builder.build_query_as().fetch_all(&data.db).await;
    match results {
        Ok(r) => {
            let has_next_page = r.len() as u32 > limit;
            let entries = r
                .into_iter()
                .map(CarianArchiveEntry::from_row)
                .take(limit as usize)
                .collect();
            let body = SearchTemplate {
                entries,
                search_term: query.term.clone(),
                limit,
                offset,
                has_next_page,
            }
            .render()
            .unwrap();
            HttpResponse::Ok()
                .insert_header(("content-type", "text/html"))
                .body(body)
        }
        Err(e) => HttpResponse::InternalServerError().body(format!("Request failed: {:?}", e)),
    }
}

#[get("/sprite/{sprite_id}.png")]
pub async fn get_sprite(
    data: web::Data<AppState>,
    path: web::Path<(i64,)>,
) -> Result<NamedFile, actix_web::Error> {
    let (sprite_id,) = path.into_inner();

    let result = sqlx::query!("SELECT filepath FROM sprites WHERE id=?", sprite_id)
        .fetch_one(&data.db)
        .await;

    let sprite_path: PathBuf = if let Ok(row) = result {
        row.filepath.into()
    } else {
        return Err(ErrorNotFound("Inexistent sprite id"));
    };

    match NamedFile::open(sprite_path) {
        Ok(file) => Ok(file),
        _ => Err(ErrorInternalServerError("Sprite file not found")),
    }
}
