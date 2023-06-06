mod routes;
mod schema;

use actix_web::{web, App, HttpServer};
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};

use routes::{get_entry, home, search, style};

pub struct AppState {
    db: SqlitePool,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    std::env::set_var("RUST_LOG", "debug");
    env_logger::init();
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect("sqlite://elden_ring.db")
        .await
        .expect("Unable to connect to the database");

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(AppState { db: pool.clone() }))
            .service(home)
            .service(get_entry)
            .service(search)
            .service(style)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
