from googleapiclient.discovery import build
import pandas as pd

# =========================================
# YOUTUBE API CONFIG
# =========================================

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

print("API Connected Successfully")

# =========================================
# SEARCH FOR RAJ SHAMANI CHANNEL
# =========================================

search_response = youtube.search().list(
    part="snippet",
    q="Raj Shamani",
    type="channel",
    maxResults=1
).execute()

print("Channel Search Completed")

# Extract channel ID
channel_id = search_response["items"][0]["id"]["channelId"]

print("Channel ID:", channel_id)

# =========================================
# GET UPLOADS PLAYLIST
# =========================================

channel_response = youtube.channels().list(
    part="contentDetails",
    id=channel_id
).execute()

uploads_playlist_id = (
    channel_response["items"][0]
    ["contentDetails"]
    ["relatedPlaylists"]
    ["uploads"]
)

print("Uploads Playlist Found")

# =========================================
# FETCH LONG-FORM VIDEOS
# =========================================

videos = []
next_page_token = None

while True:

    playlist_response = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=50,
        pageToken=next_page_token
    ).execute()

    for item in playlist_response["items"]:

        video_id = item["snippet"]["resourceId"]["videoId"]

        # ---------------------------------
        # GET VIDEO DETAILS
        # ---------------------------------

        video_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()

        if not video_response["items"]:
            continue

        video_data = video_response["items"][0]

        snippet = video_data["snippet"]
        statistics = video_data.get("statistics", {})
        content_details = video_data["contentDetails"]

        # ---------------------------------
        # VIDEO DURATION
        # ---------------------------------

        duration = content_details.get("duration")

        # ---------------------------------
        # CONVERT DURATION TO MINUTES
        # ---------------------------------

        total_minutes = 0

        # Extract hours
        if "H" in duration:
            hours = int(
                duration.split("H")[0].replace("PT", "")
            )
            total_minutes += hours * 60

        # Extract minutes
        if "M" in duration:

            if "H" in duration:
                minutes_part = duration.split("H")[1]
            else:
                minutes_part = duration.replace("PT", "")

            minutes = int(minutes_part.split("M")[0])

            total_minutes += minutes

        # ---------------------------------
        # SKIP SHORT VIDEOS (<10 MIN)
        # ---------------------------------

        if total_minutes < 10:
            continue

        # ---------------------------------
        # STORE DATA
        # ---------------------------------

        videos.append({

            "video_id": video_id,

            "title": snippet.get("title"),

            "published_at": snippet.get("publishedAt"),

            "views": statistics.get("viewCount"),

            "likes": statistics.get("likeCount"),

            "comments": statistics.get("commentCount"),

            "duration": duration,

            "duration_minutes": total_minutes,

            "video_url":
                f"https://www.youtube.com/watch?v={video_id}"

        })

        print(f"Collected: {snippet.get('title')}")

    next_page_token = playlist_response.get("nextPageToken")

    if not next_page_token:
        break

# =========================================
# CREATE DATAFRAME
# =========================================

df = pd.DataFrame(videos)

# =========================================
# SAVE TO EXCEL
# =========================================

output_file = "raj_shamani_longform_videos.xlsx"

df.to_excel(output_file, index=False)

print("\n====================================")
print("DATA EXTRACTION COMPLETED")
print(f"Total Long Videos Saved: {len(df)}")
print(f"Excel File: {output_file}")
print("====================================")