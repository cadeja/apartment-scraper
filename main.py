import httpx
from selectolax.parser import HTMLParser
import time


def get_html(url: str, **kwargs) -> HTMLParser:
    headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0'
    }
    resp = httpx.get(url, headers=headers, follow_redirects=True)
    html = HTMLParser(resp.text)
    return html


def parse_search_page(html: HTMLParser):
    # yields listing urls
    listings = html.css('section#placards ul li.mortar-wrapper')
    for listing in listings:
        yield listing.css_first('a.property-link').attributes['href']


def extract_text(html, sel) -> str:
    try:
        return html.css_first(sel).text(strip=True)
    except:
        return None


def parse_listing(html: HTMLParser):
    return {
        'property_name': extract_text(html, 'h1#propertyName'),
        'neighborhood': extract_text(html, 'a.neighborhood'),
        'rent_range': extract_text(html, 'p.rentInfoDetail')
    }


def main():
    
    baseurl = 'https://www.apartments.com/apartments/minneapolis-mn/max-1-bedrooms/?bb=0j6ynr5w9Kh-9919J'
    html = get_html(baseurl)
    urls = parse_search_page(html)
    for url in urls:
        html = get_html(url)
        print(parse_listing(html))
        time.sleep(.5)

if __name__ == '__main__':
    main()