"""Spotify API service for fetching song metadata"""

import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials
import requests


SOTY_SONGS = [
    "1Bmszn7gaym9lx8CGrq2SA",
    "06vnM67RcfQcc7oPQRA9tP",
    "45hNb2Uha7uFTSpTWVDGt4",
    "4XosapYiYaXGcxc83p3DD9",
    "5CKp1RqaCeUYDGqo14KMfU",
    "3cZajhyr8LmtPfHZ9296tj",
    "5jRKYf6UqyjIFf8dagJ9pT",
    "1lbNgoJ5iMrMluCyhI4OQP",
    "2262bWmqomIaJXwCRHr13j",
    "1fLTi1wA2FPONA5SAIoKJX",
    "7t0ohvf7w4e8VacR124wbA",
    "1QnFKAPgZ7GI9sYITPuYyL",
    "2bWlEirBgnK78PY6ITEcZG",
    "3diMgXk3RxGChNwsAVqyIL",
    "6XA6bozZwlowStujsKQoIY",
    "73vfMXcXa6iY1E3lpf2fZO",
    "1cQQB9z7fNQQ2VzSkslt7Y",
    "2SGj1WdNaTwW00cz9GO1AO",
    "3OQk21nMrEPnc5KXePcv6E",
    "3a73t7XIrNt6i3G4f3hw9E",
    "2P362P669T4HGZQeFVucgO",
    "5gGqgnain6yTxQF6UJagqL",
    "7DTE4ib3z3j2syoUnRogPu",
    "6ATGoNeKZih1AhZ8Ossy1H",
    "2TugrDKkd55mfVOMVZsfO8",
    "7qSaRUz9tOTtjzzifPL2Jv",
    "3M61o9wFaLaCqixyKx8DC2",
    "0k9JIBszlCqCa4SpXI353F",
    "5dUCixiCL0CcIUdlgUl1ct",
    "5RYBjITAd8YJ24ugbTU4Yr",

]


class SpotifyService:
    """Service for interacting with Spotify API"""

    def __init__(self, client_id, client_secret):
        """Initialize Spotify client with credentials"""
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )

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
            "title": track["name"],
            "artist": ", ".join([artist["name"] for artist in track["artists"]]),
            "album": track["album"]["name"],
            "release_date": track["album"].get("release_date"),
            "release_date_precision": track["album"].get("release_date_precision"),
            "popularity": track.get("popularity"),
            "isrc_number": track.get("external_ids", {}).get("isrc"),
            "duration_seconds": track["duration_ms"] // 1000,
            "thumbnail_url": (
                track["album"]["images"][0]["url"] if track["album"]["images"] else None
            ),
            "spotify_track_id": track_id,
            "isrc_number": track.get("external_ids", {}).get("isrc"),
            "apple_music_id": None,
        }


song_data = []


Spot = SpotifyService(
    client_id="1779ae39983343bfb63afdbfc61ce997",
    client_secret="686c123e4d744113a0e2a14a506ddd35",
)

for track_id in SOTY_SONGS:

    metadata = Spot.get_track_metadata(track_id=track_id)
    
    apple_music_id = requests.get(
        f"https://api.song.link/v1-alpha.1/links?url=open.spotify.com/track/{track_id}"
        ).json()["linksByPlatform"].get('appleMusic', {}).get('entityUniqueId', 'NO_ID')
    
    apple_music_id = apple_music_id.replace("ITUNES_SONG::", "") if apple_music_id != 'NO_ID' else 'NO_ID'
    
    song_data.append(
        {
            "spotify_track_id": metadata["spotify_track_id"],
            "title": metadata["title"],
            "artist": metadata["artist"],
            "album": metadata["album"],
            "release_date": metadata["release_date"],
            "popularity": metadata["popularity"],
            "artwork_url": metadata["thumbnail_url"],
            "isrc_number": metadata["isrc_number"],
            "apple_music_id": apple_music_id,
        }
    )

print(song_data)

