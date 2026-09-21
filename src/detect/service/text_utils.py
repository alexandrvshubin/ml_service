import re

def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.lower().strip()
    text = re.sub("https", '', text)
    text = re.sub("www", '', text)
    text = re.sub(r'[^a-zа-яё0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text