from bs4 import BeautifulSoup

html = "<div><div class='sidebar'><p>Hello</p></div></div>"
soup = BeautifulSoup(html, "html.parser")

for element in soup.find_all(True):
    if 'sidebar' in element.get('class', []):
        element.decompose()
    else:
        print(element.get('class'))
