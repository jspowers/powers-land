"""Flask CLI commands for SOTY blueprint"""
import click
from flask import Blueprint
from app import db
from app.blueprints.soty.models import Song, Round, Matchup, Vote
from app.blueprints.soty.services import load_songs_into_db


# Create a blueprint for CLI commands
soty_cli = Blueprint('soty', __name__)


@soty_cli.cli.command('load-songs')
@click.option('--reset', is_flag=True, help='Delete existing songs before loading')
def load_songs_command(reset):
    """Load songs from soty_songs.py into the database

    Usage:
        flask soty load-songs              # Load songs (skip if already exist)
        flask soty load-songs --reset      # Delete existing songs and reload
    """
    click.echo("=" * 60)
    click.echo("SOTY Song Loader")
    click.echo("=" * 60)

    try:
        if reset:
            click.echo("\n🗑️  Deleting existing songs...")
            # Delete in correct order (respecting foreign keys)
            Vote.query.delete()
            Matchup.query.delete()
            Round.query.delete()
            Song.query.delete()
            db.session.commit()
            click.echo("✅ Existing data deleted")

        click.echo("\n📦 Loading songs from soty_songs.py...")
        load_songs_into_db()

        # Count and display songs
        song_count = Song.query.count()
        click.echo(f"✅ Loaded {song_count} songs successfully")

        # Display sample
        click.echo("\n🎵 Sample of loaded songs:")
        for song in Song.query.limit(5).all():
            click.echo(f"  - {song.title} by {song.artist} (popularity: {song.popularity})")

        click.echo(f"\n✨ Total songs in database: {song_count}")
        click.echo("=" * 60)
        click.echo("\n🚀 Next steps:")
        click.echo("  1. Log in as admin (PIN: 7553)")
        click.echo("  2. Go to /soty/admin/build-bracket")
        click.echo("  3. Build the tournament bracket")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@soty_cli.cli.command('reset-all')
@click.confirmation_option(prompt='⚠️  This will DELETE all SOTY data. Continue?')
def reset_all_command():
    """Delete ALL SOTY data (votes, matchups, rounds, songs)

    Usage:
        flask soty reset-all
    """
    click.echo("=" * 60)
    click.echo("SOTY Full Reset")
    click.echo("=" * 60)

    try:
        click.echo("\n🗑️  Deleting all SOTY data...")

        # Delete in correct order (respecting foreign keys)
        Vote.query.delete()
        Matchup.query.delete()
        Round.query.delete()
        Song.query.delete()

        db.session.commit()

        click.echo("✅ All SOTY data deleted successfully")
        click.echo("\n💡 Tip: Run 'flask soty load-songs' to reload songs")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        db.session.rollback()
        raise click.Abort()


@soty_cli.cli.command('stats')
def stats_command():
    """Show SOTY database statistics

    Usage:
        flask soty stats
    """
    click.echo("=" * 60)
    click.echo("SOTY Database Statistics")
    click.echo("=" * 60)

    try:
        song_count = Song.query.count()
        round_count = Round.query.count()
        matchup_count = Matchup.query.count()
        vote_count = Vote.query.count()

        click.echo(f"\n📊 Current Data:")
        click.echo(f"  Songs:    {song_count}")
        click.echo(f"  Rounds:   {round_count}")
        click.echo(f"  Matchups: {matchup_count}")
        click.echo(f"  Votes:    {vote_count}")

        if song_count > 0:
            click.echo(f"\n🎵 Sample songs:")
            for song in Song.query.limit(5).all():
                click.echo(f"  - {song.title} by {song.artist}")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort()
