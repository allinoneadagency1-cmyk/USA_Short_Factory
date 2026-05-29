import os
import time
import requests
import json
import random
import urllib.parse
import xml.etree.ElementTree as ET

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
    print("\n🌍 Scraping Google for Deep-Dive Documentary Topics...")
    try:
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        tree = ET.parse(urllib.request.urlopen(req))
        trends = [item.text.split(" - ")[0] for item in tree.getroot().findall('./channel/item/title')]
        chosen_topic = random.choice(trends[:5]) # Top 5 only for major news
        print(f"🎯 Locked Documentary Topic: {chosen_topic}")
        return chosen_topic
    except:
        pass
    return "The Untold Truth About The Global Economy"

def generate_master_script(topic):
    prompt = f"""
    You are an elite YouTube Documentary writer. Write a highly engaging 300-word mini-documentary about '{topic}'.
    
    RULES:
    1. THE HOOK: The first sentence must be a mind-blowing hook.
    2. THE STORY: Deep dive into the topic. Keep it fast-paced.
    3. THUMBNAIL: Create a 'Mr Beast' style prompt for an AI image generator (e.g., 'Shocked man holding glowing money, high contrast, vibrant colors, explosive background').
    4. THUMBNAIL TEXT: 2 to 4 words of massive clickbait text to overlay on the image (e.g., "WE ARE DOOMED").
    5. VISUALS: Provide a 1-2 word abstract visual keyword for EACH scene (e.g., 'wallstreet', 'hacker', 'mansion').
    
    Structure the JSON exactly like this:
    {{
        "seo": {{
            "title": "Insane Clickbait Title | Deep Dive",
            "description": "A long, detailed description explaining the topic...",
            "tags": "15, comma, separated, long-tail, keywords"
        }},
        "thumbnail_prompt": "Shocked face, vibrant colors, Mr Beast style...",
        "thumbnail_text": "THE HIDDEN TRUTH",
        "bgm_keyword": "dark synthwave",
        "scenes": [
            {{
                "text": "The spoken text...",
                "keyword": "city"
            }}
        ]
    }}
    Make exactly 15 scenes! Return ONLY valid JSON.
    """
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}", "Content-Type": "application/json"}
    
    try:
        models_resp = requests.get("https://openrouter.ai/api/v1/models").json()
        free_models = [m['id'] for m in models_resp.get('data', []) if str(m['id']).endswith(':free')][:3]
        if not free_models: 
            free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]
    except: 
        free_models = ["qwen/qwen-2-7b-instruct:free", "google/gemma-2-9b-it:free"]

    url = "https://openrouter.ai/api/v1/chat/completions"
    for model in free_models:
        payload = {"model": model, "messages": [{"role": "system", "content": "You output strict JSON."}, {"role": "user", "content": prompt}]}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=40)
            if response.status_code == 200:
                clean_json = response.json()['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except:
            pass
    exit()

def create_mrbeast_thumbnail(prompt, text):
    print("🖼️ Generating Mr. Beast Style Thumbnail...")
    if not prompt: prompt = "Surprised face, vibrant colors, high contrast, cinematic"
    if not text: text = "SHOCKING"
    
    safe_prompt = urllib.parse.quote(f"{prompt}, youtube thumbnail style, 8k, highly saturated, 16:9")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            with open("raw_thumb.jpg", "wb") as f: 
                f.write(resp.content)
            
            # Add massive yellow text to the thumbnail using MoviePy
            img_clip = ImageClip("raw_thumb.jpg")
            txt_clip = TextClip(str(text).upper(), fontsize=160, color='yellow', font='Liberation-Sans-Bold', stroke_color='black', stroke_width=8)
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(1)
            
            final_thumb = CompositeVideoClip([img_clip, txt_clip])
            final_thumb.save_frame("final_thumbnail.jpg", t=0)
            return "final_thumbnail.jpg"
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
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
                with open(fpath, "wb") as f: 
                    f.write(requests.get(link).content)
                return fpath
    except:
        pass
    return None

def generate_voice_and_audio(scenes, bgm_keyword):
    print("🎤 Generating Long-Form Voiceover...")
    full_script = " ".join([scene.get('text', '') for scene in scenes])
    
    clean_script = full_script.replace('"', "'")
    os.system(f'edge-tts --voice "en-US-ChristopherNeural" --text "{clean_script}" --write-media voice.mp3')
    
    if not os.path.exists("voice.mp3"):
        from gtts import gTTS
        gTTS(text=full_script, lang='en', tld='co.uk').save("voice.mp3")
    
    voice = AudioFileClip("voice.mp3")
    bgm_file = download_bgm(bgm_keyword)
    
    if bgm_file:
        try:
            bgm = afx_volumex(AudioFileClip(bgm_file), 0.06)
            if bgm.duration < voice.duration:
                loops_needed = int(voice.duration / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * loops_needed)
            bgm = bgm.subclip(0, voice.duration)
            final_audio = CompositeAudioClip([voice, bgm])
            final_audio.write_audiofile("final_audio.mp3", fps=44100, logger=None)
            voice.close(); bgm.close()
            return "final_audio.mp3"
        except:
            pass
    return "voice.mp3"

def generate_ai_image(prompt, index):
    if not prompt: prompt = "dark cinematic abstract"
    safe_prompt = urllib.parse.quote(f"Shot on RED camera, 8k resolution, landscape 16:9, highly detailed, {prompt}")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1920&height=1080&nologo=true"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            fpath = f"ai_scene_{index}.jpg"
            with open(fpath, "wb") as f: 
                f.write(resp.content)
            return fpath, "image"
    except:
        pass
    return None, None

def download_media(keyword, index):
    if not keyword: keyword = "abstract"
    simple_kw = urllib.parse.quote(str(keyword).split(" ")[0])
    try:
        if PIXABAY_API_KEY:
            # Note: orientation is 'horizontal' for long videos
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={simple_kw}&orientation=horizontal&per_page=10"
            resp = requests.get(url, timeout=10).json()
            if resp.get('hits'):
                video = random.choice(resp['hits']) 
                link = video['videos']['medium']['url']
                fpath = f"scene_{index}.mp4"
                with open(fpath, "wb") as f: 
                    f.write(requests.get(link).content)
                return fpath, "video"
    except:
        pass
    return generate_ai_image(keyword, index)

# 🚨 THE 16:9 UPGRADE: Crops footage for standard YouTube landscape mode
def smart_crop_to_landscape(clip, target_w=1920, target_h=1080):
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h
    if clip_ratio > target_ratio:
        return clip.resize(height=target_h).crop(x_center=clip.w/2, width=target_w)
    else:
        return clip.resize(width=target_w).crop(y_center=clip.h/2, height=target_h)

def create_subtitle_clip(text, duration, target_w, target_h):
    if not text: return None
    try:
        # Smaller, more professional font for long-form, placed at bottom center
        txt_clip = TextClip(str(text), fontsize=65, color='white', font='Liberation-Sans-Bold', stroke_color='black', stroke_width=3, method='caption', size=(target_w - 200, None))
        return txt_clip.set_position(('center', 0.85), relative=True).set_duration(duration)
    except:
        return None

def edit_long_video(audio_file, scenes, target_w=1920, target_h=1080):
    print("🎬 Rendering 16:9 Mini-Documentary...")
    audio = AudioFileClip(audio_file)
    dur_per_scene = audio.duration / max(len(scenes), 1)
    clips = []
    
    for i, scene in enumerate(scenes):
        scene_keyword = scene.get('keyword', 'abstract')
        scene_text = scene.get('text', '')
        
        file, m_type = download_media(scene_keyword, i)
        
        try:
            if m_type == "video":
                c = VideoFileClip(file).without_audio()
                c = smart_crop_to_landscape(c)
                c = vfx_loop(c, duration=dur_per_scene) if c.duration < dur_per_scene else c.subclip(0, dur_per_scene)
            elif m_type == "image":
                c = ImageClip(file)
                c = smart_crop_to_landscape(c).set_duration(dur_per_scene)
            else:
                c = generate_ai_image("dark cinematic abstract background", i)
                c = ImageClip(c[0]).set_duration(dur_per_scene) if c[0] else ColorClip(size=(target_w, target_h), color=(15, 15, 15)).set_duration(dur_per_scene)
            
            sub_clip = create_subtitle_clip(scene_text, dur_per_scene, target_w, target_h)
            if sub_clip:
                c = CompositeVideoClip([c, sub_clip])
                
            clips.append(c)
        except Exception as e:
            print(f"Skipping scene {i} error: {e}")

    final_video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    out_name = f"MINI_DOC_{int(time.time())}.mp4"
    final_video.write_videofile(out_name, fps=30, codec="libx264", audio_codec="aac", logger=None)
    audio.close(); final_video.close()
    return out_name

def upload_to_youtube(video_file, seo, thumbnail_file):
    if not os.path.exists("token.json"): 
        return False
        
    scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
    creds = Credentials.from_authorized_user_file("token.json", scopes)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    tag_list = [t.strip() for t in seo.get('tags', '').split(',')]
    
    body = {
        "snippet": {"title": seo.get('title', 'Deep Dive'), "description": seo.get('description', ''), "tags": tag_list[:20], "categoryId": "25"}, 
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }
    
    try:
        print("📤 Uploading Long Video...")
        response = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)).execute()
        
        video_id = response.get('id')
        print(f"✅ Video Uploaded! ID: {video_id}")
        
        # 🚨 THUMBNAIL UPLOAD (Requires channel to be phone-verified)
        if thumbnail_file and os.path.exists(thumbnail_file):
            print("🖼️ Uploading Custom Thumbnail...")
            try:
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_file)).execute()
                print("✅ Thumbnail attached!")
            except Exception as e:
                print(f"⚠️ Thumbnail failed (Is your YouTube channel phone verified?): {e}")
                
        return True
    except Exception as e: 
        print(f"Upload crashed: {e}")
        return False

def main():
    topic = get_fresh_topic()
    script_data = generate_master_script(topic)
    
    # Generate Thumbnail
    thumb_prompt = script_data.get('thumbnail_prompt', '')
    thumb_text = script_data.get('thumbnail_text', '')
    thumbnail_file = create_mrbeast_thumbnail(thumb_prompt, thumb_text)
    
    bgm_keyword = script_data.get('bgm_keyword', 'epic')
    final_audio = generate_voice_and_audio(script_data.get('scenes', []), bgm_keyword)
    
    final_video = edit_long_video(final_audio, script_data.get('scenes', []))
    upload_to_youtube(final_video, script_data.get('seo', {}), thumbnail_file)

if __name__ == "__main__":
    main()
