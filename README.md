# e-ticaret

E-Ticaret ürün görsellerini optimize eden, Gemini ve Hugging Face destekli yapay zeka fotoğraf stüdyosu.

## Kurulum
1. `python -m venv .venv`
2. `.\.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `.env` dosyası oluşturup API anahtarlarınızı (`GEMINI_API_KEY`, `GROQ_API_KEY`, `HF_API_KEY`) ekleyin.
5. `streamlit run app.py`