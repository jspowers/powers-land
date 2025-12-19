"""Spotify API service for fetching song metadata"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re


SOTY_SONGS = [
    "297PYWIVLP38C1a92ND8Kv",
    "2SGDxeH9stHj9bYbqtClHw",
    "77evpfqHmmSklsFpo8wLCB",
    "3EgkmxKS8IN08vbdoL7cFi",
    "307FpyXlwHxNJ4k6s9j3yD",
    "0pDEOMK5Gds7j913G0MYEB",
    "0fU5NxjkR689ve8OU9bu14",
    "1YQ0OTXmx9rDICY61OgbNZ",
    "59P1nrdEImkAKa1nyW9X2e",
    "2PiqZzkHpqtR7j7NkbBiwJ",
    "1ElySIlHwm1HX7sUjAZZnp",
    "0jhgOpwjx6TgKmiUkuV3ba",
    "0dgjHnrUPdFjcHSWSoPkkF",
    "36Lb2L21fDT7vtl0r7zpa5",
    "23tsQgyGHxGZjHM8uWe9v5",
    "2Sa7c1IlT7bVHEt8s982It",
    "0doTgRQa7qyw5JYPfwhPcK",
    "6r4aDudAgH1fdtmNNNXR3N",
    "7uJsXh9G2w5DRnffzlwdFt",
    "2PbeypWBKBrnEUmjVL7Y6b",
    "4Sr36ITQ9JMBHz5xuQM2Ql",
    "6VfeVmzckgv3N0qYutzJOg",
    "5XyN4ThYy7yLPol7FEGRty",
]


class SpotifyService:
    """Service for interacting with Spotify API"""

    def __init__(self, client_id, client_secret):
        """Initialize Spotify client with credentials"""
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))


    def get_track_metadata(self, track_id):
        """Fetch song metadata from Spotify URL

        Args:
            url: Spotify track URL

        Returns:
            dict: Song metadata including title, artist, album, etc.

        Raises:
            ValueError: If URL is invalid or track not found
        """

        try:
            track = self.sp.track(track_id)
        except Exception as e:
            raise ValueError(f"Could not fetch track from Spotify: {str(e)}")

        return {
            'title': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'release_date': track['album'].get('release_date'),
            'release_date_precision': track['album'].get('release_date_precision'),
            'popularity': track.get('popularity'),
            'isrc_number': track.get('external_ids', {}).get('isrc'),
            'duration_seconds': track['duration_ms'] // 1000,
            'thumbnail_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'spotify_track_id': track_id
        }

song_data = [
    
]


Spot = SpotifyService(
    client_id="1779ae39983343bfb63afdbfc61ce997",
    client_secret="686c123e4d744113a0e2a14a506ddd35"
)

for track_id in SOTY_SONGS:

    metadata = Spot.get_track_metadata(track_id=track_id)
    song_data.append({
            'spotify_track_id': metadata['spotify_track_id'],
            'title': metadata['title'],
            'artist': metadata['artist'],
            'album': metadata['album'],
            'release_date': metadata['release_date'],
            'popularity': metadata['popularity'],
            'artwork_url': metadata['thumbnail_url']
        })

print(song_data)


