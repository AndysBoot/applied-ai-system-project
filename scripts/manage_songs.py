"""
CLI for growing the real song catalog in data/songs.db.

Usage:
    python scripts/manage_songs.py list
    python scripts/manage_songs.py add "Title" "Artist" genre mood energy valence danceability acousticness
    python scripts/manage_songs.py import-csv path/to/more_songs.csv
    python scripts/manage_songs.py import-musicbrainz rock --limit 25
    python scripts/manage_songs.py import-musicbrainz-bulk --per-genre 100

The database is NOT seeded from data/songs.csv -- that file is a small
fabricated example catalog kept only as the CSV-loading fallback in
src.recommender.load_songs(); the DB only ever contains what you explicitly
add here. add_song() auto-assigns the next id.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import DB_PATH, add_song, count_songs, init_db, load_songs_from_db  # noqa: E402
from src.musicbrainz import GENRE_FEATURE_ESTIMATES, fetch_recordings_by_genre  # noqa: E402


def cmd_list(_args) -> None:
    init_db()
    songs = load_songs_from_db()
    for song in songs:
        print(f"{song['id']:>4}  {song['title']} — {song['artist']} "
              f"[{song['genre']}/{song['mood']}]")
    print(f"\n{len(songs)} songs in {DB_PATH}")


def cmd_add(args) -> None:
    init_db()
    song = {
        "title": args.title,
        "artist": args.artist,
        "genre": args.genre,
        "mood": args.mood,
        "energy": args.energy,
        "valence": args.valence,
        "danceability": args.danceability,
        "acousticness": args.acousticness,
    }
    song_id = add_song(song)
    print(f"Added song {song_id}: {args.title} — {args.artist} (total: {count_songs()})")


def cmd_import_csv(args) -> None:
    init_db()
    added = 0
    with open(args.path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = {
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            }
            add_song(song)
            added += 1
    print(f"Imported {added} songs from {args.path} (total: {count_songs()})")


def _existing_keys() -> set:
    """(title.lower(), artist.lower()) for every song already in the DB, so imports don't re-add it."""
    return {(s["title"].strip().lower(), s["artist"].strip().lower()) for s in load_songs_from_db()}


def cmd_import_musicbrainz(args) -> None:
    init_db()
    seen = _existing_keys()
    songs = fetch_recordings_by_genre(args.genre, limit=args.limit, seen_keys=seen)
    for song in songs:
        add_song(song)
    print(
        f"Imported {len(songs)} real songs tagged '{args.genre}' from MusicBrainz "
        f"(total: {count_songs()}).\n"
        "Note: title/artist/genre are real; mood/energy/valence/danceability/"
        "acousticness/tempo_bpm are genre-level estimates, not measured audio "
        "features -- MusicBrainz doesn't provide those. See src/musicbrainz.py."
    )


def cmd_import_musicbrainz_bulk(args) -> None:
    init_db()
    genres = args.genres if args.genres else sorted(GENRE_FEATURE_ESTIMATES)
    seen = _existing_keys()
    total_added = 0

    for i, genre in enumerate(genres):
        try:
            songs = fetch_recordings_by_genre(genre, limit=args.per_genre, seen_keys=seen)
        except Exception as e:
            print(f"  ! '{genre}' failed ({e}), skipping")
            continue
        for song in songs:
            add_song(song)
        total_added += len(songs)
        print(f"  [{i + 1}/{len(genres)}] '{genre}': +{len(songs)} songs (running total: {count_songs()})")

    print(
        f"\nBulk import done: {total_added} real songs added across {len(genres)} genres "
        f"(total catalog: {count_songs()}).\n"
        "Note: title/artist/genre are real; the numeric/mood fields are genre-level "
        "estimates -- see src/musicbrainz.py."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all songs in the database").set_defaults(func=cmd_list)

    add_parser = subparsers.add_parser("add", help="Add a single song to the database")
    add_parser.add_argument("title")
    add_parser.add_argument("artist")
    add_parser.add_argument("genre")
    add_parser.add_argument("mood")
    add_parser.add_argument("energy", type=float)
    add_parser.add_argument("valence", type=float)
    add_parser.add_argument("danceability", type=float)
    add_parser.add_argument("acousticness", type=float)
    add_parser.set_defaults(func=cmd_add)

    import_parser = subparsers.add_parser("import-csv", help="Bulk-add songs from another CSV file")
    import_parser.add_argument("path")
    import_parser.set_defaults(func=cmd_import_csv)

    mb_parser = subparsers.add_parser(
        "import-musicbrainz", help="Bulk-add real songs from the MusicBrainz API by genre tag"
    )
    mb_parser.add_argument("genre", help=f"One of: {', '.join(sorted(GENRE_FEATURE_ESTIMATES))}")
    mb_parser.add_argument("--limit", type=int, default=25, help="Max recordings to fetch (default 25)")
    mb_parser.set_defaults(func=cmd_import_musicbrainz)

    bulk_parser = subparsers.add_parser(
        "import-musicbrainz-bulk",
        help="Bulk-add real songs from MusicBrainz across many genres in one run (for thousands of songs)",
    )
    bulk_parser.add_argument(
        "--genres", nargs="+", default=None,
        help=f"Genres to import (default: all {len(GENRE_FEATURE_ESTIMATES)} known genres). "
             f"Choices: {', '.join(sorted(GENRE_FEATURE_ESTIMATES))}",
    )
    bulk_parser.add_argument("--per-genre", type=int, default=100, help="Max songs to fetch per genre (default 100)")
    bulk_parser.set_defaults(func=cmd_import_musicbrainz_bulk)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
