import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET
from gtts import gTTS

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, ColorClip
from moviepy.video.fx.loop import loop as vfx_loop

import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def get_fresh_topic():
    print("\n🌍 Scraping Google for Viral News...")
    try:
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        tree = ET.parse(urllib.request.urlopen(req))
        trends = [item.text.split(" - ")[0] for item in tree.getroot().findall('./channel/item/title')]
        chosen_topic = random.choice(trends[:15]) # Tighter focus on top news
        print(f"🎯 Locked Viral Topic: {chosen_topic}")
        return chosen_topic
    except: pass
    return "Shocking Secrets of the Billionaire Mindset"

def generate_master_script(topic):
    # 🚨 VIRAL PROMPT: Forces high-retention hooks and fast pacing
    prompt = f"""
    You are a viral YouTube Shorts scriptwriter. Write a fast-paced, highly controversial or shocking 150-word script about '{topic}'.
    
    RULES TO GO VIRAL:
    1. THE HOOK: The first sentence MUST be a shocking statement or question that makes people stop scrolling instantly.
    2. RETENTION: Build intense curiosity. Use short, punchy sentences.
    3. KEYWORDS: Provide ONE simple, highly generic noun (e.g., 'city', 'police', 'money', 'crowd', 'fire') for the visual keyword of each scene.
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Insane Clickbait Title under 60 chars",
            "description": "Engaging description with 3 hashtags",
            "tags": "exactly 15 comma-separated highly searched keywords"
        }},
        "scenes": [
            {{
                "text": "The spoken text...",
                "keyword": "generic single word"
            }}
        ]
    }}
    Make exactly 10 to 12 scenes! Return ONLY valid JSON.
    """
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}", "Content-Type": "application/json"}
    
    try:
        models_resp = requests.get("https://openrouter.ai/api/v1/models").json()
        free_models = [m['id'] for m in models_resp.get('data', []) if str(m['id']).endswith(':free')][:3]
        if not free_models: free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]
    except: free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]

    url = "https://openrouter.ai/api/v1/chat/completions"
    for model in free_models:
        payload = {"model": model, "messages": [{"role": "system", "content": "You output strict JSON."}, {"role": "user", "content": prompt}]}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                clean_json = response.json()['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except: pass
    exit()

def generate_voice(scenes):
    full_script = " ".join([scene['text'] for scene in scenes])
    tts = gTTS(text=full_script, lang='en', tld='co.uk')
    tts.save("voice.mp3")
    return "voice.mp3"

def generate_ai_image(prompt, index):
    print(f"🎨 Generating unique AI Image for: {prompt}")
    safe_prompt = urllib.parse.quote(f"Ultra realistic vertical 9:16 cinematic image of {prompt}, dramatic lighting, 8k")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(resp.content)
            return fpath, "image"
    except: pass
    return None, None

def download_media(keyword, index):
    simple_kw = urllib.parse.quote(keyword.split(" ")[0])
    
    # 1. PIXABAY (Deep Randomization)
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=vertical&per_page=15"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) # Pick a random video from the top 15
                link = video['videos']['medium']['url']
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath, "video"
    except: pass

    # 2. PEXELS (Deep Randomization)
    try:
        if PEXELS_API_KEY:
            headers = {"Authorization": PEXELS_API_KEY}
            url = f"https://api.pexels.com/videos/search?query={simple_kw}&orientation=portrait&per_page=15"
            resp = requests.get(url, headers=headers, timeout=10).json()
            if resp.get('videos'):
                video = random.choice(resp['videos']) # Pick a random video from the top 15
                link = max(video['video_files'], key=lambda x: x.get('width', 0))['link']
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath, "video"
    except: pass

    # 3. AI IMAGE FALLBACK
    return generate_ai_image(keyword, index)

def smart_crop_to_tiktok(clip, target_w=1080, target_h=1920):
    clip_ratio = clip.w / clip.h
    if clip_ratio > (target_w / target_h):
        return clip.resize(height=target_h).crop(x_center=clip.w/2, width=target_w)
    else:
        return clip.resize(width=target_w).crop(y_center=clip.h/2, height=target_h)

def edit_short(audio_file, scenes, target_w=1080, target_h=1920):
    audio = AudioFileClip(audio_file)
    dur_per_scene = audio.duration / len(scenes)
    clips = []
    
    for i, scene in enumerate(scenes):
        file, m_type = download_media(scene['keyword'], i)
        
        if not file: 
            c = ColorClip(size=(target_w, target_h), color=(30, 30, 30)).set_duration(dur_per_scene)
        elif m_type == "video":
            c = VideoFileClip(file).without_audio()
            c = smart_crop_to_tiktok(c)
            c = vfx_loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
        else:
            c = ImageClip(file)
            c = smart_crop_to_tiktok(c).set_duration(dur_per_scene)
            
        clips.append(c)

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    out_name = f"VIRAL_SHORT_{int(time.time())}.mp4"
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
    audio.close(); final_video.close()
    return out_name

def upload_to_youtube(video_file, seo):
    if not os.path.exists("token.json"): return False
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = Credentials.from_authorized_user_file("token.json", scopes)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    tag_list = [t.strip() for t in seo['tags'].split(',')]
    
    body = {
        "snippet": {"title": seo['title'], "description": seo['description'] + "\n\n#shorts #viral #news", "tags": tag_list[:15], "categoryId": "25"}, 
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    try:
        youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)).execute()
        return True
    except: return False

def main():
    topic = get_fresh_topic()
    script_data = generate_master_script(topic)
    voice_file = generate_voice(script_data['scenes'])
    final_video = edit_short(voice_file, script_data['scenes'])
    upload_to_youtube(final_video, script_data['seo'])

if __name__ == "__main__":
    main()
