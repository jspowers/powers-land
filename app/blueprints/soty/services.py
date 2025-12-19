"""Song of the Year tournament services"""
import json
import os
import math
import time
from flask import session, redirect, url_for, flash
from functools import wraps
from app import db
from app.blueprints.soty.models import Song, Round, Matchup
from .soty_songs import SOTY_SONGS


# ==============================================================================
# USER AUTHENTICATION (PIN-based)
# ==============================================================================

def load_users():
    """Load users from .users.json file"""
    users_file = os.path.join(os.path.dirname(__file__), 'users.json')
    with open(users_file, 'r') as f:
        users = json.load(f)
    return {user['user_id']: user for user in users}


def verify_pin(pin):
    """Verify PIN and return user data if valid"""
    users = load_users()
    for user_id, user in users.items():
        if user['account_pin'] == pin:
            return user
    return None


def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        users = load_users()
        return users.get(session['user_id'])
    return None


def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user.get('admin', False)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('soty.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Admin access required', 'danger')
            return redirect(url_for('soty.index'))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# SONG DATA (Hardcoded - user will provide)
# ==============================================================================

def load_songs_into_db():
    """Load hardcoded songs into database (idempotent)"""
    for song_data in SOTY_SONGS:
        # Check if song already exists
        existing = Song.query.filter_by(
            spotify_track_id=song_data['spotify_track_id']
        ).first()

        if not existing:
            song = Song(
                spotify_track_id=song_data['spotify_track_id'],
                title=song_data['title'],
                artist=song_data['artist'],
                album=song_data.get('album'),
                release_date=song_data.get('release_date'),
                popularity=song_data.get('popularity'),
                artwork_url=song_data.get('artwork_url')
            )
            db.session.add(song)

    db.session.commit()
    print(f"Loaded {len(SOTY_SONGS)} songs into database")


# ==============================================================================
# TOURNAMENT SERVICE (Bracket Logic)
# ==============================================================================

class SOTYTournamentService:
    """Service for SOTY tournament bracket management"""

    @staticmethod
    def seed_songs():
        """Seed all songs by popularity (LOWER = better seed)"""
        songs = Song.query.all()

        # Normalize NULL popularity to 100 (worst)
        for song in songs:
            if song.popularity is None:
                song.popularity = 100

        # Sort by popularity ascending (lower number = better seed)
        seeded_songs = sorted(songs, key=lambda s: (s.popularity, s.created_at))

        # Assign seed numbers
        for idx, song in enumerate(seeded_songs):
            song.seed_number = idx + 1

        db.session.commit()
        return seeded_songs

    @staticmethod
    def generate_rounds():
        """Generate rounds based on song count"""
        song_count = Song.query.count()
        if song_count < 2:
            return []

        # Calculate rounds needed for single-elimination bracket
        num_rounds = math.ceil(math.log2(song_count))

        rounds = []
        for round_num in range(1, num_rounds + 1):
            round_name = SOTYTournamentService._get_round_name(round_num, num_rounds)

            round_obj = Round(
                round_number=round_num,
                name=round_name,
                status='pending'
            )
            db.session.add(round_obj)
            rounds.append(round_obj)

        db.session.commit()
        return rounds

    @staticmethod
    def _get_round_name(round_num, total_rounds):
        """Generate human-readable round names"""
        rounds_from_end = total_rounds - round_num

        if rounds_from_end == 0:
            return "Finals"
        elif rounds_from_end == 1:
            return "Semifinals"
        elif rounds_from_end == 2:
            return "Quarterfinals"
        else:
            # Calculate participants in this round
            participants = 2 ** (total_rounds - round_num + 1)
            return f"Round of {participants}"

    @staticmethod
    def generate_matchups(seeded_songs):
        """
        Generate ONLY Round 1 matchups for the tournament bracket.
        Future rounds are built on-demand as rounds are finalized.
        """
        song_count = len(seeded_songs)
        if song_count < 2:
            return {'round_1_matchups': [], 'total_matchups': 0, 'num_byes': 0}

        # Get Round 1 (should already exist from generate_rounds)
        round_1 = Round.query.filter_by(round_number=1).first()

        if not round_1:
            raise ValueError("Round 1 does not exist. Call generate_rounds() first.")

        # Calculate bracket size (next power of 2)
        bracket_size = 2 ** math.ceil(math.log2(song_count))
        num_byes = bracket_size - song_count

        # Round 1: Create matchups for non-bye songs
        # Best seeds (lowest seed_numbers) get byes, remaining songs compete in Round 1
        round_1_matchups = []
        songs_in_round_1 = seeded_songs[num_byes:]  # Skip best N seeds

        # Pair songs: best remaining seed vs worst seed
        num_round_1_matchups = len(songs_in_round_1) // 2
        for i in range(num_round_1_matchups):
            high_seed_song = songs_in_round_1[i]
            low_seed_song = songs_in_round_1[-(i + 1)]

            matchup = Matchup(
                round_id=round_1.id,
                position_in_round=i,
                song1_id=high_seed_song.id,
                song2_id=low_seed_song.id,
                status='pending'
            )
            db.session.add(matchup)
            round_1_matchups.append(matchup)

        db.session.commit()

        return {
            'round_1_matchups': round_1_matchups,
            'total_matchups': len(round_1_matchups),
            'num_byes': num_byes
        }

    @staticmethod
    def build_next_round_matchups(completed_round):
        """
        Build matchups for the round following the completed round.
        Uses winners from completed round to populate next round matchups.
        """
        # Get next round
        next_round = Round.query.filter_by(
            round_number=completed_round.round_number + 1
        ).first()

        if not next_round:
            return None  # Tournament complete

        # Get winners from completed round
        completed_matchups = Matchup.query.filter_by(
            round_id=completed_round.id
        ).order_by(Matchup.position_in_round).all()

        winners = []
        for matchup in completed_matchups:
            winner = matchup.get_winner()
            if winner:
                winners.append(winner)

        # Special case: Round 1 � Round 2 (handle byes)
        if completed_round.round_number == 1:
            # Get bye songs by seed_number (best seeds got byes)
            num_songs = Song.query.count()
            bracket_size = 2 ** math.ceil(math.log2(num_songs))
            num_byes = bracket_size - num_songs

            bye_songs = Song.query.filter(
                Song.seed_number <= num_byes
            ).order_by(Song.seed_number).all()

            return SOTYTournamentService._build_round_2_with_byes(
                next_round, winners, bye_songs
            )

        # Normal case: pair winners by seed
        matchups_created = []
        sorted_winners = sorted(winners, key=lambda s: s.seed_number)

        for i in range(0, len(sorted_winners), 2):
            if i + 1 < len(sorted_winners):
                matchup = Matchup(
                    round_id=next_round.id,
                    position_in_round=i // 2,
                    song1_id=sorted_winners[i].id,
                    song2_id=sorted_winners[i + 1].id,
                    status='pending'
                )
                db.session.add(matchup)
                matchups_created.append(matchup)

        db.session.commit()
        return matchups_created

    @staticmethod
    def _build_round_2_with_byes(next_round, round_1_winners, bye_songs):
        """
        Build Round 2 matchups with bye songs and Round 1 winners.
        Pairs best seeds with worst seeds for balanced matchups.
        """
        matchups_created = []

        # Sort both lists by seed_number (ascending - best seed first)
        sorted_byes = sorted(bye_songs, key=lambda s: s.seed_number)
        sorted_winners = sorted(round_1_winners, key=lambda s: s.seed_number)

        # Combine: byes first (they have better seeds), then winners
        all_advancing = sorted_byes + sorted_winners

        # Pair: best vs worst, 2nd best vs 2nd worst, etc.
        for i in range(len(all_advancing) // 2):
            high_seed = all_advancing[i]
            low_seed = all_advancing[-(i + 1)]

            matchup = Matchup(
                round_id=next_round.id,
                position_in_round=i,
                song1_id=high_seed.id,
                song2_id=low_seed.id,
                status='pending'
            )
            db.session.add(matchup)
            matchups_created.append(matchup)

        db.session.commit()
        return matchups_created
