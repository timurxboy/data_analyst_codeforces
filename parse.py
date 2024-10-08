import requests
from bs4 import BeautifulSoup

def get_titles_from_page(page_number):
    url = f'https://codeforces.com/ratings/page/{page_number}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Ошибка при получении страницы {page_number}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    members = set()

    rating_div = soup.find('div', class_='datatable ratingsDatatable')
    
    if rating_div:
        table = rating_div.find('table')
        if table:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                for cell in cells:
                    link = cell.find('a')
                    if link and 'href' in link.attrs: 
                        href_value = link['href']  
                        if '/profile/' in href_value:
                            members.add(href_value.split('/profile/')[1]) 
    return members

page_number = 1

while page_number <= 836: 
    
    members = get_titles_from_page(page_number)
    
    print(page_number)
    page_number += 1  
