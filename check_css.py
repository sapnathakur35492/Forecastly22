import re

with open('how_it_works_design.html', 'r', encoding='utf-8') as f:
    design = f.read()

with open('project/templates/index.html', 'r', encoding='utf-8') as f:
    index = f.read()

# Extract all CSS from the design
css_match = re.search(r'<style>(.*?)</style>', design, re.DOTALL)
if css_match:
    design_css = css_match.group(1)
    
    # We will just append the missing CSS part to index.html's CSS to ensure 100% adherence.
    # First, let's see where the CSS ends in index.html
    style_end = index.find('</style>')
    if style_end != -1:
        # Avoid duplicating everything. We know index.html already has some CSS.
        # But to be safe and 100% compliant with the user's design, we could replace the entire CSS block with the one from the design, 
        # since the design file the user provided contains the complete set of CSS for all pages (Dashboard, builder, etc too).
        pass

# Let's check how long the CSS is in both
print(f"Design CSS len: {len(design_css)}")
index_css_match = re.search(r'<style>(.*?)</style>', index, re.DOTALL)
if index_css_match:
    print(f"Index CSS len: {len(index_css_match.group(1))}")
