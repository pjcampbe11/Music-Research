#!/usr/bin/env python3
"""
AI Music Recommendation System with Working Spotify Integration
FINAL SINGLE FILE - No external dependencies on broken spotify_integration.py
"""

import pandas as pd
import sys
import os
from typing import Optional, List, Dict
import json
import re

# Import your existing classes
from DataCleaning import DataCleaner
from MusicRecommender import MusicRecommender
from PlaylistCreator import PlaylistCreator

# Import Spotipy directly - NO broken spotify_integration.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SimpleSpotifyIntegration:
    """
    Working Spotify integration using manual URL authentication.
    No browser dependency - just copy/paste URLs.
    EXACTLY the same as simple_spotify_working.py
    """
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize with your Spotify app credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = "http://127.0.0.1:8888/callback"
        self.scope = "playlist-modify-public playlist-modify-private"
        
        # Create SpotifyOAuth with cache
        self.sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=".spotify_cache",  # Cache tokens locally
            open_browser=False  # Don't try to open browser automatically
        )
        
        self.sp = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with Spotify using manual URL method.
        This method ALWAYS works regardless of browser settings.
        """
        try:
            print("🔐 Spotify Authentication Required")
            print("=" * 50)
            
            # Step 1: Get the authorization URL
            auth_url = self.sp_oauth.get_authorize_url()
            
            print("📋 COPY THIS URL AND OPEN IT IN YOUR BROWSER:")
            print(f"\n{auth_url}\n")
            print("👆 Copy the URL above and paste it into any web browser")
            print("🔑 Log in to Spotify and click 'Agree' to authorize the app")
            print("📄 After authorization, you'll see a page that might show an error")
            print("🔗 Copy the ENTIRE URL from your browser's address bar")
            print("   (It should start with: http://127.0.0.1:8888/callback?code=...)")
            print("=" * 50)
            
            # Step 2: Get the redirect URL from the user
            while True:
                redirect_url = input("\n📥 Paste the full redirect URL here: ").strip()
                
                if not redirect_url:
                    print("❌ Please paste the redirect URL")
                    continue
                    
                if not redirect_url.startswith("http://127.0.0.1:8888/callback"):
                    print("❌ That doesn't look like the right URL. It should start with:")
                    print("   http://127.0.0.1:8888/callback?code=...")
                    continue
                    
                break
            
            # Step 3: Extract the code and get token
            print("🔄 Processing authorization...")
            
            try:
                # Parse the authorization code from the URL
                code = self.sp_oauth.parse_response_code(redirect_url)
                if not code:
                    print("❌ Could not find authorization code in URL")
                    return False
                
                # Get the access token
                token_info = self.sp_oauth.get_access_token(code)
                if not token_info:
                    print("❌ Could not get access token")
                    return False
                
                # Create Spotify client
                self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)
                
                # Test the connection
                user = self.sp.current_user()
                print(f"✅ Success! Authenticated as: {user['display_name']} (@{user['id']})")
                print(f"🎵 Ready to create playlists in your Spotify account!")
                
                self.authenticated = True
                return True
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                print("💡 Make sure you copied the complete redirect URL")
                return False
                
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return False
    
    def create_playlist_from_songs(self, playlist_name: str, description: str, songs: List[Dict]) -> Dict:
        """Create a Spotify playlist from AI-recommended songs."""
        if not self.authenticated:
            return {'success': False, 'error': 'Not authenticated with Spotify'}
            
        try:
            print(f"\n🎵 Creating playlist: '{playlist_name}'")
            
            # Get current user
            user = self.sp.current_user()
            user_id = user['id']
            
            # Create empty playlist
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                description=description,
                public=True
            )
            
            playlist_id = playlist['id']
            playlist_url = playlist['external_urls']['spotify']
            
            print(f"✅ Created empty playlist")
            print(f"🔗 Playlist URL: {playlist_url}")
            
            # Search for and add tracks
            track_uris = []
            found_count = 0
            not_found = []
            
            print(f"\n🔍 Finding {len(songs)} songs on Spotify...")
            
            for i, song in enumerate(songs, 1):
                song_name = song.get('name', '')
                artist_name = song.get('artist', song.get('artists', ''))
                
                print(f"  {i:2d}. {song_name} - {artist_name}", end="")
                
                # Search for the track
                track_uri = self._search_track(song_name, artist_name)
                
                if track_uri:
                    track_uris.append(track_uri)
                    found_count += 1
                    print(" ✅")
                else:
                    not_found.append(f"{song_name} - {artist_name}")
                    print(" ❌")
            
            # Add tracks to playlist in batches
            if track_uris:
                print(f"\n📥 Adding {len(track_uris)} songs to playlist...")
                
                # Spotify allows max 100 tracks per request
                batch_size = 100
                for i in range(0, len(track_uris), batch_size):
                    batch = track_uris[i:i + batch_size]
                    self.sp.playlist_add_items(playlist_id, batch)
                
                print(f"🎉 SUCCESS! Added {len(track_uris)} out of {len(songs)} songs!")
                
            else:
                print("❌ No songs were found on Spotify")
            
            return {
                'success': True,
                'playlist_id': playlist_id,
                'playlist_url': playlist_url,
                'playlist_name': playlist_name,
                'tracks_added': len(track_uris),
                'tracks_requested': len(songs),
                'success_rate': f"{len(track_uris)}/{len(songs)} ({100*len(track_uris)/len(songs):.1f}%)"
            }
            
        except Exception as e:
            print(f"❌ Error creating playlist: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_track(self, song_name: str, artist_name: str) -> Optional[str]:
        """Search for a track and return its URI."""
        try:
            # Clean artist name
            if isinstance(artist_name, str):
                artist_clean = re.sub(r"[\[\]']", "", artist_name)
                artist_clean = artist_clean.split(',')[0].strip()
            else:
                artist_clean = str(artist_name)
            
            # Try different search strategies
            search_queries = [
                f'track:"{song_name}" artist:"{artist_clean}"',
                f'"{song_name}" "{artist_clean}"',
                f'{song_name} {artist_clean}',
                song_name
            ]
            
            for query in search_queries:
                results = self.sp.search(q=query, type='track', limit=1)
                
                if results['tracks']['items']:
                    return results['tracks']['items'][0]['uri']
            
            return None
            
        except:
            return None


class MusicPlaylistApp:
    def __init__(self):
        """Initialize the complete music recommendation system."""
        self.cleaner = None
        self.recommender = None  
        self.playlist_creator = None
        self.spotify = None
        self.data_loaded = False
        
        # Spotify credentials - You need to set these up
        self.SPOTIFY_CLIENT_ID = "your_client_id_here"
        self.SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
        
        print("🎵 AI Music Recommendation System")
        print("=" * 50)

    def setup_spotify_credentials(self):
        """Interactive setup for Spotify credentials."""
        print("\n🔑 Spotify API Setup")
        print("To create playlists on Spotify, you need API credentials:")
        print("1. Go to: https://developer.spotify.com/dashboard")  
        print("2. Create an app")
        print("3. Copy your Client ID and Client Secret")
        print("4. Add this redirect URI in your app settings: http://127.0.0.1:8888/callback")
        
        client_id = input("\nEnter your Spotify Client ID (or press Enter to skip): ").strip()
        if client_id:
            client_secret = input("Enter your Spotify Client Secret: ").strip()
            if client_secret:
                self.SPOTIFY_CLIENT_ID = client_id
                self.SPOTIFY_CLIENT_SECRET = client_secret
                return True
        
        print("⚠️  Skipping Spotify integration. You can still create playlists locally.")
        return False

    def load_data(self):
        """Load and prepare music data."""
        print("\n📊 Loading music dataset...")
        
        try:
            # Load your music dataset
            df = pd.read_csv('tracks_added_languages.csv')
            print(f"✅ Loaded {len(df)} tracks")
            
            # Clean and scale data
            print("🧹 Cleaning data...")
            self.cleaner = DataCleaner()
            X, songs = self.cleaner.clean_data(df)
            X_scaled = self.cleaner.scale_features(X)
            
            print(f"✅ Cleaned data: {len(X_scaled)} tracks with {X_scaled.shape[1]} features")
            
            # Initialize recommender system
            print("🤖 Initializing AI recommender...")
            self.recommender = MusicRecommender(
                features_data=X_scaled,
                songs_data=songs,
                language_weight=0.2,
                artist_weight=0.1
            )
            
            # Initialize playlist creator
            self.playlist_creator = PlaylistCreator(self.recommender)
            
            self.data_loaded = True
            print("✅ System ready!")
            
        except FileNotFoundError:
            print("❌ Error: 'tracks_added_languages.csv' not found!")
            print("Please make sure your music dataset is in the current directory.")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
            
        return True

    def setup_spotify(self) -> bool:
        """Setup Spotify integration with WORKING authentication."""
        if self.SPOTIFY_CLIENT_ID == "your_client_id_here":
            if not self.setup_spotify_credentials():
                return False
        
        try:
            print("\n🎵 Connecting to Spotify...")
            
            # Use the WORKING integration class
            self.spotify = SimpleSpotifyIntegration(
                client_id=self.SPOTIFY_CLIENT_ID,
                client_secret=self.SPOTIFY_CLIENT_SECRET
            )
            
            # This will show the URL and ask for manual copy/paste
            return self.spotify.authenticate()
            
        except Exception as e:
            print(f"❌ Spotify setup failed: {e}")
            return False

    def get_user_input(self) -> Optional[str]:
        """Get playlist request from user."""
        print("\n🎤 Describe your ideal playlist!")
        print("Examples:")
        print("  • 'upbeat rap songs for workout'")
        print("  • 'chill indie rock for studying'") 
        print("  • 'romantic pop songs for date night'")
        print("  • 'energetic EDM for running'")
        print("  • 'sad acoustic songs for rainy days'")
        
        user_input = input("\n🎯 What kind of playlist do you want? ").strip()
        
        if not user_input:
            print("❌ Please provide a playlist description.")
            return None
            
        return user_input

    def create_ai_playlist(self, user_request: str, playlist_size: int = 50, use_llm_filter: bool = True) -> Optional[dict]:
        """Create playlist using AI recommendations."""
        if not self.data_loaded:
            print("❌ Data not loaded. Run setup first.")
            return None
            
        try:
            print(f"\n🤖 Creating AI playlist for: '{user_request}'")
            print("⏳ This may take a moment...")
            
            # Use your PlaylistCreator to generate recommendations
            playlist_data = self.playlist_creator.create_playlist_from_description(
                user_request=user_request,
                final_playlist_size=playlist_size,
                use_llm_filter=use_llm_filter
            )
            
            return playlist_data
            
        except Exception as e:
            print(f"❌ Error creating playlist: {e}")
            return None

    def create_spotify_playlist(self, playlist_data: dict, custom_name: str = None) -> bool:
        """Create the playlist on Spotify."""
        if not self.spotify or not self.spotify.authenticated:
            print("❌ Spotify not connected. Cannot create online playlist.")
            return False
            
        try:
            # Prepare playlist info
            name = custom_name or playlist_data['name']
            description = playlist_data['description']
            songs = playlist_data['songs']
            
            # Create playlist on Spotify
            result = self.spotify.create_playlist_from_songs(
                playlist_name=name,
                description=description, 
                songs=songs
            )
            
            return result['success']
            
        except Exception as e:
            print(f"❌ Error creating Spotify playlist: {e}")
            return False

    def display_playlist_preview(self, playlist_data: dict, limit: int = 10):
        """Display a preview of the generated playlist."""
        songs = playlist_data['songs']
        total_songs = len(songs)
        
        print(f"\n🎵 Generated Playlist Preview ({total_songs} songs total)")
        print("=" * 60)
        
        for i, song in enumerate(songs[:limit]):
            # Display the most relevant score available
            score = song.get('total_score', song.get('similarity_score', 0))
            seed_source = song.get('seed_source', 'Unknown')
            print(f"  {i+1:2d}. {song.get('name', 'Unknown Track')}")
            print(f"      by {song.get('artist', 'Unknown Artist')}")
            print(f"      (Score: {score:.3f} | Seed: {seed_source})")
            print()
            
        if total_songs > limit:
            print(f"  ... and {total_songs - limit} more songs")

    def save_playlist_locally(self, playlist_data: dict, filename: str = None):
        """Save playlist data to a local file."""
        if not filename:
            # Generate filename from playlist name
            safe_name = "".join(c for c in playlist_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name.replace(' ', '_')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Playlist saved locally as: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving playlist: {e}")
            return False

    def interactive_session(self):
        """Run interactive playlist creation session."""
        while True:
            print("\n" + "="*60)
            print("🎵 AI Music Playlist Creator")
            print("="*60)
            
            # Get user request
            user_request = self.get_user_input()
            if not user_request:
                continue
            
            # Ask for playlist size
            try:
                size_input = input(f"\n📏 How many songs? (default: 50): ").strip()
                playlist_size = int(size_input) if size_input else 50
                playlist_size = max(10, min(100, playlist_size))  # Limit between 10-100
            except:
                playlist_size = 50

            # Ask whether to use LLM filter
            use_llm_filter_input = input("\n🤖 Use LLM to filter recommendations? (y/n, default: y): ").strip().lower()
            use_llm_filter = use_llm_filter_input not in ['n', 'no']
            
            # Create AI playlist
            playlist_data = self.create_ai_playlist(user_request, playlist_size, use_llm_filter)
            if not playlist_data:
                continue
            
            # Show preview
            self.display_playlist_preview(playlist_data)
            
            # Ask what to do with the playlist
            print("\n🎯 What would you like to do?")
            print("  1. Create on Spotify")
            print("  2. Save locally only") 
            print("  3. Both")
            print("  4. Try again with different description")
            print("  5. Quit")
            
            choice = input("\nChoice (1-5): ").strip()
            
            if choice == '1' or choice == '3':
                # Create on Spotify
                custom_name = input("\n🎵 Custom playlist name (or press Enter for auto-generated): ").strip()
                success = self.create_spotify_playlist(playlist_data, custom_name or None)
                
            if choice == '2' or choice == '3':
                # Save locally
                self.save_playlist_locally(playlist_data)
            
            if choice == '4':
                continue  # Start over
            
            if choice == '5':
                break
            
            # Ask if they want to create another playlist
            another = input("\n🔄 Create another playlist? (y/n): ").strip().lower()
            if another not in ['y', 'yes']:
                break
        
        print("\n👋 Thanks for using AI Music Playlist Creator!")

    def run(self):
        """Run the complete application."""
        print("🚀 Starting AI Music Playlist Creator...")
        
        # Load music data
        if not self.load_data():
            return

        while True:
            print("\n" + "="*60)
            print("🎵 Main Menu")
            print("="*60)
            print("  1. Create AI Playlist")
            print("  2. Explore Song Recommendations")
            print("  3. Analyze Artist in Cluster")
            print("  4. Quit")
            choice = input("\nChoice (1-4): ").strip()

            if choice == '1':
                # Setup Spotify (optional)
                has_spotify = self.setup_spotify()
                if has_spotify:
                    print("✅ Ready to create playlists on Spotify!")
                else:
                    print("⚠️  Spotify not connected. You can still create playlists locally.")
                self.interactive_session()
            elif choice == '2':
                self.explore_recommendations_session()
            elif choice == '3':
                self.analyze_artist_in_cluster_session()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please enter a number from 1 to 4.")

        print("\n👋 Thanks for using the AI Music App!")

    def analyze_artist_in_cluster_session(self):
        """Runs a session to analyze songs by the same artist in the same cluster."""
        print("\n" + "="*60)
        print("ANALYZE ARTIST IN CLUSTER")
        print("="*60)

        while True:
            query = input("\n🔍 Enter a song title to search for (or type 'back' to return): ").strip()
            if query.lower() == 'back':
                break
            if len(query) < 3:
                print("❌ Please enter at least 3 characters.")
                continue

            matches = self.recommender.search_songs(query)
            if matches.empty:
                print(f"No songs found matching '{query}'.")
                continue

            print(f"\nFound {len(matches)} matches. Please choose one:")
            for i, (_, row) in enumerate(matches.head(10).iterrows()):
                print(f"  {i + 1:2d}. {row['name']} - {row['artists']}")
            
            try:
                choice_idx = int(input("\nChoice (number): ").strip()) - 1
                if not 0 <= choice_idx < len(matches.head(10)):
                    print("❌ Invalid choice.")
                    continue
                
                chosen_song_series = matches.iloc[choice_idx]
                seed_song = {
                    'title': chosen_song_series['name'],
                    'artist': chosen_song_series['artists']
                }

                print(f"\nAnalyzing cluster for other songs by the same artist as '{seed_song['title']}'...")
                artist_cluster_songs = self.recommender.get_artist_songs_in_cluster(seed_song)

                if artist_cluster_songs.empty:
                    print("No other songs by this artist were found in the same cluster.")
                    continue

                print("\n--- Same Artist, Same Cluster Analysis ---")
                for _, rec in artist_cluster_songs.iterrows():
                    print(f"  - {rec['name']} (Similarity: {rec['audio_similarity']:.4f})")

            except (ValueError, IndexError):
                print("❌ Invalid input. Please enter a number from the list.")
                continue

    def explore_recommendations_session(self):
        """Run an interactive session to explore song recommendations."""
        print("\n" + "="*60)
        print("EXPLORE SONG RECOMMENDATIONS")
        print("="*60)

        while True:
            query = input("\n🔍 Enter a song title to search for (or type 'back' to return to main menu): ").strip()
            if query.lower() == 'back':
                break
            if len(query) < 3:
                print("❌ Please enter at least 3 characters to search.")
                continue

            matches = self.recommender.search_songs(query)
            if matches.empty:
                print(f"No songs found matching '{query}'.")
                continue

            print(f"\nFound {len(matches)} matches. Please choose one:")
            for i, (_, row) in enumerate(matches.head(10).iterrows()):
                print(f"  {i + 1:2d}. {row['name']} - {row['artists']}")
            
            try:
                choice_idx = int(input("\nChoice (number): ").strip()) - 1
                if not 0 <= choice_idx < len(matches.head(10)):
                    print("❌ Invalid choice.")
                    continue
                
                chosen_song_series = matches.iloc[choice_idx]
                seed_song = {
                    'title': chosen_song_series['name'],
                    'artist': chosen_song_series['artists']
                }

                # Ask user whether to apply the Trust Score
                apply_trust_score_input = input("\n🧠 Apply Trust Score filtering? (y/n, default: y): ").strip().lower()
                use_trust_score = apply_trust_score_input not in ['n', 'no']

                print(f"\nFetching recommendations for '{seed_song['title']}' (Trust Score: {use_trust_score})...")
                recommendations = self.recommender.get_recommendations(
                    seed_song=seed_song, 
                    n_recommendations=10, 
                    use_trust_score=use_trust_score
                )

                if recommendations.empty:
                    print("Could not find any recommendations for this song.")
                    continue

                print(f"\n--- Top 10 Recommendations (Trust Score: {use_trust_score}) ---")
                for _, rec in recommendations.iterrows():
                    print(f"  - {rec['name']} by {rec['artists']} (Score: {rec['similarity_score']:.4f})")

            except (ValueError, IndexError):
                print("❌ Invalid input. Please enter a number from the list.")
                continue


def main():
    """Main application entry point."""
    app = MusicPlaylistApp()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
