import os
import json
import requests
import redis
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
DB_ENDPOINT = os.getenv("UPSTACK_ENDPOINT")
DB_PORT = os.getenv("UPSTACK_PORT")
DB_PASSWORD = os.getenv("UPSTACK_PASSWORD")
TODAY = '20230516'

r = redis.Redis(
  host= DB_ENDPOINT,
  port= DB_PORT,
  password=DB_PASSWORD,
)

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

def post_lectura(content):
    key = TODAY
    content = json.dumps(content)
    r.set(key, content)
    print(r.get(key))

def main():
    content = get_html_content()
    res = get_pieces_of_content(content)
    post_lectura(res)
    # print(res)
    # print(title)

if __name__ == '__main__':
    main()