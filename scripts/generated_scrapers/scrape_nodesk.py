from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

def scrape_nodesk():
    url = 'https://nodesk.com/remote-jobs'
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = Request(url, headers=headers)
    
    try:
        response = urlopen(req)
        html_content = response.read()
    except Exception as e:
        print(f"Failed to fetch the page: {e}")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    
    for job in soup.find_all('div', class_='job-card'):
        title = job.find('h3').text.strip()
        company = job.find('span', class_='company-name').text.strip()
        location = job.find('span', class_='location').text.strip()
        url = job.find('a')['href']
        
        jobs.append({
            'title': title,
            'company': company,
            'location': location,
            'url': url,
            'source': "nodesk"
        })
    
    return jobs
