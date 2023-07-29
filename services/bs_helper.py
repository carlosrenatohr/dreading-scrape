from bs4 import BeautifulSoup

def get_lecture_pieces(content):
    res = {}
    body = BeautifulSoup(content, 'html.parser')
    res['title'] = body.find('h1').text
    res['date_title'] = body.find('time').text
    res['date_raw'] = body.find('time').attrs['datetime']
    res['lecturas'] = []
    lecturas = body.find_all('div', {'class':"lecturas"})
    # Loop through each section which contains a reading
    for section in body.find_all('section'):
        # Get the content of the reading to scrape it
        lectura_content = section.find('div', {'class':'texto_palabra'})
        lectura_content_b = lectura_content.find_all('b')
        # Remove the <script> tags if they are inserted into the reading, no needed
        scripts_to_remove = lectura_content.script
        if scripts_to_remove:
            scripts_to_remove.extract()
        # If the reading has a <i> tag, it means it has a psalm
        salmo_extract = lectura_content.i.extract().text if lectura_content.i else ''
        # If the reading has <b> tags, it means the reading is not empty and has a title
        # otherwise it's empty and we don't want to add it to the database
        if lectura_content_b:
            # Remove the <b> tags to get the text only
            lectura_content.b.extract()
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