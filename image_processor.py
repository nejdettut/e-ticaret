# image_processor.py
import cv2
import numpy as np
from PIL import Image
import io

def pil_to_cv2(pil_image):
    """PIL → OpenCV"""
    img_array = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv2_image):
    """OpenCV → PIL"""
    rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def remove_background_simple(pil_image):
    """
    Basit arka plan temizleme (beyaz arka plan için)
    Gerçek projede rembg kütüphanesi kullanılabilir
    """
    img = pil_to_cv2(pil_image)
    
    # GrabCut ile arka plan segmentasyonu
    mask = np.zeros(img.shape[:2], np.uint8)
    h, w = img.shape[:2]
    rect = (10, 10, w-10, h-10)
    
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")
    
    result = img * mask2[:, :, np.newaxis]
    return cv2_to_pil(result)

def add_white_background(pil_image):
    """Beyaz arka plan ekle"""
    background = Image.new("RGB", pil_image.size, (255, 255, 255))
    if pil_image.mode == "RGBA":
        background.paste(pil_image, mask=pil_image.split()[3])
    else:
        background.paste(pil_image)
    return background

def adjust_brightness_contrast(pil_image, brightness=1.0, contrast=1.0):
    """Parlaklık ve kontrast ayarı"""
    img = pil_to_cv2(pil_image)
    
    # Kontrast ve parlaklık
    adjusted = cv2.convertScaleAbs(img, alpha=contrast, beta=(brightness-1)*100)
    return cv2_to_pil(adjusted)

def sharpen_image(pil_image):
    """Görüntü netleştirme"""
    img = pil_to_cv2(pil_image)
    # Daha yumuşak bir keskinleştirme matrisi
    kernel = np.array([[0, -0.5, 0],
                       [-0.5, 3, -0.5],
                       [0, -0.5, 0]])
    sharpened = cv2.filter2D(img, -1, kernel)
    return cv2_to_pil(sharpened)

def resize_for_platform(pil_image, target_size, keep_ratio=True):
    """Platform boyutuna göre yeniden boyutlandır"""
    if keep_ratio:
        img_w, img_h = pil_image.size
        ratio = min(target_size[0] / img_w, target_size[1] / img_h) * 0.98
        new_size = (int(img_w * ratio), int(img_h * ratio))
        
        # Eğer resmi büyütüyorsak BICUBIC, küçültüyorsak LANCZOS daha iyi sonuç verebilir
        resample_method = Image.Resampling.BICUBIC if ratio > 1.0 else Image.Resampling.LANCZOS
        resized_img = pil_image.resize(new_size, resample_method)
        
        # Arka plan oluştur ve ortala
        background = Image.new("RGB", target_size, (255, 255, 255))
        offset = ((target_size[0] - new_size[0]) // 2,
                  (target_size[1] - new_size[1]) // 2)
        background.paste(resized_img, offset)
        return background
    else:
        return pil_image.resize(target_size, Image.Resampling.LANCZOS)

def apply_vignette(pil_image, strength=0.5):
    """Vinyet efekti (kenarları karartma)"""
    img = pil_to_cv2(pil_image)
    h, w = img.shape[:2]
    
    X = cv2.getGaussianKernel(w, w * strength)
    Y = cv2.getGaussianKernel(h, h * strength)
    kernel = Y * X.T
    mask = kernel / kernel.max()
    
    vignette = np.copy(img).astype(float)
    for i in range(3):
        vignette[:, :, i] = vignette[:, :, i] * mask
    
    return cv2_to_pil(vignette.astype(np.uint8))

def add_gradient_background(pil_image, color1=(255,255,255), color2=(240,240,240)):
    """Gradient arka plan ekle"""
    w, h = pil_image.size
    gradient = Image.new("RGB", (w, h))
    
    for y in range(h):
        ratio = y / h
        r = int(color1[0] * (1-ratio) + color2[0] * ratio)
        g = int(color1[1] * (1-ratio) + color2[1] * ratio)
        b = int(color1[2] * (1-ratio) + color2[2] * ratio)
        for x in range(w):
            gradient.putpixel((x, y), (r, g, b))
    
    if pil_image.mode == "RGBA":
        gradient.paste(pil_image, mask=pil_image.split()[3])
    else:
        gradient.paste(pil_image)
    return gradient

def get_image_stats(pil_image):
    """Görüntü istatistikleri"""
    img = pil_to_cv2(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return {
        "brightness": float(np.mean(gray)),
        "contrast": float(np.std(gray)),
        "width": pil_image.size[0],
        "height": pil_image.size[1],
        "sharpness": float(cv2.Laplacian(gray, cv2.CV_64F).var())
    }

def auto_enhance(pil_image):
    """Otomatik iyileştirme pipeline"""
    img = pil_to_cv2(pil_image)
    
    # 1. Histogram eşitleme (CLAHE)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 2. Hafif keskinleştirme
    kernel = np.array([[0,-0.5,0],[-0.5,3,-0.5],[0,-0.5,0]])
    enhanced = cv2.filter2D(enhanced, -1, kernel)
    
    # 3. Denoise (Daha hafif)
    enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 3, 3, 7, 21)
    
    return cv2_to_pil(enhanced)