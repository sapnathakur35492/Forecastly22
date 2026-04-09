import sys
from pypdf import PdfReader

def extract(pdf_path, out_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
