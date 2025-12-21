#!/usr/bin/env python3
"""
Reset SOTY database and load new songs

Usage:
    python reset_soty.py              # Delete data and reload songs
    python reset_soty.py --schema     # Recreate tables + reload songs
    python reset_soty.py --migrate    # Run migrations + reload songs
"""
import sys
import argparse
import os
from app import create_app, db
from app.blueprints.soty.models import Song, Round, Matchup, Vote
from app.blueprints.soty.services import load_songs_into_db


def reset_schema():
    """Drop and recreate all SOTY tables (handles schema changes)"""
    print("🔧 Recreating SOTY database schema...")

    # Drop all SOTY tables
    inspector = db.inspect(db.engine)
    soty_tables = [
        'soty_votes',
        'soty_matchups',
        'soty_rounds',
        'soty_songs'
    ]

    for table_name in soty_tables:
        if table_name in inspector.get_table_names():
            print(f"  Dropping table: {table_name}")
            db.session.execute(db.text(f"DROP TABLE IF EXISTS {table_name}"))

    db.session.commit()

    # Recreate tables from models
    print("  Creating tables from current schema...")
    db.create_all()
    db.session.commit()

    print("✅ Schema recreated successfully")


def run_migrations():
    """Run Flask-Migrate to handle schema changes"""
    import subprocess

    print("🔄 Running database migrations...")

    try:
        # Run migrations
        result = subprocess.run(
            ['flask', 'db', 'upgrade'],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e.stderr}")
        return False


def reset_data():
    """Delete all SOTY data but preserve schema"""
    print("🗑️  Deleting existing SOTY data...")

    try:
        # Delete in correct order (respecting foreign keys)
        Vote.query.delete()
        Matchup.query.delete()
        Round.query.delete()
        Song.query.delete()

        db.session.commit()
        print("✅ Existing SOTY data deleted")
    except Exception as e:
        print(f"❌ Error deleting data: {e}")
        db.session.rollback()
        raise


def load_songs():
    """Load songs from soty_songs.py"""
    print("\n📦 Loading songs from soty_songs.py...")

    try:
        load_songs_into_db()

        # Count and display songs
        song_count = Song.query.count()
        print(f"✅ Loaded {song_count} songs successfully")

        # Display sample
        print("\n🎵 Sample of loaded songs:")
        for song in Song.query.limit(5).all():
            print(f"  - {song.title} by {song.artist} (popularity: {song.popularity})")

        print(f"\n✨ Total songs loaded: {song_count}")
        return song_count
    except Exception as e:
        print(f"❌ Error loading songs: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Reset SOTY database and reload songs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_soty.py              # Delete data and reload songs (default)
  python reset_soty.py --schema     # Drop/recreate tables + reload (for schema changes)
  python reset_soty.py --migrate    # Run migrations + reload (for schema changes)
        """
    )

    parser.add_argument(
        '--schema',
        action='store_true',
        help='Drop and recreate all SOTY tables (USE WITH CAUTION)'
    )

    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Run Flask-Migrate database migrations before reset'
    )

    parser.add_argument(
        '--data-only',
        action='store_true',
        help='Only reload song data (skip schema changes)'
    )

    args = parser.parse_args()


    # prefer FLASK_ENV if set, otherwise default to production for safety
    env = os.environ.get('FLASK_ENV', 'production')
    app = create_app(env)

    with app.app_context():
        print("=" * 60)
        print("SOTY Database Reset Utility")
        print("=" * 60)

        try:
            # Handle schema changes
            if args.schema:
                confirm = input("\n⚠️  WARNING: This will DROP all SOTY tables. Continue? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("❌ Aborted")
                    return
                reset_schema()

            elif args.migrate:
                if not run_migrations():
                    print("❌ Aborting due to migration failure")
                    return

            # Reset data (unless data-only with no other flags)
            if not args.data_only or args.schema or args.migrate:
                reset_data()

            # Load songs
            song_count = load_songs()

            print("\n" + "=" * 60)
            print(f"✨ Reset complete! {song_count} songs ready for tournament")
            print("=" * 60)
            print("\n🚀 Next steps:")
            print("  1. Log in as admin (PIN: 7553)")
            print("  2. Go to /soty/admin/build-bracket")
            print("  3. Build the tournament bracket")

        except Exception as e:
            print(f"\n❌ Reset failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
