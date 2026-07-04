import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET
import re
import gc # 🚨 NEW: The Garbage Collector to clear RAM!

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
    print("\n🌍 Scraping for High-Stakes Deep-Dive Topics...")
    backup_topics = [
        "The 2026 Wealth Transfer: Who is Really Getting Rich?",
        "How BlackRock is Buying the Entire World",
        "The Dark Truth About the US Debt Crisis",
        "Why the Middle Class Will Not Exist in 10 Years"
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
        if len(scenes) > 15: return True 
    return False

def generate_master_script(topic):
    prompt = f"""
    You are an elite Netflix Documentary director. Write a highly engaging 600-word, 3 to 4-minute documentary script about '{topic}'.
    
    RULES:
    1. THE HOOK: The first sentence must be a mind-blowing hook.
    2. THE STORY: Deep dive into the topic. Keep it highly cinematic, mysterious, and factual.
    3. THUMBNAIL: Create a 'Mr Beast' style prompt for an AI image generator.
    4. THUMBNAIL TEXT: 2 to 4 words of massive clickbait text.
    5. VISUALS: Provide a 2-3 word cinematic keyword for EACH scene.
    6. LOCATIONS: If a scene talks about a specific real-world city/country, provide the exact name in the 'location_name' field.
    7. TEXT CHUNKS: Break the spoken text into exactly 1-2 short sentences per scene.
    
    Return ONLY valid JSON matching this structure:
    {{
        "seo": {{"title": "Insane Clickbait Title | Deep Dive", "description": "Engaging description...", "tags": "finance, money, economy, documentary"}},
        "thumbnail_prompt": "Shocked face, vibrant colors, cinematic",
        "thumbnail_text": "THE TRUTH",
        "bgm_keyword": "documentary dark",
        "scenes": [
            {{"text": "The banks are hiding a massive secret.", "keyword": "bank vault", "location_name": ""}},
            {{"text": "Right now in Wall Street, they are doing this.", "keyword": "wallstreet drone", "location_name": "Wall Street"}}
        ]
    }}
    Make EXACTLY 35 fast-paced scenes! No emojis. Return ONLY valid JSON block.
    """
    
    print("🧠 Attempting Brain 1 (OpenRouter - Heavy Request)...")
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip() if OPENROUTER_API_KEY else ''}", "Content-Type": "application/json"}
    try:
        payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            script_json = extract_json(response.json()['choices'][0]['message']['content'])
            if is_valid_script(script_json): return script_json
    except: pass

    print("🚀 Brain 1 Busy. Routing to Brain 2 (Free Dynamic AI)...")
    try:
        safe_prompt = urllib.parse.quote(f"Respond strictly in JSON format. {prompt}")
        url = f"https://text.pollinations.ai/prompt/{safe_prompt}?model=openai"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            script_json = extract_json(response.text)
            if is_valid_script(script_json): return script_json
    except: pass

    print("⚠️ ALL AI NETWORKS DOWN. Using Emergency Local Long Script.")
    return {
        "seo": {"title": "The Greatest Wealth Transfer in History 🚨", "description": "How the 1% is buying everything.", "tags": "finance, economy, wealth transfer"},
        "thumbnail_prompt": "Billionaire laughing while holding a golden globe, cinematic, hyperrealistic",
        "thumbnail_text": "THEY OWN YOU",
        "bgm_keyword": "dark synthwave",
        "scenes": [
            {"text": "We are living through the greatest wealth transfer in human history.", "keyword": "money printing cinematic", "location_name": ""},
            {"text": "And the crazy part? Most people don't even see it happening.", "keyword": "crowded street drone", "location_name": ""},
            {"text": "While regular people are struggling to buy a single home...", "keyword": "suburb house cinematic", "location_name": ""},
            {"text": "Massive corporations are buying up entire neighborhoods.", "keyword": "city skyline drone", "location_name": "New York City"},
            {"text": "They use cheap institutional debt to outbid families by tens of thousands of dollars.", "keyword": "signing contract cinematic", "location_name": ""},
            {"text": "The goal is simple: turn a nation of homeowners into a nation of renters.", "keyword": "apartment building drone", "location_name": ""},
            {"text": "Because when you own nothing, you are entirely dependent on the system.", "keyword": "matrix code cinematic", "location_name": ""},
            {"text": "This is why asset prices are skyrocketing while wages stay completely flat.", "keyword": "stock chart dramatic", "location_name": ""},
            {"text": "The 1% knows that fiat currency is designed to lose value over time.", "keyword": "burning money 4k", "location_name": ""},
            {"text": "So they store their wealth in real estate, gold, and equity.", "keyword": "gold bars cinematic", "location_name": ""},
            {"text": "If you are keeping your money in a traditional savings account right now...", "keyword": "bank vault dramatic", "location_name": ""},
            {"text": "You are actually losing purchasing power every single day.", "keyword": "clock ticking cinematic", "location_name": ""},
            {"text": "Look at what is happening in Silicon Valley.", "keyword": "tech campus drone", "location_name": "Silicon Valley"},
            {"text": "Tech billionaires are quietly buying thousands of acres of farmland.", "keyword": "tractor field drone", "location_name": ""},
            {"text": "They aren't doing this to become farmers.", "keyword": "businessman cinematic", "location_name": ""},
            {"text": "They are doing this because land is a finite resource.", "keyword": "earth satellite view", "location_name": ""},
            {"text": "The rules of the game have been completely rewritten.", "keyword": "chess board cinematic", "location_name": ""},
            {"text": "You can no longer save your way to wealth.", "keyword": "empty wallet 4k", "location_name": ""},
            {"text": "You have to invest your way to freedom.", "keyword": "soaring eagle cinematic", "location_name": ""},
            {"text": "The clock is ticking. What is your next move?", "keyword": "dark storm dramatic", "location_name": ""}
        ]
    }

def download_bgm(keyword):
    if not keyword: keyword = "documentary dark"
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

def generate_ai_image(prompt, index, width=1920, height=1080):
    safe_prompt = urllib.parse.quote(f"Cinematic documentary footage, 8k resolution, highly detailed, photorealistic, 16:9, {prompt}")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&model=flux"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: f.write(resp.content)
            return fpath, "image"
    except: pass
    return None, None

def create_mrbeast_thumbnail(prompt, text):
    print("🖼️ Generating V5 FLUX Thumbnail...")
    if not prompt: prompt = "Surprised face, vibrant colors, high contrast, cinematic"
    if not text: text = "SHOCKING"
    
    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()
    if not clean_text: clean_text = "SHOCKING"
    
    file, _ = generate_ai_image(f"YouTube thumbnail, Mr Beast style, highly saturated, {prompt}", "thumb")
    if file:
        try:
            img_clip = ImageClip(file)
            txt_clip = TextClip(clean_text.upper(), fontsize=160, color='yellow', stroke_color='black', stroke_width=8)
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(1)
            final_thumb = CompositeVideoClip([img_clip, txt_clip])
            final_thumb.save_frame("final_thumbnail.jpg", t=0)
            return "final_thumbnail.jpg"
        except: pass
    return None

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
                    fpath = f"scene_{index}.mp4"
                    with open(fpath, "wb") as f: f.write(requests.get(video['videos']['large']['url']).content)
                    return fpath, "video"
        except: pass
        map_prompt = f"Google Earth top-down satellite view of {location_name}, 3D map drone shot, hyperrealistic"
        return generate_ai_image(map_prompt, index)

    simple_kw = urllib.parse.quote(f"{str(keyword)} cinematic")
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=horizontal&min_width=1280&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(video['videos']['medium']['url']).content) # Uses medium to save massive amounts of RAM
                return fpath, "video"
    except: pass
    return generate_ai_image(keyword, index)

def force_16_9_landscape(clip, target_w=1920, target_h=1080):
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h
    
    if clip_ratio > target_ratio:
        resized = clip.resize(height=target_h)
        return resized.crop(x_center=resized.w/2, width=target_w)
    else:
        resized = clip.resize(width=target_w)
        return resized.crop(y_center=resized.h/2, height=target_h)

def add_3d_ken_burns_effect(clip, zoom_ratio=0.04):
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
    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()
    if len(clean_text) < 1: return None
    try:
        txt_clip = TextClip(clean_text, fontsize=70, color='white', stroke_color='black', stroke_width=4, method='caption', size=(target_w - 400, None))
        if txt_clip.get_frame(0).size == 0: return None
        return txt_clip.set_position(('center', 0.85), relative=True).set_duration(duration)
    except: return None

def build_v5_netflix_long_video(scenes, bgm_keyword, target_w=1920, target_h=1080):
    print("🎬 Initializing V5.1 RAM-Optimized Netflix Engine...")
    clips = []
    
    for i, scene in enumerate(scenes):
        scene_text = scene.get('text', '').strip()
        scene_kw = scene.get('keyword', 'abstract')
        location_name = scene.get('location_name', '')
        if len(scene_text) < 2: continue
        
        txt_file = f"temp_scene_{i}.txt"
        audio_file = f"scene_{i}.mp3"
        with open(txt_file, "w", encoding="utf-8") as f: f.write(scene_text)
        
        os.system(f'edge-tts --voice "en-US-ChristopherNeural" --rate=+0% -f {txt_file} --write-media {audio_file}')
        
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 500:
            from gtts import gTTS
            gTTS(text=scene_text, lang='en', tld='co.uk').save(audio_file)
            
        scene_audio = AudioFileClip(audio_file)
        exact_duration = scene_audio.duration
        
        file, m_type = download_media(scene_kw, i, location_name)
        try:
            if m_type == "video" and file:
                c = VideoFileClip(file).without_audio()
                c = force_16_9_landscape(c, target_w, target_h)
                c = vfx.loop(c, duration=exact_duration) if c.duration < exact_duration else c.subclip(0, exact_duration)
            elif m_type == "image" and file:
                c = ImageClip(file).set_duration(exact_duration)
                c = force_16_9_landscape(c, target_w, target_h)
                c = add_3d_ken_burns_effect(c) 
            else:
                c = ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(exact_duration)
                
            sub_clip = create_subtitle_clip(scene_text, exact_duration, target_w, target_h)
            if sub_clip: c = CompositeVideoClip([c, sub_clip])
            
            c = c.set_audio(scene_audio)
            clips.append(c)
            
        except Exception as e:
            print(f"Skipping scene {i} error: {e}")
            
        # 🚨 GARBAGE COLLECTOR: Clears system RAM after processing each heavy scene
        gc.collect() 

    print("🧩 Merging all scenes into a massive Master File...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    bgm_file = download_bgm(bgm_keyword)
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.05)
            if bgm.duration < final_video.duration:
                bgm = concatenate_audioclips([bgm] * (int(final_video.duration / bgm.duration) + 1))
            bgm = bgm.subclip(0, final_video.duration)
            final_audio = CompositeAudioClip([final_video.audio, bgm])
            final_video = final_video.set_audio(final_audio)
        except: pass

    out_name = f"NETFLIX_DOC_{int(time.time())}.mp4"
    
    # 🚨 CPU & RAM PROTECTOR: Drops frame rate to Hollywood standard 24fps and forces ultrafast rendering
    print("⚙️ Rendering Video at 24 FPS (Cinematic Standard)...")
    final_video.write_videofile(out_name, fps=24, codec="libx264", preset="ultrafast", threads=4, audio_codec="aac", logger=None)
    
    final_video.close()
    return out_name

def upload_to_youtube(video_file, seo, thumbnail_file):
    if not os.path.exists("token.json"): return False
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = Credentials.from_authorized_user_file("token.json", scopes)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    tag_list = [t.strip() for t in seo.get('tags', '').split(',')]
    
    body = {
        "snippet": {"title": seo.get('title', 'Deep Dive Documentary'), "description": seo.get('description', ''), "tags": tag_list[:20], "categoryId": "25"}, 
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
    
    if not script_data or not isinstance(script_data, dict): return
    
    thumb_prompt = script_data.get('thumbnail_prompt', '')
    thumb_text = script_data.get('thumbnail_text', '')
    thumbnail_file = create_mrbeast_thumbnail(thumb_prompt, thumb_text)
        
    final_video = build_v5_netflix_long_video(script_data.get('scenes', []), script_data.get('bgm_keyword', 'documentary suspense'))
    upload_to_youtube(final_video, script_data.get('seo', {}), thumbnail_file)

if __name__ == "__main__":
    main()
