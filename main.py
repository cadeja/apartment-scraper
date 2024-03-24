import httpx
from selectolax.parser import HTMLParser
import time
from dataclasses import dataclass, asdict

@dataclass
class Listing:
    name: str
    neighborhood: str
    


def get_html(url: str, **kwargs) -> HTMLParser:
    headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0'
    }
    page = kwargs.get('page')
    if page:
        resp = httpx.get(url + str(page), headers=headers, follow_redirects=True)
    else:
        resp = httpx.get(url, headers=headers, follow_redirects=True)
    html = HTMLParser(resp.text)
    return html


def parse_search_page(html: HTMLParser):
    # yields listing urls
    listings = html.css('section#placards ul li.mortar-wrapper')
    for listing in listings:

        try:
            company = listing.css_first('div.property-logo').attributes['aria-label']
        except:
            company = None

        yield {
            'url': listing.css_first('a.property-link').attributes['href'],
            'company': company
        }


def extract_text(html, sel) -> str:
    try:
        return html.css_first(sel).text(strip=True)
    except:
        return None


def parse_listing(html: HTMLParser):
    return {
        'property_name': extract_text(html, 'h1#propertyName'),
        'neighborhood': extract_text(html, 'a.neighborhood'),
        'phone_number': extract_text(html, 'div.phoneNumber span'),
        'rent_range': extract_text(html, 'p.rentInfoDetail'),
        'walk_score': extract_text(html, 'div#walkScoreValue'),
        'bike_score': extract_text(html, 'div.bikeScore div.score'),
        'transit_score': extract_text(html, 'div.transitScore div.score'),
        # 'sound_score': extract_text(html, 'div#soundScoreSection div.score') <- requires script
    }


def main():
    
    baseurl = 'https://www.apartments.com/apartments/minneapolis-mn/max-1-bedrooms/'
    html = get_html(baseurl, page=1)
    
    # gets url AND company. Company is not easy to get on actual listing
    listings = parse_search_page(html)
    for listing in listings:
        html = get_html(listing.get('url'))
        print(listing.get('company'), parse_listing(html))
        time.sleep(.5)

if __name__ == '__main__':
    main()