import re

html_path = 'how_it_works_design.html'
index_path = r'project\templates\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    source_html = f.read()

with open(index_path, 'r', encoding='utf-8') as f:
    index_html = f.read()

# Extract inner HTML of page-methodology
meth_start = source_html.find('id="page-methodology"')
if meth_start != -1:
    meth_end = source_html.find('class="footer"', meth_start)
    meth_content = source_html[meth_start:meth_end]

    # Extract only inner elements
    hw_hero_start = meth_content.find('<div class="meth-hero">')
    hw_footer = meth_content.find('<div class="footer">')
    if hw_footer != -1:
        meth_inner = meth_content[hw_hero_start:hw_footer]
    else:
        meth_inner = meth_content[hw_hero_start:]

    # Replace inside <section id="meth-sec" style="display:none"> ... </section>
    new_index, count = re.subn(
        r'<section id="meth-sec" style="display:none">.*?</section>',
        f'<section id="meth-sec" style="display:none">\n{meth_inner.strip()}\n        </section>',
        index_html,
        flags=re.DOTALL
    )

    print(f"Replaced meth-sec: {count} times")

    if count > 0:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_index)
        print("index.html method updated successfully!")
    else:
        print("meth-sec not found for replacement.")
else:
    print("Methodology page not found in source.")
