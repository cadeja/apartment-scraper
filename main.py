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
    fees_and_policies: dict


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


def get_fees_and_policies(html: HTMLParser) -> dict:
    # returns dict of dict of dict of dict...
    fees_and_policies = {}

    tabs = {
        'required_fees': 'div#fees-policies-required-fees-tab',
        'pets': 'div#fees-policies-pets-tab',
        'parking': 'div#fees-policies-parking-tab',
        'storage': 'div#fees-policies-storage-tab'
    }

    for tab in tabs:
        try:
            category = html.css_first(tabs[tab])
        except:
            category = None

        if category:
            fees_and_policies[tab] = {}

            sections = category.css('div.feespolicies')
            for section in sections:
                section_name = extract_text(section, 'h4.header-column')

                fees_and_policies[tab][section_name] = {}

                fees = section.css('ul li:nth-child(n+2)')
                for fee in fees:
                    fee_name = extract_text(fee, 'div.feeName')

                    if fee_name == 'Requirements:':
                        requirements = extract_text(fee, 'div.subTitle')
                        fees_and_policies[tab][section_name]['Requirements'] = requirements
                    elif fee_name:
                        fee_amount = extract_text(fee, 'div.column-right')
                        fees_and_policies[tab][section_name][fee_name] = fee_amount

    return fees_and_policies


def parse_listing(html: HTMLParser) -> dict:

    fees_and_policies = get_fees_and_policies(html)
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
        fees_and_policies=fees_and_policies
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