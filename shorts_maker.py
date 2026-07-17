import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET
import re

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip, concatenate_audioclips, concatenate_videoclips
import moviepy.video.fx.all as vfx
from moviepy.audio.fx.volumex import volumex as afx_volumex

import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def get_fresh_topic():
    print("\n🌍 Scraping for High-Stakes Finance Topics...")
    backup_topics = [
        "The 2026 Housing Market Crash Nobody Sees Coming",
        "How Banks Secretly Steal Your Wealth Everyday",
        "The Middle Class Trap: Why You Are Kept Poor",
        "The Truth About BlackRock Buying Every Single Home"
    ]
    try:
        url = 'https://finance.yahoo.com/news/rssindex'
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            tree = ET.fromstring(resp.content)
            trends = [item.text for item in tree.findall('./channel/item/title')]
            if trends: return random.choice(trends[:5])
    except: pass
    return random.choice(backup_topics)

def extract_json(raw_text):
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    return None

def is_valid_script(script_json):
    if script_json and isinstance(script_json, dict):
        scenes = script_json.get("scenes", [])
        if len(scenes) > 3: return True
    return False

def generate_master_script(topic):
    prompt = f"""
    You are a viral YouTube Shorts producer for a Finance Channel. Write a fast-paced, highly controversial 150-word script about '{topic}'.
    
    RULES:
    1. THE HOOK: The first 3 seconds MUST provoke fear, greed, or intense curiosity. 
    2. PACING: Short, punchy phrases. No boring explanations.
    3. VISUALS: Provide a 2-word highly specific cinematic keyword for each scene.
    4. CHUNKED TEXT: Break the 'text' into very small 3-4 word chunks so they flash quickly on screen.
    
    Return ONLY valid JSON matching this exact structure:
    {{
        "seo": {{"title": "Insane Clickbait Title | #shorts", "description": "Engaging description...", "tags": "finance, money, wealth, investing"}},
        "bgm_keyword": "phonk drift",
        "scenes": [
            {{"text": "The banks are lying.", "keyword": "bank vault"}}
        ]
    }}
    Make EXACTLY 16 fast-paced scenes! No emojis. Return ONLY valid JSON block.
    """
    
    print("🧠 Attempting Brain 1 (OpenRouter)...")
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip() if OPENROUTER_API_KEY else ''}", "Content-Type": "application/json"}
    try:
        payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            script_json = extract_json(response.json()['choices'][0]['message']['content'])
            if is_valid_script(script_json): return script_json
    except Exception as e:
        print(f"⚠️ Brain 1 Failed: {e}")

    print("🚀 Brain 1 Busy. Routing to Brain 2 (Free Dynamic AI)...")
    try:
        safe_prompt = urllib.parse.quote(f"Respond strictly in JSON format. {prompt}")
        url = f"https://text.pollinations.ai/prompt/{safe_prompt}?model=openai"
        response = requests.get(url, timeout=40)
        if response.status_code == 200:
            script_json = extract_json(response.text)
            if is_valid_script(script_json): return script_json
    except: pass

    print("⚠️ ALL AI NETWORKS DOWN. Using Emergency Local Script.")
    return {
        "seo": {"title": "The Middle Class Trap Exposed 🚨 | #shorts", "description": "Why you are working harder but getting poorer.", "tags": "finance, money, wealth"},
        "bgm_keyword": "phonk aggressive",
        "scenes": [
            {"text": "The middle class", "keyword": "suburb house"}, {"text": "is a trap.", "keyword": "mouse trap"},
            {"text": "While you work", "keyword": "office worker"}, {"text": "for a salary,", "keyword": "money counting"},
            {"text": "the top 1%", "keyword": "mansion pool"}, {"text": "are buying assets.", "keyword": "gold bars"},
            {"text": "They use debt", "keyword": "credit card"}, {"text": "to pay zero taxes.", "keyword": "tax form"},
            {"text": "And inflation?", "keyword": "grocery store"}, {"text": "It silently pays off", "keyword": "bank vault"},
            {"text": "their massive loans.", "keyword": "signing document"}, {"text": "Wake up.", "keyword": "eyes opening"},
            {"text": "Stop saving cash.", "keyword": "burning money"}, {"text": "Start buying assets.", "keyword": "real estate"},
            {"text": "Before it's", "keyword": "clock ticking"}, {"text": "too late.", "keyword": "dark storm"}
        ]
    }

def download_bgm(keyword):
    if not keyword: keyword = "phonk aggressive"
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/audio/?key={PIXABAY_API_KEY}&q={urllib.parse.quote(str(keyword))}"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                fpath = "bgm.mp3"
                with open(fpath, "wb") as f: f.write(requests.get(resp['hits'][0]['audio_download']).content)
                return fpath
    except: pass
    return None

def generate_ai_image(prompt, index):
    # 🚨 V6 UPGRADE: Using FLUX for hyper-realistic 9:16 vertical shorts images
    safe_prompt = urllib.parse.quote(f"Cinematic masterpiece, 8k resolution, highly detailed, dramatic lighting, vertical 9:16, {prompt}")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&model=flux"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(resp.content)
            return fpath, "image"
    except: pass
    return None, None

def download_media(keyword, index):
    # 🚨 V6 UPGRADE: Randomized Pages to stop repeating the exact same videos
    simple_kw = urllib.parse.quote(f"{str(keyword)} 4k cinematic")
    random_page = random.randint(1, 3) 
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=vertical&min_width=1080&page={random_page}&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(video['videos']['large']['url']).content)
                return fpath, "video"
    except: pass
    return generate_ai_image(keyword, index)

# 🚨 THE MERCILESS 9:16 ENFORCER 🚨
def force_9_16_portrait(clip, target_w=1080, target_h=1920):
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h
    
    if clip_ratio > target_ratio:
        # Too wide -> match height, crop sides
        resized = clip.resize(height=target_h)
        return resized.crop(x_center=resized.w/2, width=target_w)
    else:
        # Too tall -> match width, crop top/bottom
        resized = clip.resize(width=target_w)
        return resized.crop(y_center=resized.h/2, height=target_h)

def add_ken_burns_effect(clip, zoom_ratio=0.04):
    def zoom_in(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        zoom_factor = 1 + (t / clip.duration) * zoom_ratio
        new_w, new_h = int(w / zoom_factor), int(h / zoom_factor)
        x_center, y_center = w / 2, h / 2
        cropped = frame[int(y_center - new_h/2):int(y_center + new_h/2), int(x_center - new_w/2):int(x_center + new_w/2)]
        import numpy as np
        from PIL import Image
        return np.array(Image.fromarray(cropped).resize((w, h), Image.Resampling.LANCZOS))
    return clip.fl(zoom_in)

def create_subtitle_clip(text, duration, target_w, target_h):
    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip().upper()
    if len(clean_text) < 1: return None
    try:
        # 🚨 V6 UPGRADE: Larger font, thicker stroke, moved to lower-middle of screen (0.7)
        txt_clip = TextClip(clean_text, fontsize=110, color='#FFFF00', stroke_color='black', stroke_width=8, method='caption', size=(target_w - 100, None))
        if txt_clip.get_frame(0).size == 0: return None
        return txt_clip.set_position(('center', 0.7), relative=True).set_duration(duration)
    except: return None

def build_v6_viral_short(scenes, bgm_keyword, target_w=1080, target_h=1920):
    print("🎬 Initializing V6 Hyper-Viral Engine (Strict 9:16 | Perfect Sync)...")
    clips = []
    
    for i, scene in enumerate(scenes):
        scene_text = scene.get('text', '').strip()
        scene_kw = scene.get('keyword', 'abstract')
        if len(scene_text) < 2: continue
        
        # Audio Sync Generation
        txt_file = f"temp_scene_{i}.txt"
        audio_file = f"scene_{i}.mp3"
        with open(txt_file, "w", encoding="utf-8") as f: f.write(scene_text)
        
        os.system(f'edge-tts --voice "en-US-GuyNeural" --rate=+10% -f {txt_file} --write-media {audio_file}')
        
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 500:
            from gtts import gTTS
            gTTS(text=scene_text, lang='en', tld='us').save(audio_file)
            
        scene_audio = AudioFileClip(audio_file)
        exact_duration = scene_audio.duration
        
        # Get Media & Merciless Crop
        file, m_type = download_media(scene_kw, i)
        try:
            if m_type == "video" and file:
                c = VideoFileClip(file).without_audio()
                c = force_9_16_portrait(c, target_w, target_h)
                c = vfx.loop(c, duration=exact_duration) if c.duration < exact_duration else c.subclip(0, exact_duration)
            elif m_type == "image" and file:
                c = ImageClip(file).set_duration(exact_duration)
                c = force_9_16_portrait(c, target_w, target_h)
                c = add_ken_burns_effect(c)
            else:
                c = ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(exact_duration)
                
            sub_clip = create_subtitle_clip(scene_text, exact_duration, target_w, target_h)
            if sub_clip: c = CompositeVideoClip([c, sub_clip])
            
            c = c.set_audio(scene_audio)
            clips.append(c)
            
        except Exception as e:
            print(f"Skipping scene {i} error: {e}")

    final_video = concatenate_videoclips(clips, method="compose")
    
    bgm_file = download_bgm(bgm_keyword)
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.08)
            if bgm.duration < final_video.duration:
                bgm = concatenate_audioclips([bgm] * (int(final_video.duration / bgm.duration) + 1))
            bgm = bgm.subclip(0, final_video.duration)
            final_audio = CompositeAudioClip([final_video.audio, bgm])
            final_video = final_video.set_audio(final_audio)
        except: pass

    out_name = f"V6_VIRAL_SHORT_{int(time.time())}.mp4"
    # Using high bitrate cinematic settings
    final_video.write_videofile(out_name, fps=30, codec="libx264", preset="fast", bitrate="8000k", audio_codec="aac", logger=None)
    final_video.close()
    return out_name

def upload_to_youtube(video_file, seo):
    if not os.path.exists("token.json"): return False
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = Credentials.from_authorized_user_file("token.json", scopes)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    tag_list = [t.strip() for t in seo.get('tags', '').split(',')]
    
    body = {
        "snippet": {"title": seo.get('title', 'Deep Dive'), "description": seo.get('description', ''), "tags": tag_list[:20], "categoryId": "25"}, 
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    try:
        youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)).execute()
        return True
    except: return False

def main():
    topic = get_fresh_topic()
    script_data = generate_master_script(topic)
    
    if not script_data or not isinstance(script_data, dict): return
        
    final_video = build_v6_viral_short(script_data.get('scenes', []), script_data.get('bgm_keyword', 'phonk'))
    upload_to_youtube(final_video, script_data.get('seo', {}))

if __name__ == "__main__":
    main()
