import sys
html = open('how_it_works_design.html', 'r', encoding='utf-8').read()
start = html.find('id="page-howitworks"')
if start != -1:
    end = html.find('class="footer"', start)
    # Also find methodology page to replace it too
    meth_start = html.find('id="page-methodology"')
    if meth_start != -1:
        meth_end = html.find('class="footer"', meth_start)
        meth_content = html[meth_start-5:meth_end+500]
        with open('extracted_methodology.html', 'w', encoding='utf-8') as f:
            # truncate until </div>
            last_div = meth_content.rfind('</div>')
            f.write(meth_content[:last_div+6])

    content = html[start-5:end+500]
    with open('extracted_howitworks.txt', 'w', encoding='utf-8') as f:
        # truncate until </div>
        last_div = content.rfind('</div>')
        f.write(content[:last_div+6])
else:
    print('not found')
