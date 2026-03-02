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
    analyze_product, generate_product_prompt, enhance_image_description, generate_ai_image
)
from huggingface_handler import generate_ai_image_hf
from groq_handler import generate_editing_guide, generate_hashtags

# Zorunlu olarak en güncel .env dosyasını yeniden yüklemesine zorluyoruz
load_dotenv(override=True)

# ─── SAYFA AYARLARI ───────────────────────────────────────────────
st.set_page_config(
    page_title="📸 AI Ürün Fotoğrafçısı (Generative)",
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
    .ai-magic-btn {
        background: linear-gradient(90deg, #FFB75E 0%, #ED8F03 100%);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ─── BAŞLIK ───────────────────────────────────────────────────────
st.markdown('<div class="main-title">✨ AI Gen. Ürün Fotoğrafçısı</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="subtitle">Elinizdeki fotoğrafı profesyonel stüdyo kalitesinde yapay zeka ile baştan yaratın</div>', 
            unsafe_allow_html=True)

st.divider()

# ─── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Üretim Ayarları")
    
    # Platform seçimi
    st.subheader("🎯 Hedef Platform ve Boyut")
    platform_name = st.selectbox(
        "Kullanılacak Alan",
        list(PLATFORM_PRESETS.keys()),
        format_func=lambda x: f"{PLATFORM_PRESETS[x]['icon']} {x}"
    )
    preset = PLATFORM_PRESETS[platform_name]
    
    # Platform bilgisi
    with st.expander("📋 Platform Detayları", expanded=True):
        st.markdown(f"**Oran:** {preset['aspect']}")
        st.markdown(f"**Stil:** {preset['style']}")
        st.markdown(f"**Arka Plan:** {preset['background']}")
    
    st.divider()
    
    # Manuel Görüntü Ayarları (Filtreler)
    st.subheader("🎨 Manuel Görüntü Ayarları")
    brightness = st.slider("☀️ Parlaklık", 0.5, 2.0, 1.0, 0.1)
    contrast = st.slider("🌗 Kontrast", 0.5, 2.0, 1.0, 0.1)
    sharpen = st.checkbox("✨ Netleştir", value=False)
    auto_enh = st.checkbox("🪄 Otomatik İyileştir", value=False)
    
    st.divider()
    
    # Arka plan
    st.subheader("🖼️ Arka Plan")
    bg_option = st.selectbox(
        "Arka Plan Tipi",
        ["Orijinal", "Beyaz", "Açık Gradient", "Koyu Gradient"]
    )
    
    st.divider()
    
    # Işık seçimi
    st.subheader("💡 Konsept (Işık & Atmosfer)")
    lighting_name = st.selectbox("Işık Tipi", list(LIGHTING_STYLES.keys()))
    lighting_desc = LIGHTING_STYLES[lighting_name]
    
    st.divider()
    
    # Ek bilgiler
    st.subheader("📝 Yapay Zeka Ek Detaylar")
    product_name = st.text_input("Ürünün Adı/Cinsi", placeholder="Örn: Siyah Erkek Deri Ayakkabı")
    extra_notes = st.text_area("Yapay Zekaya Özel İstek", placeholder="Örn: Fotoğraf lüks görünsün, zemin mermer olsun", height=80)

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
            st.subheader("🛠️ Düzenleme Seçenekleri")
            edit_tab1, edit_tab2 = st.tabs(["🖌️ Manuel Düzenleme (Filtreler)", "🤖 Yapay Zeka İle Üret (Hugging Face)"])

            with edit_tab1:
                st.info("Orijinal fotoğrafınızı klasik fotoğraf filtreleriyle (Parlaklık, Kontrast, Keskinlik vs.) düzenler.")
                if st.button("🪄 Manuel Düzenlemeyi Uygula", type="primary", use_container_width=True):
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
                        st.success("✅ Manuel Düzenleme tamamlandı!")

            with edit_tab2:
                st.info("Bu işlem, tamamen ÜCRETSİZ Hugging Face (Stable Diffusion) API'sini kullanarak fotoğrafı yeniden resmeder.")

                if st.button("✨ Yapay Zeka ile Yeniden Çiz (Hugging Face)", type="primary", use_container_width=True):
                    with st.spinner("⏳ Adım 1: Fotoğraf analiz ediliyor ve prompt yazılıyor..."):
                        try:
                            # İlk olarak Gemini ile profesyonel fotoğraf promptu oluşturuyoruz (Gemini hala ücretsiz okuma desteği veriyor)
                            # Lighting default since we removed it from sidebar
                            generated_prompt = generate_product_prompt(
                                img, preset, lighting_desc, 
                                extra_notes, product_name
                            )
                            st.session_state["ai_prompt"] = generated_prompt
                            
                            st.success("✅ Analiz Tamamlandı. Görüntü üretimi başlıyor...")
                        
                        except Exception as e:
                            st.error(f"❌ Analiz Hatası: {str(e)}")
                            generated_prompt = None

                    if generated_prompt:
                        with st.spinner("⏳ Adım 2: Hugging Face yeni resmi çiziyor (Bu biraz vakit alabilir)..."):
                            try:
                                # Prompt'un sonundaki "IMAGE_PROMPT:" kısmını ayıklıyoruz
                                if "IMAGE_PROMPT:" in generated_prompt:
                                    actual_prompt = generated_prompt.split("IMAGE_PROMPT:")[1].strip()
                                else:
                                    actual_prompt = generated_prompt 
                                
                                st.session_state["image_prompt_text"] = actual_prompt

                                # generate via hugging face
                                new_image = generate_ai_image_hf(actual_prompt)
                                
                                # Platform boyutuna getir
                                new_image_resized = resize_for_platform(new_image, preset["size"], keep_ratio=False)
                                
                                # İndirme kısmında kullanılabilmesi için atıyoruz
                                st.session_state["processed_image"] = new_image_resized
                                st.success("🎉 Mükemmel! Stable Diffusion ile yepyeni bir görsel üretildi!")
                            
                            except Exception as e:
                                st.error(f"❌ Üretim Hatası (Hugging Face): {str(e)}")

        # Üretilen Prompt Gösterimi
        if "ai_prompt" in st.session_state:
            with st.expander("📋 Son Üretilen AI Promptu (Gizli Gönderilen)", expanded=False):
                st.markdown(st.session_state["ai_prompt"])
                st.write("---")
                st.write("**Aktif Prompt:**", st.session_state.get("image_prompt_text", ""))
        
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