import datetime
import requests
import services.db as db
import services.db_cache as redis
import services.bs_helper as scrapper

readings_table_name = 'readings'
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


def main():
    content = get_html_content()
    res = scrapper.get_lecture_pieces(content)
    cache_id = redis.post(TODAY, res)
    inserted_id = db.post_doc('readings', res)
    print(f'Inserted id: {inserted_id}')
    print(f'Cache id: {cache_id}')

if __name__ == '__main__':
    main()