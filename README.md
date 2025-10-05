# Pulser News Aggregation Service

Pulser is a lightweight service that aggregates articles from RSS feeds, enriches
content with heuristic scoring and auto-generated hashtags, and stores the result
in a local SQLite database. The project demonstrates how to build maintainable
pipelines that can be executed synchronously, asynchronously, or in parallel.

## Features

- **Pipeline infrastructure** – reusable base classes for building synchronous
  and asynchronous workflows.
- **RSS ingestion** – fetches items from configurable RSS feeds and stores them
  in a relational database.
- **Content enrichment** – assigns quality scores and generates hashtags using
  deterministic heuristics.
- **Extensible web scrapers** – helper classes that collect article links from
  common news websites.
- **Command-line runner** – bootstrap the database, manage channels, and run the
  parser in a single command.

## Project structure

```
app/
├── bot/                # Configuration helpers
├── database/           # SQLite models and managers
├── misc/               # Utilities (logging, threads, scheduler, paths)
├── pipelines/          # Pipeline base classes and implementations
│   ├── pipeline.py
│   └── pipes/
│       ├── parser/     # RSS parser pipeline and helpers
│       └── test_pipeline.py
run_parser.py           # CLI entry point
requirements.txt
```

## Getting started

1. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Bootstrap sample RSS channels (optional but recommended)**

   ```bash
   python run_parser.py --bootstrap
   ```

3. **Run the parser**

   ```bash
   python run_parser.py --run
   ```

   The command fetches RSS entries, stores new posts in `data/pulser.db`, and
   generates hashtags for high-quality entries.

## Command-line options

- `--bootstrap` – populate the database with a set of sample RSS feeds.
- `--list` – display configured channels.
- `--add-channel --title <TITLE> --url <URL>` – store a custom feed in the
  database. You can also change the channel type via `--channel-type`.
- `--run` – execute the parser once. When no other flags are provided the
  command defaults to running the pipeline.

Channels are stored in the `channels` table with a `channel_type` column. Type
`1` is used for RSS feeds, while type `3` can be reserved for Telegram channels.

## Database schema

The SQLite database lives in `data/pulser.db` and is created automatically. The
following tables are available:

- `channels` – stores configured sources (`channel_type`, `title`, `url`).
- `posts` – parsed entries with `channel_id`, `title`, `content`, `link`, and a
  heuristic `rating`.
- `posts_hashtags` – generated hashtags for high-rated posts.

## Extending the parser

- **Pipeline customization** – subclass `app.pipelines.pipeline.Pipeline` to
  define new workflows or reuse `DynamicPipeline` for ad-hoc task orchestration.
- **Web scrapers** – add new scrapers next to the existing classes in
  `app/pipelines/pipes/parser/parser_web/common_http/`. They inherit from
  `AbstractCommonWeb` which provides convenience helpers for fetching and
  validating links.
- **Telegram support** – the skeleton for Telegram parsing is present in
  `Parser.telegram_parser`. Provide valid API credentials via environment
  variables (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_BOT_TOKEN`) and
  extend the routine as needed.

## Testing the pipeline infrastructure

You can run the demo pipeline to observe synchronous and parallel steps:

```bash
python -m app.pipelines.pipes.test_pipeline
```

The script logs task execution, spawns background workers, and demonstrates how
pipeline hooks work.

## Troubleshooting

- The parser skips items whose links already exist in the database.
- Network errors are logged and do not stop the entire run; the pipeline simply
  moves to the next feed.
- If you plan to run the scrapers that require dynamic content, install a modern
  browser driver or replace `_extremely_hard_getter` with a solution that fits
  your infrastructure.

## License

This project is distributed under the terms of the MIT License. See `LICENSE`
for details.
