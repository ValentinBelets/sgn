with open('detail_page.html', encoding='utf-8') as f:
    content = f.read()

start = content.find('id="block-content"')
if start != -1:
    print(content[start:start+5000])
else:
    print("Not found")
