import logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

class Crawler:

    def __init__(self, urls=[]):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.crawled_data = []

    def download_url(self, url):
        return requests.get(url).text

    def extract_page_data(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract basic metadata
        title = soup.title.string if soup.title else "No title"
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc else "No description"

        # Extract text content by sections
        content_data = {
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'tables': []
        }

        # Extract headings (h1 to h6)
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            for heading in headings:
                if heading.text.strip():
                    content_data['headings'].append({
                        'level': i,
                        'text': heading.text.strip()
                    })

        # Extract paragraphs
        for p in soup.find_all('p'):
            if p.text.strip():
                content_data['paragraphs'].append(p.text.strip())

        # Extract lists (both ordered and unordered)
        for list_tag in soup.find_all(['ul', 'ol']):
            list_items = []
            for item in list_tag.find_all('li'):
                if item.text.strip():
                    list_items.append(item.text.strip())
            if list_items:
                content_data['lists'].append({
                    'type': list_tag.name,
                    'items': list_items
                })

        # Extract tables
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr'):
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    if cell.text.strip():
                        row_data.append(cell.text.strip())
                if row_data:
                    table_data.append(row_data)
            if table_data:
                content_data['tables'].append(table_data)

        # Store the extracted data
        page_data = {
            'url': url,
            'title': title,
            'description': description,
            'content': content_data
        }
        self.crawled_data.append(page_data)

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
            yield path

    def add_url_to_visit(self, url):
        if url not in self.visited_urls and url not in self.urls_to_visit:
            self.urls_to_visit.append(url)

    def crawl(self, url):
        html = self.download_url(url)
        self.extract_page_data(url, html)
        for url in self.get_linked_urls(url, html):
            self.add_url_to_visit(url)

    def run(self, max_pages=10):
        while self.urls_to_visit and len(self.visited_urls) < max_pages:
            url = self.urls_to_visit.pop(0)
            logging.info(f'Crawling: {url}')
            try:
                self.crawl(url)
            except Exception:
                logging.exception(f'Failed to crawl: {url}')
            finally:
                self.visited_urls.append(url)
        
        return self.display_results()

    def display_results(self):
        all_content = []
        for data in self.crawled_data:
            content_text = ""
            
            # Add metadata as a header section
            content_text += f"# {data['title']}\n\n"
            content_text += f"**URL:** {data['url']}\n\n"
            content_text += f"**Description:** {data['description']}\n\n"
            content_text += "---\n\n"  # Horizontal rule for separation
            
            # Add headings
            if data['content']['headings']:
                content_text += "## Page Headings\n\n"
                for heading in data['content']['headings']:
                    # Add appropriate number of # for heading level
                    content_text += f"{'#' * heading['level']} {heading['text']}\n"
                content_text += "\n"
            
            # Add paragraphs
            if data['content']['paragraphs']:
                content_text += "## Content\n\n"
                for p in data['content']['paragraphs']:
                    content_text += f"{p}\n\n"
            
            # Add lists
            if data['content']['lists']:
                content_text += "## Lists\n\n"
                for lst in data['content']['lists']:
                    content_text += f"### {lst['type'].upper()} List\n\n"
                    for item in lst['items']:
                        if lst['type'] == 'ul':
                            content_text += f"* {item}\n"
                        else:
                            content_text += f"1. {item}\n"
                    content_text += "\n"
            
            # Add tables
            if data['content']['tables']:
                content_text += "## Tables\n\n"
                for table in data['content']['tables']:
                    if table:  # Check if table has data
                        # Create header row
                        content_text += "| " + " | ".join(table[0]) + " |\n"
                        # Add separator row
                        content_text += "| " + " | ".join(["---"] * len(table[0])) + " |\n"
                        # Add data rows
                        for row in table[1:]:
                            content_text += "| " + " | ".join(row) + " |\n"
                        content_text += "\n"
            
            all_content.append(content_text)
            
        # Return all content as a single string with separators
        return "\n---\n\n".join(all_content)

if __name__ == '__main__':
    crawler = Crawler(urls=['https://mace.ac.in/'])
    content = crawler.run(max_pages=1)
    
    # Save to markdown file
    with open('crawled_content.md', 'w', encoding='utf-8') as f:
        f.write(content)
