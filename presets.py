# presets.py

PLATFORM_PRESETS = {
    "Instagram Kare": {
        "size": (1080, 1080),
        "aspect": "1:1",
        "background": "beyaz veya soft gradient",
        "lighting": "parlak, doğal ışık",
        "style": "minimalist, temiz, modern",
        "description": "Instagram feed için kare format, ürün ortada, beyaz arka plan",
        "icon": "📸"
    },
    "Instagram Story": {
        "size": (1080, 1920),
        "aspect": "9:16",
        "background": "gradient veya sahne",
        "lighting": "dramatik yan ışık",
        "style": "dikey, bold, dikkat çekici",
        "description": "Story formatı, dikey kompozisyon, büyük ürün gösterimi",
        "icon": "📱"
    },
    "E-Ticaret (Amazon/Trendyol)": {
        "size": (2000, 2000),
        "aspect": "1:1",
        "background": "saf beyaz (#FFFFFF)",
        "lighting": "düz, gölgesiz stüdyo ışığı",
        "style": "profesyonel, detaylı, net",
        "description": "Marketplace standartı, tamamen beyaz arka plan, ürün %85 alanı kaplar",
        "icon": "🛒"
    },
    "Pinterest": {
        "size": (1000, 1500),
        "aspect": "2:3",
        "background": "lifestyle sahne, ahşap veya mermer yüzey",
        "lighting": "sıcak, doğal gün ışığı",
        "style": "estetik, yaratıcı, hikaye anlatıcı",
        "description": "Dikey format, yaşam tarzı görseli, ürün kullanım ortamında",
        "icon": "📌"
    },
    "LinkedIn / Kurumsal": {
        "size": (1200, 627),
        "aspect": "16:9",
        "background": "kurumsal, koyu veya marka rengi",
        "lighting": "profesyonel stüdyo",
        "style": "kurumsal, güven veren, sade",
        "description": "Yatay banner formatı, ürün + marka uyumu",
        "icon": "💼"
    },
    "Website Banner": {
        "size": (1920, 600),
        "aspect": "32:10",
        "background": "blur edilmiş ürün ortamı",
        "lighting": "geniş açı, ambient ışık",
        "style": "geniş, sinematik, çarpıcı",
        "description": "Hero banner için geniş format",
        "icon": "🌐"
    }
}

LIGHTING_STYLES = {
    "Stüdyo (Beyaz)": "saf beyaz stüdyo arka planı, eşit dağılmış soft box ışıkları",
    "Doğal Gün Işığı": "pencere kenarı doğal gün ışığı, yumuşak gölgeler",
    "Dramatik": "koyu arka plan, güçlü yan ışık, derin gölgeler",
    "Sıcak Sahne": "sıcak tonlar, kahve dükkanı/ev ortamı, bokeh arka plan",
    "Minimalist": "açık gri zemin, diffused yumuşak ışık, temiz çizgiler",
    "Lüks": "derin siyah veya derin lacivert arka plan, accent ışıklar, premium his"
}