from datetime import datetime, timedelta, timezone
import requests
import services.db as db
from services.db_cache import RedisUp
import services.bs_helper as scrapper

readings_table_name = 'readings'
today_utc = today = datetime.now(timezone.utc)
today_eu = today_utc.astimezone(timezone(timedelta(hours=1)))

today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
now_eu = today_eu.date().strftime("%Y-%m-%d")
edate = datetime(2023,5,20) #.strftime("%Y-%m-%d")
sdate = datetime(2023,4,9) # .strftime("%Y-%m-%d") // 2/13, 4/7-8

URL_TODAY = 'https://www.ciudadredonda.org/calendario-lecturas/evangelio-del-dia/hoy'
URL = 'https://www.ciudadredonda.org/calendario-lecturas/evangelio-del-dia/?f='


def request_web_content(date = None):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    uri = URL_TODAY if not date else (URL + date)
    response = requests.get(uri, headers=headers)
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


# TODO: Add cache
def get_html_content():
    # content = get_html_local_file()

    # if content:
    #     return content

    content = request_web_content()
    create_html_local_file(content)

    return content

def loop_days_range(start_date, end_date):
   current_date = start_date
   while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def run_from_date(start_date, end_date):
    for time in loop_days_range(sdate, today):
        datee = time.strftime("%Y-%m-%d")
        content = request_web_content(datee)
        send_data_to_db(content)


def run_today():
    content = get_html_content()
    send_data_to_db(content)
    

def send_data_to_db(content):
    res = scrapper.get_lecture_pieces(content)
    cache_id = redis.post(now_eu, res)
    print(f'Inserted id: {cache_id}\n')
    inserted_id = db.post_doc('readings', res)
    print(f'Inserted id: {inserted_id}')
    print(f'Cache id: {cache_id}')

def main():
    # run_from_date(sdate, today)
    run_today()

if __name__ == '__main__':
    redis = RedisUp()
    main()