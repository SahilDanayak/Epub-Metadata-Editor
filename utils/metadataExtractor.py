import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

async def getMetadata(query, maxResults):


    async with aiohttp.ClientSession() as session:
        tasks = []
        google_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={maxResults}"
        tasks.append(fetch_metadata_via_google_api(google_url,maxResults, session=session))
        amazon_url = f"https://www.amazon.in/s?k={query}&i=stripbooks"
        tasks.append(fetch_metadata_via_amazon(amazon_url,maxResults/2, session=session))
        amazon_url = f"https://www.amazon.in/s?k={query}&i=digital-text"
        tasks.append(fetch_metadata_via_amazon(amazon_url,maxResults/2, session=session))

        return await asyncio.gather(*tasks, return_exceptions=True)

def fetch_metadata(query,maxResults=10):
    """
    Fetch metadata and images from Google Books and Amazon.
    """
    results = asyncio.run(getMetadata(query, maxResults))
    google_books = results[0]
    amazon_books = results[1] + results[2]
    return google_books, amazon_books



async def fetch_metadata_via_google_api(url,maxResults=10,session=None):
    """Fetch metadata and images via Google Books API."""
    response = await session.get(url,headers=headers)
    if response.status == 200:
        data = await response.json()
        if "items" in data:
            books = []
            for item in data["items"]:
                volume_info = item["volumeInfo"]
                metadata = {
                    "title": volume_info.get("title", "Unknown Title"),
                    "author": ", ".join(volume_info.get("authors", ["Unknown Author"])),
                    "description": volume_info.get("description", "No description available."),
                    "cover_image_url": volume_info.get("imageLinks", {}).get("thumbnail"),
                }
                books.append(metadata)
            return books
    raise Exception("Books not found or API issue.")

async def fetch_metadata_via_amazon(url,maxResults=5, session=None):
    """
    Fetch metadata of the top results for a search query on Amazon.
    """
    
    # Perform search on Amazon
    books = []
    response = await session.get(url, headers=headers)
    if response.status == 200:
        data = await response.read()
        soup = BeautifulSoup(data, 'html.parser')
        search_results = soup.select('.s-result-item')
        for result in search_results:
            title_element = result.select_one('h2 span')
            title = title_element.get_text(strip=True) if title_element else "Unknown Title"
            author_element = result.select_one('.a-color-secondary .a-size-base+ .a-size-base')
            url_element = result.select_one('a')
            image_element = result.select_one('.s-image')

            if (title!="Unknown Title"):
                books.append({
                    "title": title,
                    "author": author_element.get_text(strip=True).replace("(Author)", "").replace("(author)", "").replace("Author","").strip() if author_element else "Unknown Author",
                    "product_url": f"https://www.amazon.in{url_element['href']}" if url_element else None,
                    "cover_image_url": image_element['src'] if image_element else None
                })
                if len(books)==maxResults:
                    break
    else:
        raise Exception(f"Failed to fetch search results from Amazon. HTTP Status: {response.status_code}")
            
    return books


def fetch_metadata_from_amazon_url(url):
    """
    Fetch detailed metadata from an Amazon book URL.
    """
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('span', {'id': 'productTitle'})
        author = soup.find('span', {'class': 'author'})
        description_element = soup.select_one('#bookDescription_feature_div')
        if description_element:
            for br in description_element.find_all('br'):
                br.replace_with('\n')
            description = description_element.get_text().replace("Read more", "").strip()
        else:
            description = "No description available."
        image_element = soup.select_one('#landingImage')

        image_url = (
            image_element.attrs.get('data-old-hires') if image_element and image_element.attrs.get('data-old-hires')
            else image_element.attrs.get('src') if image_element and image_element.attrs.get('src')
            else None
        )

        return {
            "title": title.get_text(strip=True) if title else 'Unknown Title',
            "author": author.get_text(strip=True) if author else 'Unknown Author',
            "description": description,
            "cover_image_url": image_url
        }
    else:
        raise Exception(f"Failed to fetch data from Amazon. HTTP Status: {response.status_code}")