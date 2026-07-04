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

def generate_master_script(topic):
    # 🚨 V3 AI BRAIN: Strictly designed for maximum dopamine and watch time
    prompt = f"""
    You are a viral YouTube Shorts producer for a Finance Channel. Write a fast-paced, highly controversial 150-word script about '{topic}'.
    
    RULES:
    1. THE HOOK: The first 3 seconds MUST provoke fear, greed, or intense curiosity. 
    2. PACING: Short, punchy phrases. No boring explanations.
    3. VISUALS: Provide a 2-word highly specific cinematic keyword for each scene (e.g., 'mansion night', 'hacker desk', 'wallstreet panic').
    4. CHUNKED TEXT: Break the 'text' into very small 3-4 word chunks so they flash quickly on screen.
    
    Return ONLY valid JSON matching this exact structure:
    {{
        "seo": {{
            "title": "Insane Clickbait Title | #shorts",
            "description": "Engaging description with SEO keywords",
            "tags": "finance, money, wealth, investing, crash"
        }},
        "bgm_keyword": "phonk",
        "scenes": [
            {{
                "text": "The banks are lying.",
                "keyword": "bank vault"
            }}
        ]
    }}
    Make EXACTLY 18 fast-paced scenes! No emojis. Return ONLY JSON.
    """
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}", "Content-Type": "application/json"}
    try:
        models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]
        for model in models:
            payload = {"model": model, "messages": [{"role": "system", "content": "You output strict JSON."}, {"role": "user", "content": prompt}]}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=40)
            if response.status_code == 200:
                clean_json = response.json()['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
    except: exit("AI Generation Failed. Retrying next run.")

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

def generate_voice_and_audio(scenes, bgm_keyword):
    print("🎤 Generating Ultra-Crisp AI Voice...")
    full_script = " ".join([str(scene.get('text', '')).strip() for scene in scenes])
    clean_script = full_script.replace('"', "'")
    
    # Using a more aggressive/engaging voice
    os.system(f'edge-tts --voice "en-US-GuyNeural" --rate=+10% --text "{clean_script}" --write-media voice.mp3')
    
    voice = AudioFileClip("voice.mp3")
    bgm_file = download_bgm(bgm_keyword)
    
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.08) # Loud enough to feel, quiet enough to hear voice
            if bgm.duration < voice.duration:
                bgm = concatenate_audioclips([bgm] * (int(voice.duration / bgm.duration) + 1))
            bgm = bgm.subclip(0, voice.duration)
            final_audio = CompositeAudioClip([voice, bgm])
            final_audio.write_audiofile("final_audio.mp3", fps=44100, logger=None)
            voice.close(); bgm.close()
            return "final_audio.mp3"
        except: pass
    return "voice.mp3"

def generate_ai_image(prompt, index):
    safe_prompt = urllib.parse.quote(f"Cinematic masterpiece, 8k resolution, highly detailed, dramatic lighting, vertical 9:16, {prompt}")
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
    # 🚨 V3 FILTER: Forcing 4K and cinematic parameters on Pixabay
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
    # 🚨 V3 MOTION ENGINE: Slowly zooms in on images to create high-end movement
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
        # 🚨 V3 CAPTIONS: Massive, high-contrast yellow text in the exact center of the screen
        txt_clip = TextClip(clean_text, fontsize=100, color='#FFFF00', stroke_color='black', stroke_width=6, method='caption', size=(target_w - 150, None))
        if txt_clip.get_frame(0).size == 0: return None
        return txt_clip.set_position(('center', 'center')).set_duration(duration)
    except: return None

def edit_short(audio_file, scenes, target_w=1080, target_h=1920):
    print("🎬 Rendering V3 Cinematic Final Cut...")
    audio = AudioFileClip(audio_file)
    dur_per_scene = audio.duration / max(len(scenes), 1)
    clips = []
    
    for i, scene in enumerate(scenes):
        file, m_type = download_media(scene.get('keyword', 'abstract'), i)
        
        try:
            if m_type == "video" and file:
                c = VideoFileClip(file).without_audio()
                c.get_frame(0.1) 
                c = smart_crop_to_tiktok(c)
                c = vfx.loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
            elif m_type == "image" and file:
                c = ImageClip(file).set_duration(dur_per_scene)
                c = smart_crop_to_tiktok(c)
                c = add_ken_burns_effect(c) # Apply cinematic zoom to images
            else:
                fallback, _ = generate_ai_image("dark cinematic abstract background", i)
                c = ImageClip(fallback).set_duration(dur_per_scene) if fallback else ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(dur_per_scene)
                if fallback: c = add_ken_burns_effect(smart_crop_to_tiktok(c))
            
            if c.get_frame(0).size == 0: raise ValueError("Corrupted Array")
            
            sub_clip = create_subtitle_clip(scene.get('text', ''), dur_per_scene, target_w, target_h)
            if sub_clip: c = CompositeVideoClip([c, sub_clip])
            
            clips.append(c.set_duration(dur_per_scene))
            
        except Exception as e:
            print(f"Skipping corrupted scene {i}")
            clips.append(ColorClip(size=(target_w, target_h), color=(20, 20, 20)).set_duration(dur_per_scene))

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    out_name = f"V3_VIRAL_SHORT_{int(time.time())}.mp4"
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
    audio.close(); final_video.close()
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
    final_audio = generate_voice_and_audio(script_data.get('scenes', []), script_data.get('bgm_keyword', 'phonk'))
    final_video = edit_short(final_audio, script_data.get('scenes', []))
    upload_to_youtube(final_video, script_data.get('seo', {}))

if __name__ == "__main__":
    main()
