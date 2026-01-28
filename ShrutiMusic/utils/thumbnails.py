import os
import re

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from unidecode import unidecode
from py_yt import VideosSearch

from ShrutiMusic import app
from config import YOUTUBE_IMG_URL

os.makedirs("cache", exist_ok=True)

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def clear(text):
    if not text:
        return ""
    list = text.split(" ")
    title = ""
    for i in list:
        if len(title) + len(i) < 60:
            title += " " + i
    return title.strip()


async def gen_thumb(videoid, user_id=None, force_update=False):
    os.makedirs("cache", exist_ok=True)
    
    if os.path.isfile(f"cache/{videoid}.png") and not force_update:
        return f"cache/{videoid}.png"
    
    thumbnail = None
    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(videoid, limit=1)
        results_data = results.result()
        
        if results_data and "result" in results_data and results_data["result"]:
            result = results_data["result"][0]
            try:
                if "thumbnails" in result and result["thumbnails"]:
                    thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            except:
                pass
    except:
        pass
    
    if not thumbnail:
        thumbnail = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    
    fallback_thumbnails = [
        f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg",
        f"https://img.youtube.com/vi/{videoid}/sddefault.jpg",
        f"https://img.youtube.com/vi/{videoid}/mqdefault.jpg"
    ]

    temp_thumb = f"cache/thumb{videoid}.png"
    downloaded = False
    
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) > 5000:
                            async with aiofiles.open(temp_thumb, mode="wb") as f:
                                await f.write(content)
                            downloaded = True
            except:
                pass
            
            if not downloaded:
                for fallback_url in fallback_thumbnails:
                    try:
                        async with session.get(fallback_url) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                async with aiofiles.open(temp_thumb, mode="wb") as f:
                                    await f.write(content)
                                downloaded = True
                                break
                    except:
                        continue
            
            if not downloaded:
                return YOUTUBE_IMG_URL
                
    except:
        return YOUTUBE_IMG_URL

    try:
        template_path = "ShrutiMusic/assets/MrPerfect.jpg"
        if not os.path.exists(template_path):
            template_path = "ShrutiMusic/assets/Perfect.jpg"
            if not os.path.exists(template_path):
                return YOUTUBE_IMG_URL
            
        template = Image.open(template_path).convert("RGBA")
        template_width, template_height = template.size
        
        if not os.path.exists(temp_thumb):
            return YOUTUBE_IMG_URL
        
        song_art = Image.open(temp_thumb).convert("RGBA")
        
        artwork_width = int(template_width * 0.47)
        artwork_height = int(artwork_width * 0.52)
        artwork_x = int((template_width - artwork_width) / 2)
        artwork_y = int(template_height * 0.086)
        
        song_art = song_art.resize((artwork_width, artwork_height), Image.LANCZOS)
        corner_radius = int(artwork_width * 0.09)
        
        effects_padding = 15
        art_with_effects = Image.new(
            "RGBA", 
            (artwork_width + effects_padding*2, artwork_height + effects_padding*2),
            (0, 0, 0, 0)
        )
        
        shadow = Image.new("RGBA", art_with_effects.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [(effects_padding-5, effects_padding-5), 
             (effects_padding + artwork_width+5, effects_padding + artwork_height+5)],
            corner_radius+5,
            fill=(0, 0, 0, 100)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        art_with_effects.paste(shadow, (0, 0), shadow)
        
        mask = Image.new("L", (artwork_width, artwork_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (artwork_width, artwork_height)], corner_radius, fill=255)
        song_art.putalpha(mask)
        
        border_img = Image.new("RGBA", (artwork_width+6, artwork_height+6), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_img)
        border_draw.rounded_rectangle(
            [(0, 0), (artwork_width+6, artwork_height+6)],
            corner_radius+3,
            fill=(255, 255, 255, 0),
            outline=(255, 255, 255, 180),
            width=3
        )
        
        art_with_effects.paste(border_img, (effects_padding-3, effects_padding-3), border_img)
        art_with_effects.paste(song_art, (effects_padding, effects_padding), song_art)
        
        glow = Image.new("RGBA", art_with_effects.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.rounded_rectangle(
            [(effects_padding, effects_padding), 
             (effects_padding + artwork_width, effects_padding + artwork_height)],
            corner_radius,
            fill=(255, 255, 255, 0),
            outline=(180, 180, 255, 60),
            width=5
        )
        glow = glow.filter(ImageFilter.GaussianBlur(5))
        art_with_effects = Image.alpha_composite(art_with_effects, glow)
        
        template.paste(
            art_with_effects, 
            (artwork_x - effects_padding, artwork_y - effects_padding), 
            art_with_effects
        )
        
        final_image_path = f"cache/{videoid}.png"
        template.convert("RGB").save(final_image_path)
        
        try:
            if os.path.exists(temp_thumb):
                os.remove(temp_thumb)
        except:
            pass
            
        return final_image_path
        
    except:
        try:
            if os.path.exists(temp_thumb):
                os.remove(temp_thumb)
        except:
            pass
        return YOUTUBE_IMG_URL
