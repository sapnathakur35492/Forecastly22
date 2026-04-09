import docx
import os

doc_path = r'c:\Users\Santosh\Desktop\market\How it Works Paeg UI design.docx'
output_path = r'c:\Users\Santosh\Desktop\market\extracted_code.html'

if os.path.exists(doc_path):
    doc = docx.Document(doc_path)
    content = '\n'.join([p.text for p in doc.paragraphs])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully extracted {len(content)} characters to {output_path}")
else:
    print(f"File not found: {doc_path}")
