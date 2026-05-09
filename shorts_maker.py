import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET
from gtts import gTTS

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip
from moviepy.video.fx.loop import loop as vfx_loop

# 🚨 THE REAL BUG FIX: Importing audio effects safely and directly from their source files
from moviepy.audio.fx.volumex import volumex as afx_volumex
from moviepy.audio.fx.audio_loop import audio_loop as afx_audio_loop

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
        chosen_topic = random.choice(trends[:15])
        print(f"🎯 Locked Viral Topic: {chosen_topic}")
        return chosen_topic
    except: pass
    return "The Hidden Cost of Living in the USA"

def generate_master_script(topic):
    prompt = f"""
    You are a viral YouTube Shorts scriptwriter. Write a highly engaging 150-word script about '{topic}'.
    
    RULES:
    1. THE HOOK: Scene 1 MUST be a 5-second hooking statement or question.
    2. BGM: Provide a 1-2 word keyword for the best background music (e.g., 'suspense', 'lofi', 'epic', 'sad').
    3. VISUALS: 'keyword' must be a SINGLE abstract word (e.g., 'money', 'city', 'documents').
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Insane Clickbait Title under 60 chars",
            "description": "Engaging description with 3 hashtags",
            "tags": "exactly 15 comma-separated highly searched keywords"
        }},
        "bgm_keyword": "suspense",
        "scenes": [
            {{
                "text": "The spoken text...",
                "keyword": "city"
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

def download_bgm(keyword):
    print(f"🎵 Hunting for Background Music: '{keyword}'...")
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/audio/?key={PIXABAY_API_KEY}&q={urllib.parse.quote(keyword)}"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                link = resp['hits'][0]['audio_download']
                fpath = "bgm.mp3"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath
    except Exception as e: print(f"BGM Error: {e}")
    return None

def generate_voice_and_audio(scenes, bgm_keyword):
    print("🎤 Generating Voiceover and mixing audio...")
    full_script = " ".join([scene['text'] for scene in scenes])
    tts = gTTS(text=full_script, lang='en', tld='co.uk')
    tts.save("voice.mp3")
    
    voice = AudioFileClip("voice.mp3")
    bgm_file = download_bgm(bgm_keyword)
    
    if bgm_file:
        try:
            # 🚨 Safely applying volume and loop effects using direct imports
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.08)
            if bgm.duration < voice.duration:
                bgm = afx_audio_loop(bgm, duration=voice.duration)
            else:
                bgm = bgm.subclip(0, voice.duration)
                
            final_audio = CompositeAudioClip([voice, bgm])
            final_audio.write_audiofile("final_audio.mp3", fps=44100, logger=None)
            voice.close(); bgm.close()
            return "final_audio.mp3"
        except Exception as e:
            print(f"Audio mix failed, using voice only: {e}")
            
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
    try:
        if PIXABAY_API_KEY:
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=vertical&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                link = video['videos']['medium']['url']
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: f.write(requests.get(link).content)
                return fpath, "video"
    except: pass
    return generate_ai_image(keyword, index)

def smart_crop_to_tiktok(clip, target_w=1080, target_h=1920):
    clip_ratio = clip.w / clip.h
    if clip_ratio > (target_w / target_h):
        return clip.resize(height=target_h).crop(x_center=clip.w/2, width=target_w)
    else:
        return clip.resize(width=target_w).crop(y_center=clip.h/2, height=target_h)

def create_subtitle_clip(text, duration, target_w):
    try:
        txt_clip = TextClip(text, fontsize=65, color='white', font='Liberation-Sans-Bold', stroke_color='black', stroke_width=2.5, method='caption', size=(target_w - 100, None))
        return txt_clip.set_position(('center', 'center')).set_duration(duration)
    except Exception as e:
        print(f"Subtitle generation failed: {e}")
        return None

def edit_short(audio_file, scenes, target_w=1080, target_h=1920):
    audio = AudioFileClip(audio_file)
    dur_per_scene = audio.duration / len(scenes)
    clips = []
    
    for i, scene in enumerate(scenes):
        file, m_type = download_media(scene['keyword'], i)
        
        try:
            if m_type == "video":
                c = VideoFileClip(file).without_audio()
                c = smart_crop_to_tiktok(c)
                c = vfx_loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
            elif m_type == "image":
                c = ImageClip(file)
                c = smart_crop_to_tiktok(c).set_duration(dur_per_scene)
            else:
                c = generate_ai_image("abstract background", i)
                c = ImageClip(c[0]).set_duration(dur_per_scene) if c[0] else ColorClip(size=(target_w, target_h), color=(50, 50, 50)).set_duration(dur_per_scene)
            
            sub_clip = create_subtitle_clip(scene['text'], dur_per_scene, target_w)
            if sub_clip:
                c = CompositeVideoClip([c, sub_clip])
                
            clips.append(c)
        except Exception as e:
            print(f"Error processing scene {i}, skipping to prevent black screen: {e}")

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    out_name = f"VIRAL_PRO_{int(time.time())}.mp4"
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
    
    bgm_keyword = script_data.get('bgm_keyword', 'suspense')
    final_audio = generate_voice_and_audio(script_data['scenes'], bgm_keyword)
    
    final_video = edit_short(final_audio, script_data['scenes'])
    upload_to_youtube(final_video, script_data['seo'])

if __name__ == "__main__":
    main()
