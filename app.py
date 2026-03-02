# app.py
import streamlit as st
from PIL import Image
import io
import json
import os
from dotenv import load_dotenv

from presets import PLATFORM_PRESETS, LIGHTING_STYLES
from image_processor import (
    adjust_brightness_contrast, sharpen_image, 
    resize_for_platform, auto_enhance, get_image_stats,
    add_white_background, add_gradient_background, apply_vignette
)
from gemini_handler import (
    analyze_product, generate_product_prompt, enhance_image_description
)
from groq_handler import generate_editing_guide, generate_hashtags

load_dotenv()

# ─── SAYFA AYARLARI ───────────────────────────────────────────────
st.set_page_config(
    page_title="📸 AI Ürün Fotoğrafçısı",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem; font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
        border-radius: 12px; padding: 15px; text-align: center;
        margin: 5px;
    }
    .platform-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border-radius: 20px;
        padding: 5px 15px; font-size: 0.85rem; font-weight: bold;
    }
    .success-box {
        background: #f0fff4; border: 2px solid #68d391;
        border-radius: 12px; padding: 15px; margin: 10px 0;
    }
    .warning-box {
        background: #fffaf0; border: 2px solid #f6ad55;
        border-radius: 12px; padding: 15px; margin: 10px 0;
    }
    div[data-testid="stTabs"] button {
        font-size: 1rem; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── BAŞLIK ───────────────────────────────────────────────────────
st.markdown('<div class="main-title">📸 AI Ürün Fotoğrafçısı</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ürün fotoğraflarını Instagram, E-Ticaret ve daha fazlası için optimize edin</div>', 
            unsafe_allow_html=True)

st.divider()

# ─── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # AI Model seçimi
    st.subheader("🤖 AI Model")
    ai_model = st.selectbox(
        "Kullanılacak AI",
        ["🔵 Gemini (Görsel Analiz)", "🟠 Groq (Metin Rehberi)"],
        help="Gemini fotoğrafı görsel olarak analiz eder. Groq metin tabanlı rehber üretir."
    )
    
    st.divider()
    
    # Platform seçimi
    st.subheader("🎯 Platform")
    platform_name = st.selectbox(
        "Hedef Platform",
        list(PLATFORM_PRESETS.keys()),
        format_func=lambda x: f"{PLATFORM_PRESETS[x]['icon']} {x}"
    )
    preset = PLATFORM_PRESETS[platform_name]
    
    # Platform bilgisi
    with st.expander("📋 Platform Detayları"):
        st.markdown(f"**Boyut:** {preset['size'][0]}x{preset['size'][1]} px")
        st.markdown(f"**Oran:** {preset['aspect']}")
        st.markdown(f"**Stil:** {preset['style']}")
        st.markdown(f"**Açıklama:** {preset['description']}")
    
    st.divider()
    
    # Işık seçimi
    st.subheader("💡 Işık Stili")
    lighting_name = st.selectbox("Işık Tipi", list(LIGHTING_STYLES.keys()))
    lighting_desc = LIGHTING_STYLES[lighting_name]
    
    st.divider()
    
    # Görüntü ayarları
    st.subheader("🎨 Görüntü Ayarları")
    brightness = st.slider("☀️ Parlaklık", 0.5, 2.0, 1.0, 0.1)
    contrast = st.slider("🌗 Kontrast", 0.5, 2.0, 1.0, 0.1)
    sharpen = st.checkbox("✨ Netleştir", value=True)
    auto_enh = st.checkbox("🪄 Otomatik İyileştir", value=False)
    
    st.divider()
    
    # Arka plan
    st.subheader("🖼️ Arka Plan")
    bg_option = st.selectbox(
        "Arka Plan Tipi",
        ["Orijinal", "Beyaz", "Açık Gradient", "Koyu Gradient"]
    )
    
    st.divider()
    
    # Ek bilgiler
    st.subheader("📝 Ek Bilgiler")
    product_name = st.text_input("Ürün Adı (opsiyonel)", placeholder="Örn: Kırmızı Çanta")
    extra_notes = st.text_area("Özel İstekler", placeholder="Örn: Lüks görünüm, koyu tema istiyorum...", height=80)

# ─── ANA ALAN ─────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📤 Fotoğraf Yükle", "🔍 Analiz & Düzenleme", "📊 Sonuç & İndir"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: FOTOĞRAF YÜKLEME
# ═══════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Dosya Yükle")
        uploaded_file = st.file_uploader(
            "Ürün fotoğrafınızı seçin",
            type=["jpg", "jpeg", "png", "webp"],
            help="Maksimum 200MB, JPG/PNG/WEBP formatları"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.session_state["original_image"] = image
            st.success(f"✅ Fotoğraf yüklendi: {uploaded_file.name}")
    
    with col2:
        st.subheader("📷 Kamera ile Çek")
        camera_photo = st.camera_input("Kameranızla fotoğraf çekin")
        
        if camera_photo:
            image = Image.open(camera_photo)
            st.session_state["original_image"] = image
            st.success("✅ Kamera fotoğrafı alındı!")
    
    # Fotoğraf önizleme
    if "original_image" in st.session_state:
        st.divider()
        st.subheader("🖼️ Orijinal Fotoğraf")
        
        img = st.session_state["original_image"]
        col_img, col_stats = st.columns([2, 1])
        
        with col_img:
            st.image(img, caption="Yüklenen Fotoğraf", use_column_width=True)
        
        with col_stats:
            stats = get_image_stats(img)
            st.markdown("**📊 Fotoğraf İstatistikleri**")
            
            st.markdown(f"""
            <div class="stat-card">
                <b>Boyut</b><br>{stats['width']} × {stats['height']} px
            </div>
            <div class="stat-card">
                <b>Parlaklık</b><br>{stats['brightness']:.1f} / 255
            </div>
            <div class="stat-card">
                <b>Kontrast</b><br>{stats['contrast']:.1f}
            </div>
            <div class="stat-card">
                <b>Netlik Skoru</b><br>{stats['sharpness']:.0f}
            </div>
            """, unsafe_allow_html=True)
            
            # Kalite değerlendirmesi
            if stats['brightness'] < 80:
                st.warning("⚠️ Fotoğraf çok karanlık!")
            elif stats['brightness'] > 220:
                st.warning("⚠️ Fotoğraf çok parlak!")
            else:
                st.success("✅ Işık seviyesi iyi")
            
            if stats['sharpness'] < 100:
                st.warning("⚠️ Fotoğraf bulanık olabilir")
            else:
                st.success("✅ Netlik yeterli")

# ═══════════════════════════════════════════════════════════════════
# TAB 2: ANALİZ & DÜZENLEME
# ═══════════════════════════════════════════════════════════════════
with tab2:
    if "original_image" not in st.session_state:
        st.info("👆 Önce Tab 1'den bir fotoğraf yükleyin")
    else:
        img = st.session_state["original_image"]
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader(f"🎯 Hedef: {platform_name}")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea22, #764ba222); 
                        border-radius: 12px; padding: 15px; border-left: 4px solid #667eea;">
                <b>Platform:</b> {preset['icon']} {platform_name}<br>
                <b>Boyut:</b> {preset['size'][0]}×{preset['size'][1]} px<br>
                <b>Arka Plan:</b> {preset['background']}<br>
                <b>Işık:</b> {lighting_name}<br>
                <b>Stil:</b> {preset['style']}
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            st.subheader("🤖 AI Analizi")
            
            if st.button("🔍 AI ile Analiz Et", type="primary", use_container_width=True):
                with st.spinner("AI analiz yapıyor..."):
                    try:
                        if "Gemini" in ai_model:
                            analysis = enhance_image_description(img, platform_name)
                            st.session_state["ai_analysis"] = analysis
                        else:
                            # Groq metin tabanlı
                            analysis = generate_editing_guide(
                                platform_name, preset, lighting_desc,
                                product_name or "genel ürün", extra_notes
                            )
                            st.session_state["ai_analysis"] = analysis
                        st.success("✅ Analiz tamamlandı!")
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
        
        # AI Analiz sonucu
        if "ai_analysis" in st.session_state:
            with st.expander("📋 AI Analiz Raporu", expanded=True):
                st.markdown(st.session_state["ai_analysis"])
        
        st.divider()
        
        # DÜZENLEME VE ÖNIZLEME
        st.subheader("✏️ Düzenle & Önizle")
        
        if st.button("🪄 Düzenlemeleri Uygula & Önizle", type="primary", use_container_width=True):
            with st.spinner("Görüntü işleniyor..."):
                processed = img.copy()
                
                # 1. Otomatik iyileştirme
                if auto_enh:
                    processed = auto_enhance(processed)
                
                # 2. Parlaklık/Kontrast
                processed = adjust_brightness_contrast(processed, brightness, contrast)
                
                # 3. Netleştirme
                if sharpen:
                    processed = sharpen_image(processed)
                
                # 4. Arka plan
                if bg_option == "Beyaz":
                    processed = add_white_background(processed)
                elif bg_option == "Açık Gradient":
                    processed = add_gradient_background(processed, (255,255,255), (230,235,245))
                elif bg_option == "Koyu Gradient":
                    processed = add_gradient_background(processed, (50,50,70), (20,20,30))
                
                # 5. Platform boyutuna göre yeniden boyutlandır
                resized = resize_for_platform(processed, preset["size"])
                
                st.session_state["processed_image"] = resized
                st.success("✅ Düzenleme tamamlandı!")
        
        # Karşılaştırma görünümü
        if "processed_image" in st.session_state:
            st.subheader("👁️ Karşılaştırma")
            col_orig, col_proc = st.columns(2)
            
            with col_orig:
                st.markdown("**⬅️ Orijinal**")
                st.image(img, use_column_width=True)
            
            with col_proc:
                st.markdown(f"**➡️ {platform_name} için Düzenlenmiş**")
                st.image(st.session_state["processed_image"], use_column_width=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 3: SONUÇ & İNDİR
# ═══════════════════════════════════════════════════════════════════
with tab3:
    if "processed_image" not in st.session_state:
        st.info("👆 Önce Tab 2'den düzenleme yapın")
    else:
        processed = st.session_state["processed_image"]
        
        st.subheader("✅ Sonuç Fotoğraf")
        st.image(processed, caption=f"{platform_name} için optimize edildi", use_column_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        # İndirme butonları
        def get_download_bytes(img, format="JPEG", quality=95):
            buf = io.BytesIO()
            if format == "PNG":
                img.save(buf, format="PNG")
            else:
                img.convert("RGB").save(buf, format="JPEG", quality=quality)
            return buf.getvalue()
        
        with col1:
            st.download_button(
                label="⬇️ JPG İndir (Yüksek)",
                data=get_download_bytes(processed, "JPEG", 95),
                file_name=f"urun_{platform_name.replace(' ', '_')}_HQ.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                label="⬇️ JPG İndir (Web)",
                data=get_download_bytes(processed, "JPEG", 75),
                file_name=f"urun_{platform_name.replace(' ', '_')}_web.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
        
        with col3:
            st.download_button(
                label="⬇️ PNG İndir",
                data=get_download_bytes(processed, "PNG"),
                file_name=f"urun_{platform_name.replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True
            )
        
        st.divider()
        
        # Hashtag önerileri
        st.subheader("# Hashtag Önerileri")
        if st.button("🏷️ Hashtag Üret (Groq)", use_container_width=True):
            with st.spinner("Hashtagler oluşturuluyor..."):
                try:
                    hashtags = generate_hashtags(platform_name, product_name or "ürün")
                    st.session_state["hashtags"] = hashtags
                except Exception as e:
                    st.error(f"❌ {str(e)}")
        
        if "hashtags" in st.session_state:
            st.code(st.session_state["hashtags"])
            st.download_button(
                "📋 Hashtagleri Kopyala",
                data=st.session_state["hashtags"],
                file_name="hashtags.txt",
                mime="text/plain"
            )
        
        st.divider()
        
        # Prompt üretimi
        st.subheader("🎨 Image Generation Prompt")
        st.caption("Bu promptu Midjourney, DALL-E veya başka araçlarda kullanabilirsiniz")
        
        if st.button("📝 Prompt Üret (Gemini)", use_container_width=True):
            with st.spinner("Prompt oluşturuluyor..."):
                try:
                    orig_img = st.session_state["original_image"]
                    result = generate_product_prompt(
                        orig_img, preset, lighting_desc, 
                        extra_notes, product_name
                    )
                    st.session_state["generated_prompt"] = result
                except Exception as e:
                    st.error(f"❌ {str(e)}")
        
        if "generated_prompt" in st.session_state:
            st.markdown(st.session_state["generated_prompt"])