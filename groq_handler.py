# groq_handler.py
# NOT: Groq şu an vision desteklemiyor, metin tabanlı öneri üretir
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

def init_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY bulunamadı!")
    return Groq(api_key=api_key)

def generate_editing_guide(platform_name, platform_preset, lighting_style,
                            product_type="genel ürün", extra_notes=""):
    """
    Groq ile düzenleme rehberi oluştur (görüntü olmadan, metin tabanlı)
    """
    client = init_groq()
    
    prompt = f"""Sen profesyonel bir ürün fotoğrafçısısın.

{product_type} için {platform_name} platformuna uygun fotoğraf düzenleme rehberi yaz.

Platform Detayları:
- Boyut: {platform_preset['size'][0]}x{platform_preset['size'][1]} px  
- Arka Plan: {platform_preset['background']}
- Işık: {lighting_style}
- Stil: {platform_preset['style']}
{f"- Ek Notlar: {extra_notes}" if extra_notes else ""}

Şunları içersin:
1. Kompozisyon kuralları
2. Renk paleti önerileri  
3. Arka plan hazırlama adımları
4. Işık düzeni
5. Son rötuş ipuçları
6. Yaygın hatalar

Türkçe, madde madde, pratik yaz."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def generate_hashtags(platform_name, product_type):
    """Platform için hashtag önerileri"""
    client = init_groq()
    
    prompt = f"""{product_type} için {platform_name} platformunda kullanılacak 
    20 adet Türkçe ve İngilizce hashtag öner. 
    Sadece hashtagleri listele, # işaretiyle başlat."""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content