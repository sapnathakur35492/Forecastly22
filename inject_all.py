import re

def update_index():
    with open('how_it_works_design.html', 'r', encoding='utf-8') as f:
        design = f.read()
    
    with open('project/templates/index.html', 'r', encoding='utf-8') as f:
        index = f.read()

    # We want to replace the `how-sec` section in index.html with the `page-howitworks` content from the design
    # BUT, we should keep the `<section class="how" id="how-sec">` wrapper so the JS routing continues to work properly.
    
    # 1. Extract How It Works
    how_match = re.search(r'<div id="page-howitworks" class="page">(.*?)</div>\s*<!-- PAGE 2: BUILDER -->', design, re.DOTALL)
    how_content = how_match.group(1).strip() if how_match else ""
    # Remove the footer from how_content because index.html likely already has one, or it's fine. 
    # Actually, the user's design puts the footer inside each page. Let's keep it exactly as the design!

    # Replace in index
    index = re.sub(
        r'<section class="how" id="how-sec">.*?</section>',
        f'<section class="how" id="how-sec" style="display:none">\n{how_content}\n</section>',
        index,
        flags=re.DOTALL
    )

    # 2. Extract Methodology
    meth_match = re.search(r'<div id="page-methodology" class="page">(.*?)</div>\s*<!-- PAGE 2: BUILDER -->', design, re.DOTALL)
    if not meth_match:
        # In the actual file it might be before builder or something. Let's find it.
        meth_match = re.search(r'<div id="page-methodology" class="page">(.*?)(?:</div>\s*<!-- PAGE |</div>\s*<div id="page-)', design, re.DOTALL)
        if not meth_match:
             meth_start = design.find('<div id="page-methodology"')
             meth_end = design.find('<div id="page-builder"', meth_start)
             if meth_start != -1 and meth_end != -1:
                 meth_content = design[meth_start:meth_end]
                 # Remove the outer div
                 meth_content = re.sub(r'^<div.*?class="page">', '', meth_content, count=1).strip()
                 meth_content = meth_content[:meth_content.rfind('</div>')].strip()
             else:
                 meth_content = ""
        else:
             meth_content = meth_match.group(1).strip()
    else:
        meth_content = meth_match.group(1).strip()

    # Replace in index
    # Note: index.html has `<section id="meth-sec" style="display:none">`
    index = re.sub(
        r'<section id="meth-sec" style="display:none">.*?</section>',
        f'<section id="meth-sec" style="display:none">\n{meth_content}\n</section>',
        index,
        flags=re.DOTALL
    )

    # 3. Ensure CSS is fully incorporated. Let's extract all CSS from design and put it in index (replace index.css basically)
    # The user says "pure page ka code yeah hai". This implies the design CSS is what they want.
    # But wait, index.html has a lot of custom CSS. 
    css_match = re.search(r'<style>(.*?)</style>', design, re.DOTALL)
    design_css = css_match.group(1) if css_match else ""

    # Instead of replacing, just inject missing classes if any. But I already did in previous steps. 
    # Let me just run this and see.
    with open('project/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index)
    print("HTML Content integrated.")

update_index()
