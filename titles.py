import os
import csv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def get_channel_id(youtube, channel_name):
    try:
        request = youtube.search().list(part="id", type="channel", q=channel_name, maxResults=1)
        response = request.execute()
        if "items" in response and response["items"]:
            return response["items"][0]["id"]["channelId"]
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_channel_videos_and_playlists(youtube, channel_id):
    videos = []
    
    # Get all playlists for the channel
    playlists = []
    next_page_token = None
    while True:
        playlists_request = youtube.playlists().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        playlists_response = playlists_request.execute()
        playlists.extend(playlists_response.get('items', []))
        next_page_token = playlists_response.get('nextPageToken')
        if not next_page_token:
            break
    
    # Get videos from each playlist
    for playlist in playlists:
        playlist_id = playlist['id']
        playlist_title = playlist['snippet']['title']
        
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append({
                    'title': item['snippet']['title'],
                    'playlist': playlist_title,
                    'url': video_url
                })
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
    
    return videos

def main():
    youtube = get_authenticated_service()
    channel_name = "NeetCode"  # You can change this to any channel name
    channel_id = get_channel_id(youtube, channel_name)
    
    if channel_id:
        print(f"Channel ID: {channel_id}")
        videos = get_channel_videos_and_playlists(youtube, channel_id)
        
        # Write to CSV
        csv_filename = f"{channel_name}_videos.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Video Title', 'Playlist', 'Video URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for video in videos:
                writer.writerow({
                    'Video Title': video['title'],
                    'Playlist': video['playlist'],
                    'Video URL': video['url']
                })
        
        print(f"CSV file '{csv_filename}' has been created with {len(videos)} videos.")
    else:
        print("Could not find the channel. Please check the channel name.")

if __name__ == '__main__':
    main()