import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET
import re

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip, concatenate_audioclips, concatenate_videoclips
from moviepy.video.fx.loop import loop as vfx_loop
from moviepy.audio.fx.volumex import volumex as afx_volumex

import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def get_fresh_topic():
    print("\n🌍 Hunting for Viral Finance Topics (Bypassing Google)...")
    
    backup_topics = [
        "The Hidden Trillion Dollar Economy Nobody Talks About",
        "How BlackRock Actually Controls The World",
        "The Terrifying Truth About The US Housing Market",
        "Why The Middle Class Is Being Intentionally Destroyed",
        "The Secret Banking System Rich People Use",
        "What Happened to Silicon Valley Bank? The Real Story",
        "The Dark Side of the Federal Reserve",
        "How China is Secretly Buying Up American Land"
    ]
    
    try:
        # 🚨 THE YAHOO UPGRADE: Yahoo Finance is bot-friendly and perfect for your niche!
        url = 'https://finance.yahoo.com/news/rssindex'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            tree = ET.fromstring(resp.content)
            trends = [item.text for item in tree.findall('./channel/item/title')]
            if trends:
                chosen_topic = random.choice(trends[:5]) 
                print(f"🎯 Locked Live Yahoo Finance Topic: {chosen_topic}")
                return chosen_topic
    except Exception as e:
        print(f"⚠️ Yahoo News blocked the server: {e}")
        
    chosen_topic = random.choice(backup_topics)
    print(f"🎯 Locked Evergreen Topic: {chosen_topic}")
    return chosen_topic

def generate_master_script(topic):
    prompt = f"""
    You are an elite YouTube Documentary director. Write a highly engaging 300-word mini-documentary about '{topic}'.
    
    RULES:
    1. THE HOOK: The first sentence must be a mind-blowing hook.
    2. THE STORY: Deep dive into the topic. Keep it fast-paced.
    3. THUMBNAIL: Create a 'Mr Beast' style prompt for an AI image generator.
    4. THUMBNAIL TEXT: 2 to 4 words of massive clickbait text.
    5. VISUALS: Provide a 1-3 word keyword for EACH scene (e.g., 'wallstreet drone', 'hacker cinematic').
    6. LOCATIONS: If a scene talks about a specific real-world city, country, or landmark, you MUST provide the exact name in the 'location_name' field. If no specific location is mentioned, leave it empty.
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Insane Clickbait Title | Deep Dive",
            "description": "A long, detailed description explaining the topic...",
            "tags": "15, comma, separated, long-tail, keywords"
        }},
        "thumbnail_prompt": "Shocked face, vibrant colors, Mr Beast style...",
        "thumbnail_text": "THE TRUTH",
        "bgm_keyword": "dark synthwave",
        "scenes": [
            {{
                "text": "The spoken text...",
                "keyword": "city drone",
                "location_name": "New York City"
            }}
        ]
    }}
    Make exactly 15 scenes! Return ONLY valid JSON. Do not use emojis.
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
            response = requests.post(url, headers=headers, json=payload, timeout=40)
            if response.status_code == 200:
                clean_json = response.json()['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except: pass
    exit()

def create_mrbeast_thumbnail(prompt, text):
    print("🖼️ Generating Mr. Beast Style Thumbnail...")
    if not prompt: prompt = "Surprised face, vibrant colors, high contrast, cinematic"
    if not text: text = "SHOCKING"
    
    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()
    if not clean_text: clean_text = "SHOCKING"
    
    safe_prompt = urllib.parse.quote(f"{prompt}, youtube thumbnail style, 8k, highly saturated, 16:9")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            with open("raw_thumb.jpg", "wb") as f: f.write(resp.content)
            img_clip = ImageClip("raw_thumb.jpg")
            txt_clip = TextClip(clean_text.upper(), fontsize=160, color='yellow', font='Liberation-Sans-Bold', stroke_color='black', stroke_width=8)
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(1)
            final_thumb = CompositeVideoClip([img_clip, txt_clip])
            final_thumb.save_frame("final_thumbnail.jpg", t=0)
            return "final_thumbnail.jpg"
    except: pass
    return None

def download_bgm(keyword):
    if not keyword: keyword = "documentary"
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/audio/?key={PIXABAY_API_KEY}&q={urllib.parse.quote(str(keyword))}"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                link = resp['hits'][0]['audio_download']
                fpath = "bgm.mp3"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath
    except: pass
    return None

def generate_voice_and_audio(scenes, bgm_keyword):
    print("🎤 Generating Long-Form Voiceover...")
    full_script = " ".join([str(scene.get('text', '')).strip() for scene in scenes])
    
    clean_script = full_script.replace('"', "'")
    os.system(f'edge-tts --voice "en-US-ChristopherNeural" --text "{clean_script}" --write-media voice.mp3')
    
    if not os.path.exists("voice.mp3"):
        from gtts import gTTS
        gTTS(text=full_script, lang='en', tld='co.uk').save("voice.mp3")
    
    voice = AudioFileClip("voice.mp3")
    bgm_file = download_bgm(bgm_keyword)
    
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.05)
            if bgm.duration < voice.duration:
                loops_needed = int(voice.duration / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * loops_needed)
            bgm = bgm.subclip(0, voice.duration)
            final_audio = CompositeAudioClip([voice, bgm])
            final_audio.write_audiofile("final_audio.mp3", fps=44100, logger=None)
            voice.close(); bgm.close()
            return "final_audio.mp3"
        except: pass
    return "voice.mp3"

def generate_ai_image(prompt, index):
    if not prompt: prompt = "dark cinematic abstract"
    safe_prompt = urllib.parse.quote(f"Shot on RED camera, 8k resolution, cinematic lighting, dramatic shadows, landscape 16:9, highly detailed, {prompt}")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(resp.content)
            return fpath, "image"
    except: pass
    return None, None

def download_media(keyword, index, location_name=""):
    if location_name and len(location_name) > 2:
        print(f"📍 Location Detected: {location_name}. Initiating Drone/Map Sequence...")
        safe_loc = urllib.parse.quote(str(location_name))
        try:
            if PIXABAY_API_KEY:
                url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={safe_loc}+drone&orientation=horizontal&min_width=1920&per_page=5"
                resp = requests.get(url, timeout=10).json()
                if resp.get('hits'):
                    video = random.choice(resp['hits']) 
                    link = video['videos']['medium']['url']
                    fpath = f"scene_{index}.mp4"
                    with open(fpath, "wb") as f: f.write(requests.get(link).content)
                    print("✅ Real Drone Footage Found!")
                    return fpath, "video"
        except: pass
        
        print(f"🛰️ Generating Google Earth 3D Satellite Map for {location_name}...")
        map_prompt = f"Google Earth top-down satellite view of {location_name}, 3D map drone shot, photorealistic 8k map"
        return generate_ai_image(map_prompt, index)

    if not keyword: keyword = "abstract cinematic"
    simple_kw = urllib.parse.quote(f"{str(keyword)} cinematic 4k")
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=horizontal&min_width=1920&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                link = video['videos']['medium']['url']
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath, "video"
    except: pass
    return generate_ai_image(keyword, index)

def smart_crop_to_landscape(clip, target_w=1920, target_h=1080):
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h
    if clip_ratio > target_ratio:
        return clip.resize(height=target_h).crop(x_center=clip.w/2, width=target_w)
    else:
        return clip.resize(width=target_w).crop(y_center=clip.h/2, height=target_h)

def create_subtitle_clip(text, duration, target_w, target_h):
    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()
    if len(clean_text) < 1: return None
    try:
        txt_clip = TextClip(clean_text, fontsize=65, color='white', stroke_color='black', stroke_width=3.5, method='caption', size=(target_w - 300, None))
        if txt_clip.get_frame(0).size == 0: return None
        return txt_clip.set_position(('center', 0.85), relative=True).set_duration(duration)
    except: return None

def edit_long_video(audio_file, scenes, target_w=1920, target_h=1080):
    print("🎬 Rendering 16:9 Cinematic Mini-Documentary...")
    audio = AudioFileClip(audio_file)
    total_audio_duration = audio.duration
    dur_per_scene = total_audio_duration / max(len(scenes), 1)
    clips = []
    
    for i, scene in enumerate(scenes):
        scene_keyword = scene.get('keyword', 'abstract')
        scene_text = scene.get('text', '')
        location_name = scene.get('location_name', '')
        
        file, m_type = download_media(scene_keyword, i, location_name)
        
        try:
            if m_type == "video" and file:
                c = VideoFileClip(file).without_audio()
                c.get_frame(0.1) 
                c = smart_crop_to_landscape(c)
                c = vfx_loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
            elif m_type == "image" and file:
                c = ImageClip(file)
                c = smart_crop_to_landscape(c).set_duration(dur_per_scene)
            else:
                fallback, _ = generate_ai_image("dark cinematic abstract background", i)
                c = ImageClip(fallback).set_duration(dur_per_scene) if fallback else ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(dur_per_scene)
            
            if c.get_frame(0).size == 0: raise ValueError("Corrupted Media Array")
            
            sub_clip = create_subtitle_clip(scene_text, dur_per_scene, target_w, target_h)
            if sub_clip: c = CompositeVideoClip([c, sub_clip])
            
            c = c.set_duration(dur_per_scene)
            clips.append(c)
            
        except Exception as e:
            print(f"Skipping corrupted scene {i}: {e}")
            safe_fallback, _ = generate_ai_image(scene_keyword, i)
            if safe_fallback:
                safe_c = ImageClip(safe_fallback).set_duration(dur_per_scene)
                safe_c = smart_crop_to_landscape(safe_c)
            else:
                safe_c = ColorClip(size=(target_w, target_h), color=(20, 20, 20)).set_duration(dur_per_scene)
            
            sub_clip = create_subtitle_clip(scene_text, dur_per_scene, target_w, target_h)
            if sub_clip: safe_c = CompositeVideoClip([safe_c, sub_clip])
            clips.append(safe_c)

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final_video = final_video.set_duration(total_audio_duration)
    
    out_name = f"CINEMATIC_DOC_{int(time.time())}.mp4"
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
    audio.close(); final_video.close()
    return out_name

def upload_to_youtube(video_file, seo, thumbnail_file):
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
        response = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)).execute()
        video_id = response.get('id')
        if thumbnail_file and os.path.exists(thumbnail_file):
            try: youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_file)).execute()
            except: pass
        return True
    except: return False

def main():
    topic = get_fresh_topic()
    script_data = generate_master_script(topic)
    
    thumb_prompt = script_data.get('thumbnail_prompt', '')
    thumb_text = script_data.get('thumbnail_text', '')
    thumbnail_file = create_mrbeast_thumbnail(thumb_prompt, thumb_text)
    
    bgm_keyword = script_data.get('bgm_keyword', 'epic')
    final_audio = generate_voice_and_audio(script_data.get('scenes', []), bgm_keyword)
    
    final_video = edit_long_video(final_audio, script_data.get('scenes', []))
    upload_to_youtube(final_video, script_data.get('seo', {}), thumbnail_file)

if __name__ == "__main__":
    main()
