import httpx
from selectolax.parser import HTMLParser
import time
from dataclasses import dataclass, asdict

## SEARCH VARIABLES
CITY = 'minneapolis'
STATE = 'mn'


@dataclass
class Listing:
    name: str
    address: str
    zipcode: str
    neighborhood: str
    phone_number: str
    rent_range: str
    walk_score: int
    bike_score: int
    transit_score: int


def get_html(url: str, **kwargs) -> HTMLParser:
    headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0'
    }
    page = kwargs.get('page')
    if page:
        try:
            resp = httpx.get(url + str(page), headers=headers, follow_redirects=True)
            print(resp.status_code)
        except httpx.HTTPError as err:
            print(err)
    else:
        resp = httpx.get(url, headers=headers, follow_redirects=True)
    html = HTMLParser(resp.text)
    return html


def get_num_of_pages(html: HTMLParser) -> int:
    page_range = extract_text(html, 'span.pageRange')
    last_page = page_range.split(' ')[-1]
    return int(last_page)


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


def extract_text(html: HTMLParser, sel: str) -> str | None:
    try:
        return html.css_first(sel).text(strip=True)
    except:
        return None


def get_listing_address(html: HTMLParser) -> list[str]:
    address = extract_text(html, 'div.propertyAddressContainer span.delivery-address')
    address = address.replace(',','')
    zipcode = extract_text(html, 'div.propertyAddressContainer span.stateZipContainer span:nth-child(2)')
    return [address, zipcode]


def parse_listing(html: HTMLParser) -> dict:

    address, zipcode = get_listing_address(html)

    listing = Listing(
        name=extract_text(html, 'h1#propertyName'),
        address=address,
        zipcode=zipcode,
        neighborhood=extract_text(html, 'a.neighborhood'),
        phone_number=extract_text(html, 'div.phoneNumber span'),
        rent_range=extract_text(html, 'p.rentInfoDetail'),
        walk_score=int(extract_text(html, 'div#walkScoreValue')),
        bike_score=int(extract_text(html, 'div.bikeScore div.score')),
        transit_score=int(extract_text(html, 'div.transitScore div.score')),
    )
    return asdict(listing)


def main():
    
    baseurl = f'https://www.apartments.com/apartments/{CITY}-{STATE}/max-1-bedrooms/'

    num_pages = get_num_of_pages(get_html(baseurl))

    for x in range(1, num_pages + 1):
        html = get_html(baseurl, page=x)
    
        # gets url AND company. Company is not easy to get on actual listing
        listings = parse_search_page(html)

        for listing in listings:
            html = get_html(listing.get('url'))
            data = parse_listing(html)
            data['company'] = listing.get('company')
            print(data)
            time.sleep(.5)

if __name__ == '__main__':
    main()