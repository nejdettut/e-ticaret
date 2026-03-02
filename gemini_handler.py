# gemini_handler.py
import google.generativeai as genai
import base64
import io
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

def init_gemini():
    """Gemini API'yi başlat"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı! .env dosyasını kontrol edin.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

def image_to_base64(pil_image):
    """PIL Image'ı base64'e çevir"""
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG", quality=95)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def analyze_product(pil_image):
    """Ürünü analiz et"""
    model = init_gemini()
    
    prompt = """Bu ürün fotoğrafını analiz et ve JSON formatında şunları söyle:
    - product_name: Ürün adı
    - product_type: Ürün kategorisi
    - main_color: Ana renk
    - background_quality: Mevcut arka plan kalitesi (kötü/orta/iyi)
    - lighting_quality: Işık kalitesi (kötü/orta/iyi)  
    - suggestions: 3 kısa öneri listesi
    
    Sadece JSON döndür, başka bir şey yazma."""
    
    img_data = {
        "mime_type": "image/jpeg",
        "data": image_to_base64(pil_image)
    }
    
    response = model.generate_content([prompt, img_data])
    return response.text

def generate_product_prompt(pil_image, platform_preset, lighting_style, 
                            extra_notes="", product_name=""):
    """
    Gemini ile ürün fotoğrafı için detaylı prompt oluştur
    Bu prompt DALL-E veya başka bir image gen API'ye gönderilebilir
    Ya da Gemini'nin görsel açıklaması olarak kullanılır
    """
    model = init_gemini()
    
    prompt = f"""Sen profesyonel bir ürün fotoğrafçısı ve AI görsel direktörüsün.
    
Bu ürün fotoğrafını analiz et ve aşağıdaki platforma uygun olarak nasıl yeniden çekileceğini/düzenleneceğini açıkla.

PLATFORM: {platform_preset['description']}
BOYUT: {platform_preset['size'][0]}x{platform_preset['size'][1]} px
ARKA PLAN: {platform_preset['background']}
IŞIK STİLİ: {lighting_style}
STİL: {platform_preset['style']}
{f"ÜRÜN ADI: {product_name}" if product_name else ""}
{f"EK NOTLAR: {extra_notes}" if extra_notes else ""}

Şunları yap:
1. Mevcut fotoğrafın güçlü ve zayıf yönlerini belirt
2. Platform için ideal kompozisyonu açıkla  
3. Arka plan önerisini detaylandır
4. Işık düzenlemesini açıkla
5. Renk ve ton ayarlamalarını öner
6. Genel Türkçe açıklama yap

Son olarak şu formatta IMAGE_PROMPT yaz (İngilizce, image generation için):
IMAGE_PROMPT: [product] on [background], [lighting], [style], professional product photography, 
[platform] format, high quality, commercial photography"""

    img_data = {
        "mime_type": "image/jpeg", 
        "data": image_to_base64(pil_image)
    }
    
    response = model.generate_content([prompt, img_data])
    return response.text

def enhance_image_description(pil_image, platform_name):
    """Görüntüyü analiz edip düzenleme önerileri sun"""
    model = init_gemini()
    
    prompt = f"""Bu ürün fotoğrafına bak. {platform_name} platformu için optimize etmem gerekiyor.
    
Bana şunları söyle (Türkçe):
1. **Ürün Analizi**: Ne görüyorsun?
2. **Mevcut Sorunlar**: Fotoğrafın zayıf noktaları neler?
3. **Platform Uyumu**: {platform_name} için bu fotoğraf uygun mu?
4. **Düzenleme Adımları**: Adım adım ne yapmalıyım?
5. **Profesyonel İpuçları**: Bu tür ürün için özel ipuçları

Emoji kullan, samimi ve pratik ol."""

    img_data = {
        "mime_type": "image/jpeg",
        "data": image_to_base64(pil_image)
    }
    
    response = model.generate_content([prompt, img_data])
    return response.text