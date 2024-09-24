import argparse
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def parse():
    parser = argparse.ArgumentParser()
    #parser.add_argument("-p")
    parser.add_argument("start_url", type=str, help="Start url of the spider")

    parser.add_argument("-r", "--rate_limit", type=float, default=1.0, help="Maximim number of http requests per second")
    return parser.parse_args()

def get_all_links_on_page(url):
    try:
        reqs = requests.get(url)
    except:
        print(f"Could not load page: {url}")
        return []
    soup = BeautifulSoup(reqs.text, 'html.parser')
    url_parse = urlparse(url)
    urls = []
    for link in soup.find_all('a'):
        link = link.get('href')
        # Remove javascript:void(0)
        

        link_parse = urlparse(link)
        if(link_parse.netloc == ''):
            link_parse = link_parse._replace(netloc = url_parse.netloc)
        link = link_parse.geturl()
        if(link is None or len(link)==0):
            continue
        if("javascript:void(0)" in link):
            continue
        link = url_without_parameters_and_fragments(link)
        link = re_encode(link)
        urls.append(link)

    return urls

def url_without_parameters_and_fragments(url):
    url = urlparse(url)._replace(query=None).geturl()
    url = urlparse(url)._replace(fragment=None).geturl()
    return url

# Make sure all identical URLs encoded as identical strings
def re_encode(url):
    url = urlparse(url).geturl()
    if(url.endswith('/')):
        url = url[:-1]
    return url 

def run_spider(domain, rate_limit):
    domain = re_encode(domain)
    domain_parsed = urlparse(domain)
    visited = []
    queue = [domain]
    time_of_last_request = time.time()
    while len(queue) > 0:
        url = queue.pop(0)
        if url not in visited:
            visited.append(url)
            parsed = urlparse(url)
            
            # Rate limit
            time_since_last_request = time.time() - time_of_last_request
            if(time_since_last_request < 1.0/rate_limit):
                time.sleep(1.0/rate_limit - time_since_last_request)
            time_of_last_request = time.time()

            # Temporary, fix incorrect scheme 
            if(parsed.scheme == ''):
                parsed = parsed._replace(scheme = domain_parsed.scheme)

            url = parsed.geturl()
            print(f"Visiting {url}")
            found = get_all_links_on_page(url)
            for link in found:
                try:
                    link_netloc = urlparse(link).netloc
                    domain_netloc = urlparse(domain).netloc
                except:
                    print(f"Could not parse link: {link}")
                    continue
                is_subdomain_of_domain = link_netloc.endswith(domain_netloc)
                if not link in visited and not link in queue and is_subdomain_of_domain:
                    queue.append(link) # BFS
                    #queue = [link] + queue # DFS
    return visited

if __name__ == "__main__":
    args = parse()
    print(f"Using rate limit: {args.rate_limit}")
    domain = args.start_url
    run_spider(domain, args.rate_limit)