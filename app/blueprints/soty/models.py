"""Song of the Year tournament models"""
from app import db
from app.models.base import Base


class Song(Base):
    """Song model for tournament entries"""
    __tablename__ = 'soty_songs'

    id = db.Column(db.Integer, primary_key=True)
    spotify_track_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    apple_music_id = db.Column(db.String(50), unique=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    album = db.Column(db.String(200))
    release_date = db.Column(db.String(20))  # YYYY-MM-DD format from Spotify
    popularity = db.Column(db.Integer)  # 0-100, lower is better for seeding
    seed_number = db.Column(db.Integer)  # Assigned after seeding (1 = best seed)
    artwork_url = db.Column(db.String(500))  # Album artwork from Spotify

    # Tournament tracking
    is_alive = db.Column(db.Boolean, default=True)
    max_round_reached = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Song {self.title} by {self.artist}>'


class Round(Base):
    """Tournament round model"""
    __tablename__ = 'soty_rounds'

    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    name = db.Column(db.String(50))  # "Round of 16", "Quarterfinals", "Semifinals", "Finals"
    status = db.Column(db.String(20), default='pending')  # 'pending', 'active', 'completed'
    start_date = db.Column(db.Integer)  # Unix timestamp
    end_date = db.Column(db.Integer)  # Unix timestamp (96-hour default deadline)

    # Relationships
    matchups = db.relationship('Matchup', backref='round', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Round {self.round_number}: {self.name} ({self.status})>'


class Matchup(Base):
    """Tournament matchup model"""
    __tablename__ = 'soty_matchups'

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('soty_rounds.id'), nullable=False)
    position_in_round = db.Column(db.Integer, nullable=False)  # 0, 1, 2... (ordering)

    song1_id = db.Column(db.Integer, db.ForeignKey('soty_songs.id'))
    song2_id = db.Column(db.Integer, db.ForeignKey('soty_songs.id'))
    winner_song_id = db.Column(db.Integer, db.ForeignKey('soty_songs.id'))

    status = db.Column(db.String(20), default='pending')  # 'pending', 'voting', 'completed'

    # Relationships
    song1 = db.relationship('Song', foreign_keys=[song1_id], backref='matchups_as_song1')
    song2 = db.relationship('Song', foreign_keys=[song2_id], backref='matchups_as_song2')
    winner = db.relationship('Song', foreign_keys=[winner_song_id], backref='matchups_won')
    votes = db.relationship('Vote', backref='matchup', lazy='dynamic', cascade='all, delete-orphan')

    def get_winner(self):
        """Determine winner based on vote count"""
        if self.winner_song_id:
            return Song.query.get(self.winner_song_id)

        if not self.song1_id or not self.song2_id:
            return None

        song1_votes = self.votes.filter_by(song_id=self.song1_id).count()
        song2_votes = self.votes.filter_by(song_id=self.song2_id).count()

        if song1_votes > song2_votes:
            return self.song1
        elif song2_votes > song1_votes:
            return self.song2
        else:
            # Tie: higher seed wins (LOWER seed_number)
            return self.song1 if self.song1.seed_number < self.song2.seed_number else self.song2

    def get_vote_count(self, song_id):
        """Get vote count for a specific song in this matchup"""
        return self.votes.filter_by(song_id=song_id).count()

    def __repr__(self):
        return f'<Matchup R{self.round_id}P{self.position_in_round}: {self.status}>'


class Vote(Base):
    """Vote model for user votes on matchups"""
    __tablename__ = 'soty_votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # From session (not FK to User table)
    matchup_id = db.Column(db.Integer, db.ForeignKey('soty_matchups.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('soty_songs.id'), nullable=False)

    is_vote_changed = db.Column(db.Boolean, default=False)

    # Relationships
    song = db.relationship('Song', backref='votes_received')

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('user_id', 'matchup_id', name='unique_user_matchup_vote'),
    )

    def __repr__(self):
        return f'<Vote user={self.user_id} matchup={self.matchup_id} song={self.song_id}>'
