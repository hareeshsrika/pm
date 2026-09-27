# Database approach

The MVP uses a local SQLite database at the path configured by `DATABASE_PATH`. The database will be created automatically if it does not exist. SQLite is sufficient for the local single-container MVP and keeps the deployment simple.

## Schema

The proposed schema is recorded in [database-schema.json](database-schema.json). It contains four tables:

- `users` stores user identity and leaves a nullable password-hash field for the future database-backed authentication flow.
- `boards` stores one board per user through a unique `user_id` constraint.
- `columns` stores the five fixed board columns, their editable titles, and their order.
- `cards` stores card content, ownership through `board_id`, column membership, and order within a column.

The current hardcoded login remains the source of truth for Part 4. The database user record and `password_hash` field are reserved for the later authentication transition; plaintext passwords are never stored.

## Initialization

Part 6 will initialize the database with Python's standard-library `sqlite3` module:

1. Create the parent directory for `DATABASE_PATH`.
2. Open the SQLite file and enable foreign keys for each connection.
3. Create the tables and indexes if they do not exist.
4. Seed the hardcoded MVP user and their initial board only when they are absent.
5. Commit initialization in one transaction.

The initial board has five columns in this fixed order: Backlog, Discovery, In Progress, Review, and Done. Column titles may change, but columns cannot be added, removed, or reordered in the MVP.

## Ordering and mutations

Column and card order is stored as zero-based integers. A move, delete, or insertion will update the affected rows in one transaction and then normalize positions so there are no gaps. Every board mutation will verify the authenticated user's ownership before changing rows.

## API representation

The board API will return the normalized frontend-compatible shape shown in `board_api_json` in the schema file: an `id`, ordered `columns` with `cardIds`, and a `cards` map. The database remains normalized while the API remains convenient for the existing frontend and for later AI context.

## Migration assumption

The MVP will use SQLite's `PRAGMA user_version` as a small schema version. Initialization will apply the initial schema when the version is zero. A later schema change will add a numbered migration step and increment the pragma value. No migration framework is needed for the local MVP.
