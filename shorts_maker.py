import os
import time
import requests
import json
import sqlite3
import urllib.parse
import xml.etree.ElementTree as ET
from gtts import gTTS

# Notice we completely deleted TextClip, CompositeVideoClip, and SubtitlesClip!
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

# --- YOUTUBE UPLOADER IMPORTS ---
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# =====================================================================
# 🔑 API KEYS & SYSTEM CONFIG
# =====================================================================
OPENROUTER_API_KEY = "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"
PEXELS_API_KEY = "OgTzfDdHD8UePxkviAu10qCJ6uCFSsU1PdoBkvQE1iCgNhus11onSxKL"
PIXABAY_API_KEY = "55560146-b9b019f9e8fe327f589b6b754"
# =====================================================================

def init_db():
    conn = sqlite3.connect('shorts_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (topic TEXT UNIQUE)''')
    conn.commit()
    return conn

def is_topic_used(conn, topic):
    c = conn.cursor()
    c.execute("SELECT 1 FROM history WHERE topic=?", (topic,))
    return c.fetchone() is not None

def mark_topic_used(conn, topic):
    c = conn.cursor()
    c.execute("INSERT INTO history (topic) VALUES (?)", (topic,))
    conn.commit()

def get_fresh_topic(conn):
    print("\n🌍 Scraping Google for real-time viral topics...")
    try:
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        tree = ET.parse(urllib.request.urlopen(req))
        trends = [item.text.split(" - ")[0] for item in tree.getroot().findall('./channel/item/title')]
        for topic in trends:
            if not is_topic_used(conn, topic):
                print(f"🎯 Locked Fresh Topic: {topic}")
                return topic
    except: pass
    return "The Hidden Secrets of World History"

def generate_master_script(topic):
    print(f"\n🧠 AI is writing a 45-60 second script for: {topic}")
    
    prompt = f"""
    You are a viral YouTube Shorts director. Write a highly detailed, engaging 150-word script about '{topic}'.
    It is CRITICAL that the script is at least 150 words long to ensure a 45-60 second video. 
    I need the output in strict JSON format.
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Viral Clickbait Title under 60 chars",
            "description": "Engaging description with 3 hashtags",
            "tags": "exactly 15 comma-separated highly searched keywords"
        }},
        "scenes": [
            {{
                "text": "The spoken text for this scene (make it long and descriptive)",
                "keyword": "One simple word to search on Pexels (e.g., 'money', 'king', 'space')"
            }}
        ]
    }}
    Make exactly 10 to 12 scenes!
    Return ONLY valid JSON. No markdown formatting.
    """
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "AutoShorts"
    }
    
    print("   📡 Scanning OpenRouter database for active servers...")
    try:
        models_resp = requests.get("https://openrouter.ai/api/v1/models").json()
        free_models = [m['id'] for m in models_resp.get('data', []) if str(m['id']).endswith(':free')][:3]
        if not free_models: free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]
    except:
        free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]

    url = "https://openrouter.ai/api/v1/chat/completions"
    for model in free_models:
        print(f"   -> Requesting script from: {model}...")
        payload = {"model": model, "messages": [{"role": "system", "content": "You output strict JSON."}, {"role": "user", "content": prompt}]}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                print("   ✅ Success! Script generated.")
                clean_json = response.json()['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except: pass
            
    print("\n❌ CRITICAL ERROR: All live models failed.")
    exit()

def generate_voice(scenes):
    print("\n🎤 Generating Premium British Voiceover (No Captions)...")
    full_script = " ".join([scene['text'] for scene in scenes])
    
    # Using the UK domain for that high-quality documentary accent
    tts = gTTS(text=full_script, lang='en', tld='co.uk')
    tts.save("voice.mp3")
            
    return "voice.mp3"

def download_media(keyword, index):
    print(f"   🔍 Hunting HD Media for '{keyword}'...")
    headers = {"Authorization": PEXELS_API_KEY}
    
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(keyword)}&orientation=portrait&per_page=3"
    try:
        resp = requests.get(url, headers=headers).json()
        if resp.get('videos'):
            link = max(resp['videos'][0]['video_files'], key=lambda x: x.get('width', 0))['link']
            fpath = f"scene_{index}.mp4"
            with open(fpath, "wb") as f: f.write(requests.get(link).content)
            return fpath, "video"
    except: pass

    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keyword)}&orientation=portrait&per_page=1"
    try:
        resp = requests.get(url, headers=headers).json()
        if resp.get('photos'):
            link = resp['photos'][0]['src']['original']
            fpath = f"scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(requests.get(link).content)
            return fpath, "image"
    except: pass
    
    return None, None

def smart_crop_to_tiktok(clip, target_w=1080, target_h=1920):
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h
    
    if clip_ratio > target_ratio:
        resized_clip = clip.resize(height=target_h)
        return resized_clip.crop(x_center=resized_clip.w/2, width=target_w)
    else:
        resized_clip = clip.resize(width=target_w)
        return resized_clip.crop(y_center=resized_clip.h/2, height=target_h)

def edit_short(audio_file, scenes, target_w=1080, target_h=1920):
    print("\n🎬 Advanced Editor is stitching the Clean Short...")
    audio = AudioFileClip(audio_file)
    total_dur = audio.duration
    
    clips = []
    dur_per_scene = total_dur / len(scenes)
    
    for i, scene in enumerate(scenes):
        file, m_type = download_media(scene['keyword'], i)
        if not file: continue
            
        if m_type == "video":
            c = VideoFileClip(file).without_audio()
            c = smart_crop_to_tiktok(c)
            if c.duration < dur_per_scene: c = vfx.loop(c, duration=dur_per_scene)
            else: c = c.subclip(0, dur_per_scene)
        else:
            c = ImageClip(file)
            c = smart_crop_to_tiktok(c).set_duration(dur_per_scene)
            
        # CPU-SAFE MOTION: Cinematic Fade-In
        c = c.fx(vfx.fadein, 0.3)
        clips.append(c)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio)
    
    out_name = f"CLEAN_SHORT_{int(time.time())}.mp4"
    print(f"💾 Exporting Cinematic 1080x1920 Short: {out_name}...")
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
    
    audio.close(); final_video.close()
    for i in range(len(scenes)):
        try: os.remove(f"scene_{i}.mp4")
        except: pass
        try: os.remove(f"scene_{i}.jpg")
        except: pass
        
    return out_name

def upload_to_youtube(video_file, seo):
    print(f"\n🚀 Connecting to YouTube API...")
    if not os.path.exists("client_secrets.json"): return False
        
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = Credentials.from_authorized_user_file("token.json", scopes) if os.path.exists("token.json") else None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file("client_secrets.json", scopes)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token: token.write(creds.to_json())

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    tag_list = [t.strip() for t in seo['tags'].split(',')]
    
    body = {
        "snippet": {"title": seo['title'], "description": seo['description'] + "\n\n#shorts #viral", "tags": tag_list[:15], "categoryId": "24"}, 
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    }
    
    try:
        print(f"📤 Uploading {video_file}...")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True))
        response = request.execute()
        print(f"✅ SUCCESSFULLY UPLOADED! Link: https://youtube.com/shorts/{response.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return False

def main():
    print("="*50 + "\n🚀 V21.6 FULL-AUTO SHORTS FACTORY (CLEAN VISUALS EDITION)\n" + "="*50)
    db_conn = init_db()
    topic = get_fresh_topic(db_conn)
    script_data = generate_master_script(topic)
    print(f"✅ AI Script Generated! ({len(script_data['scenes'])} scenes)")
    
    voice_file = generate_voice(script_data['scenes'])
    final_video = edit_short(voice_file, script_data['scenes'])
    
    print("\n" + "="*50)
    print(f"🎬 SHORT PRODUCTION COMPLETE: {final_video}")
    print(f"📌 TITLE: {script_data['seo']['title']}")
    print("="*50)
    
    choice = input("\n👉 Do you want to upload this to YouTube right now? (y/n): ").lower()
    if choice == 'y':
        if upload_to_youtube(final_video, script_data['seo']):
            mark_topic_used(db_conn, topic)
            print("✅ Topic marked as used in database.")
    else:
        mark_topic_used(db_conn, topic)
        print(f"🔒 Video saved locally.")

if __name__ == "__main__":
    main()