import logging
import re
import requests_cache

from urllib.parse import urljoin
from bs4 import BeautifulSoup as BS
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL
from outputs import control_output


def whats_new(session):
    """Функция получает информацию о последних версиях Python."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = session.get(whats_new_url)
    response.encoding = 'utf-8'    
    soup = BS(response.text, features='lxml')
    get_section = soup.find('section', attrs={'id': 'what-s-new-in-python'})
    get_div = get_section.find('div', attrs={'class': "toctree-wrapper compound"})
    get_li = get_div.find_all('li', attrs={'class': "toctree-l2"})
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for li in tqdm(get_li):        
        version_a_tag = li.find('a')
        href = version_a_tag['href']
        ssil = urljoin(whats_new_url, href)
        session =requests_cache.CachedSession()
        response = session.get(ssil)
        response.encoding = 'utf-8'
        soup_v = BS(response.text, 'lxml')
        h1 = soup_v.find('h1')
        dl = soup_v.find('dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append((ssil, h1.text, dl_text))
        return result

def latest_versions(session):
    """Функция получает информацию о последней версии Python."""
    response = session.get(MAIN_DOC_URL)
    response.encoding = 'utf-8'
    soup = BS(response.text, 'lxml')    
    sidebar = soup.find('div', attrs = {'class':'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    
    result = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        result.append((link, version, status))
    return result

def download(session):
    """Функция скачивает и сохраняет файл."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = session.get(downloads_url)
    response.encoding = 'utf-8'
    soup = BS(response.text, 'lxml')    
    table_tag = soup.find('table', {'class': 'docutils'})
    a4_tag = table_tag.find('a', {'href':re.compile(r'.+pdf-a4\.zip$')})
    a4_link = a4_tag['href']    
    archive_url = urljoin(downloads_url, a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    print(filename)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}

def main():
    configure_logging()
    # Отмечаем в логах момент запуска программы.
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    # Логируем переданные аргументы командной строки.
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()    
    # Получение из аргументов командной строки нужного режима работы.
    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    # Логируем завершение работы парсера.
    logging.info('Парсер завершил работу.')

if __name__ == '__main__':
    main() 
