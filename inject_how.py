import re

html_path = 'how_it_works_design.html'
index_path = r'project\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    source_html = f.read()

with open(index_path, 'r', encoding='utf-8') as f:
    index_html = f.read()

# Extract inner HTML of page-howitworks
how_start = source_html.find('id="page-howitworks"')
how_end = source_html.find('class="footer"', how_start)
how_content = source_html[how_start:how_end]

# Extract only inner elements
inner_match = re.search(r'<div class="hiw-hero">.*?(?=</div>\s*$|<!-- PAGE)', how_content, re.DOTALL)
if inner_match:
    how_inner = inner_match.group(0)
else:
    # fallback, manually isolate
    hw_hero_start = how_content.find('<div class="hiw-hero">')
    hw_footer = how_content.find('<div class="footer">')
    if hw_footer != -1:
        how_inner = how_content[hw_hero_start:hw_footer]
    else:
        how_inner = how_content[hw_hero_start:]

# Replace inside <section class="how" id="how-sec">
new_index, count = re.subn(
    r'<section class="how" id="how-sec">.*?</section>',
    f'<section class="how" id="how-sec">\n{how_inner.strip()}\n        </section>',
    index_html,
    flags=re.DOTALL
)

print(f"Replaced how-sec: {count} times")

if count == 0:
    print("Failed to replace!")
else:
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_index)
    print("index.html updated successfully!")
