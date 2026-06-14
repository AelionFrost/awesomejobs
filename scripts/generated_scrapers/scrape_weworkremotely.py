import urllib.request
from bs4 import BeautifulSoup

def scrape_weworkremotely():
    try:
        url = "https://weworkremotely.com/"
        response = urllib.request.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')

        jobs = []
        job_elements = soup.find_all('li', class_='job')

        for job in job_elements:
            title = job.find('a').text.strip()
            company = job.find('span', class_='company').text.strip()
            location = job.find('span', class_='location').text.strip()
            apply_link = job.find('a')['href']
            jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'url': apply_link,
                'source': "weworkremotely"
            })

        return jobs
    except Exception as e:
        print(f"Error: {e}")
        return []

# Example usage
jobs = scrape_weworkremotely()
for job in jobs:
    print(job)
