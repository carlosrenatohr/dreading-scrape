from bs4 import BeautifulSoup

def get_lecture_pieces(content):
    if not content:
        return None
    body = BeautifulSoup(content, 'html.parser')
    title_el = body.find('h1')
    time_el = body.find('time')
    # Some dates (e.g. future days with no reading published yet) return a page
    # without the title/time markers; treat those as "nothing to store".
    if not title_el or not time_el or not time_el.has_attr('datetime'):
        return None
    res = {}
    res['title'] = title_el.text
    res['date_title'] = time_el.text
    res['date_raw'] = time_el.attrs['datetime']
    res['lecturas'] = []
    # Loop through each section which contains a reading
    for section in body.find_all('section'):
        # Get the content of the reading to scrape it
        lectura_content = section.find('div', {'class':'texto_palabra'})
        # Skip nav/footer/other sections that hold no reading body
        if not lectura_content:
            continue
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