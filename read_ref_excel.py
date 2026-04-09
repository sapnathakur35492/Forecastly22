with open(r"c:\Users\Santosh\Desktop\market\project\media\reports\REP-04256_enterprise.xls", 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

import re

ws_names = re.findall(r'<Worksheet ss:Name="([^"]*)"', content)
print("Sheet names:", ws_names)
print("Total length:", len(content), "bytes")

# Check each worksheet for structure
worksheets = re.findall(r'<Worksheet ss:Name="([^"]*)"[^>]*>(.*?)</Worksheet>', content, re.DOTALL)
for name, ws_content in worksheets:
    rows = re.findall(r'<Row[^>]*>(.*?)</Row>', ws_content, re.DOTALL)
    title_rows = []
    for row in rows:
        cells = re.findall(r'<Data[^>]*>(.*?)</Data>', row)
        style_ids = re.findall(r'ss:StyleID="([^"]*)"', row)
        if 'title' in style_ids:
            for c in cells:
                if len(c) > 5:
                    title_rows.append(c[:80])
    print("\n=== %s (%d rows, %d title tables) ===" % (name, len(rows), len(title_rows)))
    for t in title_rows:
        print("  TABLE:", t)
