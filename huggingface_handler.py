# huggingface_handler.py
import requests
import io
import os
from PIL import Image
from dotenv import load_dotenv

load_dotenv(override=True)

def generate_ai_image_hf(prompt):
    """
    Hugging Face Inference API üzerinden ücretsiz olarak görsel üretir.
    Kullanılan Model: stabilityai/stable-diffusion-xl-base-1.0
    """
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError("HF_API_KEY bulunamadı! Lütfen Hugging Face'den ücretsiz bir Access Token alıp .env dosyasına (HF_API_KEY=...) ekleyiniz.")

    # Güncellenmiş Hugging Face Router URL'si
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "inputs": prompt,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Eğer model yükleniyorsa vs. hata dönebilir veya 503 HTTP dönerse
        if response.status_code != 200:
            error_data = response.json()
            if "estimated_time" in error_data:
                raise Exception(f"Model şu anda Hugging Face sunucularında uyanıyor. Lütfen {int(error_data['estimated_time'])} saniye bekleyip tekrar deneyin.")
            else:
                raise Exception(f"API Hatası (Kod: {response.status_code}): {response.text}")

        # Başarılı ise resmi al
        image = Image.open(io.BytesIO(response.content))
        return image
    except requests.exceptions.RequestException as e:
        raise Exception(f"Bağlantı Hatası: {str(e)}")
