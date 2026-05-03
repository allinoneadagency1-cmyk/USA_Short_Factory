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

def get_fresh_topic():
    print("\n🌍 Scraping Google for real-time trending news...")
    try:
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        tree = ET.parse(urllib.request.urlopen(req))
        trends = [item.text.split(" - ")[0] for item in tree.getroot().findall('./channel/item/title')]
        chosen_topic = random.choice(trends[:20])
        print(f"🎯 Locked Fresh Topic: {chosen_topic}")
        return chosen_topic
    except: pass
    return "The Hidden Secrets of World History"

def generate_master_script(topic):
    prompt = f"""
    You are a professional YouTube Shorts director specializing in cinematic storytelling. Write a gripping 150-word script about '{topic}'.
    
    RULES:
    1. FACTUAL ACCURACY: Only use verified facts. No exaggerations.
    2. VISUAL KEYWORDS: Provide a highly descriptive visual keyword for EACH scene (e.g., 'Photorealistic map of Iran', 'Cinematic lighting on Wall Street', 'Close up of a generic politician').
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Engaging Title under 60 chars",
            "description": "Engaging description with 3 hashtags",
            "tags": "exactly 15 comma-separated highly searched keywords"
        }},
        "scenes": [
            {{
                "text": "The spoken text...",
                "keyword": "highly descriptive visual prompt"
            }}
        ]
    }}
    Make exactly 10 scenes! Return ONLY valid JSON.
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
    print(f"🎨 Generating custom copyright-free AI image for: {prompt}")
    safe_prompt = urllib.parse.quote(f"Photorealistic vertical 9:16 highly detailed image of {prompt}, cinematic lighting, 8k resolution, documentary style")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(resp.content)
            return fpath, "image"
    except Exception as e:
        print(f"AI Image Gen failed: {e}")
    return None, None

def download_media(keyword, index):
    # Try Pexels first for real stock video
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        simple_keyword = keyword.split(" ")[0] # Use first word for stock video
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(simple_keyword)}&orientation=portrait&per_page=3"
        resp = requests.get(url, headers=headers, timeout=10).json()
        if resp.get('videos'):
            link = max(resp['videos'][0]['video_files'], key=lambda x: x.get('width', 0))['link']
            fpath = f"scene_{index}.mp4"
            with open(fpath, "wb") as f: f.write(requests.get(link).content)
            return fpath, "video"
    except: pass

    # ADVANCED UPGRADE: If no video is found, generate a 100% custom AI image
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
            print(f"⚠️ Safe Failsafe triggered for scene {i}.")
            c = ColorClip(size=(target_w, target_h), color=(20, 20, 20)).set_duration(dur_per_scene)
        elif m_type == "video":
            c = VideoFileClip(file).without_audio()
            c = smart_crop_to_tiktok(c)
            c = vfx_loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
        else:
            c = ImageClip(file)
            c = smart_crop_to_tiktok(c).set_duration(dur_per_scene)
            
        clips.append(c)

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    out_name = f"ADVANCED_SHORT_{int(time.time())}.mp4"
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
        "snippet": {"title": seo['title'], "description": seo['description'] + "\n\n#shorts #viral", "tags": tag_list[:15], "categoryId": "24"}, 
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
