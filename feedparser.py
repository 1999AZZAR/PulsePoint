# -*- coding: utf-8 -*-
# feedparser bypass module for Python 3.13

import requests
from bs4 import BeautifulSoup
import datetime
import time

class FeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            return None

def parse(url_or_file):
    '''
    Simplified feedparser.parse() implementation using requests and BeautifulSoup
    '''
    feed = FeedParserDict()
    feed['entries'] = []
    feed['feed'] = FeedParserDict()
    feed['feed']['title'] = ""
    feed['bozo'] = 0
    
    try:
        # Check if it's a URL
        if url_or_file.startswith(('http://', 'https://')):
            response = requests.get(url_or_file, timeout=10)
            if response.status_code != 200:
                feed['bozo'] = 1
                feed['bozo_exception'] = f"HTTP error {response.status_code}"
                return feed
            content = response.text
        else:
            # Assume it's a file
            with open(url_or_file, 'r') as f:
                content = f.read()
        
        # Parse the XML content
        soup = BeautifulSoup(content, 'xml')
        if soup is None:
            feed['bozo'] = 1
            feed['bozo_exception'] = "Could not parse XML content"
            return feed
            
        # Get feed title
        channel = soup.find('channel') or soup.find('feed')
        if channel:
            title = channel.find('title')
            if title:
                feed['feed']['title'] = title.text
        
        # Extract entries
        entries = []
        items = soup.find_all('item') or soup.find_all('entry')
        
        for item in items:
            entry = FeedParserDict()
            
            # Get title
            title = item.find('title')
            entry['title'] = title.text if title else ""
            
            # Get description/summary
            description = item.find('description') or item.find('summary') or item.find('content')
            entry['description'] = description.text if description else ""
            entry['summary'] = entry['description']
            
            # Get link
            link = item.find('link')
            if link and link.has_attr('href'):
                entry['link'] = link['href']
            elif link:
                entry['link'] = link.text
            else:
                entry['link'] = ""
                
            # Get publication date
            pub_date = item.find('pubDate') or item.find('published')
            if pub_date:
                entry['published'] = pub_date.text
                try:
                    # Try to parse the date
                    time_struct = time.strptime(pub_date.text, "%a, %d %b %Y %H:%M:%S %z")
                    entry['published_parsed'] = time_struct
                except:
                    entry['published_parsed'] = None
            else:
                entry['published'] = ""
                entry['published_parsed'] = None
                
            entries.append(entry)
        
        feed['entries'] = entries
        return feed
    except Exception as e:
        feed['bozo'] = 1
        feed['bozo_exception'] = str(e)
        return feed
