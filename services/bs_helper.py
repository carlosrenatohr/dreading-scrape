from bs4 import BeautifulSoup

def get_lecture_pieces(content):
    res = {}

    body = BeautifulSoup(content, 'html.parser')
    res['title'] = body.find('h1').text
    res['date_title'] = body.find('time').text
    res['date_raw'] = body.find('time').attrs['datetime']
    res['lecturas'] = []
    lecturas = body.find_all('div', {'class':"lecturas"})
    for section in body.find_all('section'):
        lectura_content = section.find('div', {'class':'texto_palabra'})
        lectura_content_b = lectura_content.find_all('b')
        lectura_content.b.extract()
        salmo_extract = lectura_content.i.extract().text if lectura_content.i else ''

        lectura_row = {
                'title': section.find('h2').text,
                'content': lectura_content.text,
                'first_line': lectura_content_b[0].text,
            }
        if salmo_extract:
            lectura_row['psalm'] = salmo_extract
        else:
            lectura_row['last_line'] = lectura_content_b[1].text if len(lectura_content_b) > 1 else ''
        res['lecturas'].append(lectura_row)

    return res