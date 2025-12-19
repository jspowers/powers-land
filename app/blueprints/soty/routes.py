"""Song of the Year tournament routes"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.soty import soty_bp
from app.blueprints.soty.models import Song, Round, Matchup, Vote
from app.blueprints.soty.services import (
    get_current_user, is_admin, login_required, admin_required,
    SOTYTournamentService, verify_pin
)
from app import db
import time
from datetime import datetime, timedelta


@soty_bp.route('/')
def index():
    """
    Song of the Year Homepage
    Displays all songs with their tournament status
    """
    songs = Song.query.order_by(Song.seed_number).all()
    current_user = get_current_user()

    # Get current active round
    active_round = Round.query.filter_by(status='active').first()

    return render_template('soty/index.html',
                          songs=songs,
                          current_user=current_user,
                          active_round=active_round)


@soty_bp.route('/login', methods=['GET', 'POST'])
def login():
    """PIN entry page"""
    if request.method == 'POST':
        pin = request.form.get('pin')
        user = verify_pin(pin)

        if user:
            
            session.permanent = True  # Use PERMANENT_SESSION_LIFETIME from config
            session['user_id'] = user['user_id']
            session['first_name'] = user['first_name']
            return redirect(url_for('soty.index'))
        else:
            flash('Invalid PIN', 'danger')

    return render_template('soty/login.html')


@soty_bp.route('/logout')
def logout():
    """Clear session"""
    session.clear()
    return redirect(url_for('soty.index'))


@soty_bp.route('/bracket')
@login_required
def bracket():
    """
    Tournament bracket with tabs for each round
    - Shows matchups for each round
    - Vote buttons (active only if round is active)
    - Admin controls (finalize, extend)
    """
    from app.blueprints.soty.services import load_users

    rounds = Round.query.order_by(Round.round_number).all()
    current_user = get_current_user()
    users = load_users()  # Load all users for voter names

    # Build data for each round
    rounds_data = []
    for round_obj in rounds:
        matchups = Matchup.query.filter_by(round_id=round_obj.id).order_by(Matchup.position_in_round).all()

        # Get bye songs for Round 1
        bye_songs = []
        if round_obj.round_number == 1:
            num_songs = Song.query.count()
            if num_songs > 0:
                import math
                bracket_size = 2 ** math.ceil(math.log2(num_songs))
                num_byes = bracket_size - num_songs

                if num_byes > 0:
                    bye_songs = Song.query.filter(
                        Song.seed_number <= num_byes
                    ).order_by(Song.seed_number).all()

        matchups_data = []
        for matchup in matchups:
            # Get user's vote
            user_vote = None
            if current_user:
                vote = Vote.query.filter_by(
                    user_id=current_user['user_id'],
                    matchup_id=matchup.id
                ).first()
                if vote:
                    user_vote = vote.song_id

            # Get voter names for each song (only if round is completed)
            song1_voters = []
            song2_voters = []
            if round_obj.status == 'completed' and matchup.song1_id and matchup.song2_id:
                votes_song1 = Vote.query.filter_by(matchup_id=matchup.id, song_id=matchup.song1_id).all()
                votes_song2 = Vote.query.filter_by(matchup_id=matchup.id, song_id=matchup.song2_id).all()

                for vote in votes_song1:
                    user = users.get(vote.user_id)
                    if user:
                        song1_voters.append(f"{user['first_name']} {user['last_name'][0]}.")

                for vote in votes_song2:
                    user = users.get(vote.user_id)
                    if user:
                        song2_voters.append(f"{user['first_name']} {user['last_name'][0]}.")

            matchups_data.append({
                'matchup': matchup,
                'song1': matchup.song1,
                'song2': matchup.song2,
                'song1_votes': matchup.get_vote_count(matchup.song1_id) if matchup.song1_id else 0,
                'song2_votes': matchup.get_vote_count(matchup.song2_id) if matchup.song2_id else 0,
                'song1_voters': song1_voters,
                'song2_voters': song2_voters,
                'user_vote': user_vote
            })

        # Check if voting is open
        now = int(time.time())
        is_voting_open = (
            round_obj.status == 'active' and
            (not round_obj.end_date or now <= round_obj.end_date)
        )

        rounds_data.append({
            'round': round_obj,
            'matchups': matchups_data,
            'bye_songs': bye_songs,
            'is_active': round_obj.status == 'active',
            'is_voting_open': is_voting_open
        })

    return render_template('soty/bracket.html',
                          rounds_data=rounds_data,
                          current_user=current_user,
                          is_admin=is_admin())


@soty_bp.route('/vote', methods=['POST'])
@login_required
def vote():
    """Submit or update vote for a matchup"""
    matchup_id = request.form.get('matchup_id', type=int)
    song_id = request.form.get('song_id', type=int)
    current_user = get_current_user()

    # Validation
    matchup = Matchup.query.get_or_404(matchup_id)
    round_obj = Round.query.get(matchup.round_id)

    if round_obj.status != 'active':
        return jsonify({'success': False, 'error': 'Round is not active'}), 400

    now = int(time.time())
    if round_obj.end_date and now > round_obj.end_date:
        return jsonify({'success': False, 'error': 'Voting deadline passed'}), 400

    # Check existing vote
    existing_vote = Vote.query.filter_by(
        user_id=current_user['user_id'],
        matchup_id=matchup_id
    ).first()

    if existing_vote:
        if existing_vote.song_id != song_id:
            existing_vote.song_id = song_id
            existing_vote.is_vote_changed = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Vote updated'})
        else:
            return jsonify({'success': True, 'message': 'Vote already recorded'})
    else:
        new_vote = Vote(
            user_id=current_user['user_id'],
            matchup_id=matchup_id,
            song_id=song_id
        )
        db.session.add(new_vote)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Vote recorded'})


@soty_bp.route('/admin/build-bracket', methods=['GET', 'POST'])
@admin_required
def build_bracket():
    """
    Admin page to build initial bracket
    - Seed songs by popularity
    - Generate rounds and Round 1 matchups
    """
    if request.method == 'POST':
        try:
            # Seed songs
            seeded_songs = SOTYTournamentService.seed_songs()

            # Generate rounds
            SOTYTournamentService.generate_rounds()

            # Generate Round 1 matchups
            result = SOTYTournamentService.generate_matchups(seeded_songs)

            # Set Round 1 to active with 96-hour deadline
            round_1 = Round.query.filter_by(round_number=1).first()
            round_1.status = 'active'
            round_1.start_date = int(time.time())
            round_1.end_date = int(time.time() + (96 * 3600))  # 96 hours

            db.session.commit()

            flash(f'Bracket built successfully! {result["total_matchups"]} matchups created with {result["num_byes"]} bye(s). Round 1 is now active.', 'success')
            return redirect(url_for('soty.bracket'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error building bracket: {str(e)}', 'danger')

    # GET: Show preview
    songs = Song.query.order_by(Song.popularity, Song.created_at).all()
    return render_template('soty/admin_build_bracket.html', songs=songs)


@soty_bp.route('/admin/round/<int:round_id>/finalize', methods=['POST'])
@admin_required
def finalize_round(round_id):
    """
    Finalize current round and build next round
    - Mark round completed
    - Determine winners
    - Build next round matchups
    """
    round_obj = Round.query.get_or_404(round_id)

    if round_obj.status != 'active':
        flash('Can only finalize active rounds', 'warning')
        return redirect(url_for('soty.bracket'))

    try:
        # Mark round completed
        round_obj.status = 'completed'
        round_obj.end_date = int(time.time())

        # Mark matchups completed and record winners
        matchups = Matchup.query.filter_by(round_id=round_obj.id).all()
        for matchup in matchups:
            winner = matchup.get_winner()
            if winner:
                matchup.winner_song_id = winner.id
            matchup.status = 'completed'

            # Update max_round_reached for both songs in this matchup
            if matchup.song1:
                matchup.song1.max_round_reached = max(matchup.song1.max_round_reached, round_obj.round_number)
            if matchup.song2:
                matchup.song2.max_round_reached = max(matchup.song2.max_round_reached, round_obj.round_number)

        # Update is_alive status for losers
        for matchup in matchups:
            if matchup.song1_id and matchup.winner_song_id != matchup.song1_id:
                matchup.song1.is_alive = False
            if matchup.song2_id and matchup.winner_song_id != matchup.song2_id:
                matchup.song2.is_alive = False

        # Build next round
        next_matchups = SOTYTournamentService.build_next_round_matchups(round_obj)

        if next_matchups is None:
            # Tournament complete
            flash('Tournament completed!', 'success')
        else:
            # Activate next round
            next_round = Round.query.filter_by(round_number=round_obj.round_number + 1).first()
            next_round.status = 'active'
            next_round.start_date = int(time.time())
            next_round.end_date = int(time.time() + (96 * 3600))  # 96 hours

            flash(f'{round_obj.name} finalized! {next_round.name} is now active.', 'success')

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f'Error finalizing round: {str(e)}', 'danger')

    return redirect(url_for('soty.bracket'))


@soty_bp.route('/admin/round/<int:round_id>/extend', methods=['POST'])
@admin_required
def extend_round(round_id):
    """Extend round deadline by specified hours (default 24)"""
    round_obj = Round.query.get_or_404(round_id)

    extension_hours = int(request.form.get('extension_hours', 24))

    try:
        # Extend this round
        if round_obj.end_date:
            new_end_date = datetime.fromtimestamp(round_obj.end_date) + timedelta(hours=extension_hours)
            round_obj.end_date = int(new_end_date.timestamp())
        else:
            new_end_date = datetime.now() + timedelta(hours=extension_hours)
            round_obj.end_date = int(new_end_date.timestamp())

        # Cascade delay to future rounds
        rounds = Round.query.filter(Round.round_number > round_obj.round_number).all()
        for r in rounds:
            if r.start_date:
                r.start_date += (extension_hours * 3600)
            if r.end_date:
                r.end_date += (extension_hours * 3600)

        db.session.commit()
        flash(f'{round_obj.name} extended by {extension_hours} hours', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error extending round: {str(e)}', 'danger')

    return redirect(url_for('soty.bracket'))


@soty_bp.route('/admin/reset-tournament', methods=['POST'])
@admin_required
def reset_tournament():
    """Reset tournament to initial state (keeps songs)"""
    try:
        # Delete all tournament data
        Vote.query.delete()
        Matchup.query.delete()
        Round.query.delete()

        # Reset song status
        songs = Song.query.all()
        for song in songs:
            song.is_alive = True
            song.max_round_reached = 0
            song.seed_number = None

        db.session.commit()
        flash('Tournament reset successfully! You can now rebuild the bracket.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting tournament: {str(e)}', 'danger')

    return redirect(url_for('soty.index'))
