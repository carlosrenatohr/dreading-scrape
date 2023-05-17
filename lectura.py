import pprint
import datetime
import requests
from bs4 import BeautifulSoup

import db
import db_cache as redis

db.connect()
r_client = redis.connect()

readings_table_name = 'readings'
# readings_table = db.get_collection('readings')
TODAY = datetime.datetime.now().strftime("%Y-%m-%d")

URL = 'https://www.ciudadredonda.org/calendario-lecturas/evangelio-del-dia/?f=2023-05-17'
URL = 'https://www.ciudadredonda.org/calendario-lecturas/evangelio-del-dia/hoy'

def request_web_content():
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        return response.text
    
    return None
    

def create_html_local_file(content):
    try:
        with open('lectura.html', 'w') as file:
            file.write(content)
    except:
        pass


def get_html_local_file():
    content = None
    
    try:
        with open('lectura.html', 'r') as file:
            content = file.read()
    except:
        pass
    
    return content


def get_html_content():
    content = get_html_local_file()
    
    if content:
        return content

    content = request_web_content()
    create_html_local_file(content)

    return content


def get_pieces_of_content(content):
    res = {}

    body = BeautifulSoup(content, 'html.parser')
    res['title'] = body.find('h1').text
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
            lectura_row['last_line'] = lectura_content_b[1].text
        res['lecturas'].append(lectura_row)

    return res



def main():
    content = get_html_content()
    res = get_pieces_of_content(content)
    cache_id = redis.post_lectura(TODAY, res)
    inserted_id = db.post_doc('readings', res)
    print('inserted_id')
    print(inserted_id)
    print('cache_id')
    print(cache_id)
    # print(db.get_collection(readings_table_name).find_one(inserted_id))
    # print(title)

if __name__ == '__main__':
    main()