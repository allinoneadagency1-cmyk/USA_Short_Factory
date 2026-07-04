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
        if match:
            return json.loads(match.group(0))
    except: pass
    return None

def is_valid_script(script_json):
    if script_json and isinstance(script_json, dict):
        scenes = script_json.get("scenes", [])
        if len(scenes) > 3: return True
    return False

def generate_master_script(topic):
    # 🚨 V4 PODCAST FORMAT: Highly viral, conversational, conspiracy-style hooks
    prompt = f"""
    You are a viral YouTube Shorts producer. Write a 150-word script about '{topic}' formatted like a leaked, high-stakes podcast interview.
    
    RULES:
    1. THE HOOK: Start with a mind-blowing realization. (e.g., "Nobody realizes that...")
    2. PACING: Short, conversational, hard-hitting sentences. 
    3. VISUALS: Provide a 2-word cinematic keyword for each scene.
    4. TEXT CHUNKS: Break the spoken text into exactly 1 short sentence per scene so the screen changes constantly.
    
    Return ONLY valid JSON:
    {{
        "seo": {{
            "title": "They are hiding this from you... 🚨 #shorts",
            "description": "The truth about wealth. #finance #money",
            "tags": "finance, money, podcast, truth, wealth"
        }},
        "bgm_keyword": "suspense dark",
        "scenes": [
            {{"text": "Nobody realizes what the banks are actually doing.", "keyword": "bank vault"}},
            {{"text": "They take your money, pay you nothing,", "keyword": "money printing"}},
            {{"text": "and lend it out at 20% interest.", "keyword": "credit card"}}
        ]
    }}
    Make EXACTLY 10 scenes! No emojis. Return ONLY JSON.
    """
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip() if OPENROUTER_API_KEY else ''}", "Content-Type": "application/json"}
    try:
        payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            script_json = extract_json(response.json()['choices'][0]['message']['content'])
            if is_valid_script(script_json): return script_json
    except: pass

    print("🚀 Routing to Brain 2 (Free Dynamic AI)...")
    try:
        safe_prompt = urllib.parse.quote(f"Respond strictly in JSON format. {prompt}")
        url = f"https://text.pollinations.ai/prompt/{safe_prompt}?model=openai"
        response = requests.get(url, timeout=40)
        if response.status_code == 200:
            script_json = extract_json(response.text)
            if is_valid_script(script_json): return script_json
    except: pass

    return {
        "seo": {"title": "The Middle Class Trap Exposed 🚨 | #shorts", "description": "Why you are working harder but getting poorer.", "tags": "finance, money, wealth, investing, crash"},
        "bgm_keyword": "suspense dark",
        "scenes": [
            {"text": "Here is the biggest lie you've ever been told.", "keyword": "suburb house"},
            {"text": "You were told to save your money in a bank.", "keyword": "bank vault"},
            {"text": "But while your money sits there losing value to inflation,", "keyword": "burning money"},
            {"text": "the banks are using it to buy up real assets.", "keyword": "gold bars"},
            {"text": "They use debt to pay zero taxes.", "keyword": "tax form"},
            {"text": "And you are the one footing the bill.", "keyword": "tired worker"},
            {"text": "The entire system is designed to keep you renting.", "keyword": "apartment building"},
            {"text": "Stop saving cash. Start buying assets.", "keyword": "real estate"},
            {"text": "Before the middle class completely disappears.", "keyword": "dark storm"}
        ]
    }

def download_bgm(keyword):
    if not keyword: keyword = "suspense dark"
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
    # 🚨 V4 VISUALS: Utilizing the high-end FLUX model for ultra-realism
    safe_prompt = urllib.parse.quote(f"Photorealistic, cinematic lighting, 8k resolution, documentary footage style, vertical 9:16, {prompt}")
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
    simple_kw = urllib.parse.quote(f"{str(keyword)} 4k cinematic")
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=vertical&min_width=1080&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(video['videos']['large']['url']).content)
                return fpath, "video"
    except: pass
    return generate_ai_image(keyword, index)

def smart_crop_to_tiktok(clip, target_w=1080, target_h=1920):
    clip_ratio = clip.w / clip.h
    if clip_ratio > (target_w / target_h):
        return clip.resize(height=target_h).crop(x_center=clip.w/2, width=target_w)
    else:
        return clip.resize(width=target_w).crop(y_center=clip.h/2, height=target_h)

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
        txt_clip = TextClip(clean_text, fontsize=90, color='white', stroke_color='black', stroke_width=5, method='caption', size=(target_w - 150, None))
        if txt_clip.get_frame(0).size == 0: return None
        return txt_clip.set_position(('center', 'center')).set_duration(duration)
    except: return None

def build_v4_studio_video(scenes, bgm_keyword, target_w=1080, target_h=1920):
    print("🎬 Initializing V4 Studio Engine (Perfect Sync)...")
    clips = []
    
    # 🚨 V4 PERFECT SYNC ENGINE: Generate audio scene-by-scene, locking exact durations
    for i, scene in enumerate(scenes):
        scene_text = scene.get('text', '').strip()
        scene_kw = scene.get('keyword', 'abstract')
        if len(scene_text) < 2: continue
        
        # 1. Generate exact audio for this specific scene
        txt_file = f"temp_scene_{i}.txt"
        audio_file = f"scene_{i}.mp3"
        with open(txt_file, "w", encoding="utf-8") as f: f.write(scene_text)
        
        os.system(f'edge-tts --voice "en-US-ChristopherNeural" --rate=+5% -f {txt_file} --write-media {audio_file}')
        
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 500:
            from gtts import gTTS
            gTTS(text=scene_text, lang='en', tld='us').save(audio_file)
            
        scene_audio = AudioFileClip(audio_file)
        exact_duration = scene_audio.duration
        
        # 2. Get Media and lock it exactly to the audio duration
        file, m_type = download_media(scene_kw, i)
        try:
            if m_type == "video" and file:
                c = VideoFileClip(file).without_audio()
                c = smart_crop_to_tiktok(c)
                c = vfx.loop(c, duration=exact_duration) if c.duration < exact_duration else c.subclip(0, exact_duration)
            elif m_type == "image" and file:
                c = ImageClip(file).set_duration(exact_duration)
                c = smart_crop_to_tiktok(c)
                c = add_ken_burns_effect(c)
            else:
                c = ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(exact_duration)
                
            sub_clip = create_subtitle_clip(scene_text, exact_duration, target_w, target_h)
            if sub_clip: c = CompositeVideoClip([c, sub_clip])
            
            c = c.set_audio(scene_audio)
            clips.append(c)
            
        except Exception as e:
            print(f"Skipping scene {i} error: {e}")

    # Concatenate all perfectly synced blocks together
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Add Background Music across the whole video
    bgm_file = download_bgm(bgm_keyword)
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.06)
            if bgm.duration < final_video.duration:
                bgm = concatenate_audioclips([bgm] * (int(final_video.duration / bgm.duration) + 1))
            bgm = bgm.subclip(0, final_video.duration)
            
            final_audio = CompositeAudioClip([final_video.audio, bgm])
            final_video = final_video.set_audio(final_audio)
        except: pass

    out_name = f"V4_PODCAST_SHORT_{int(time.time())}.mp4"
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
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
    
    if not script_data or not isinstance(script_data, dict):
        return
        
    final_video = build_v4_studio_video(script_data.get('scenes', []), script_data.get('bgm_keyword', 'suspense'))
    upload_to_youtube(final_video, script_data.get('seo', {}))

if __name__ == "__main__":
    main()
