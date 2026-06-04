import re 

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = text.replace("\u007f", " ")
    return text