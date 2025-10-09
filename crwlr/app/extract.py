from bs4 import BeautifulSoup
from readability import Document
from .utils import clean_text


def extract_main_content(html: str) -> str:
    try:
        doc = Document(html)
        return doc.summary(html_partial=True)
    except Exception:
        return html


def sectionize(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    
    main_elem = soup.find('main')
    article_elem = soup.find('article')
    content_id = soup.find(id='content')
    content_class = soup.find(class_='content')
    
    scope = main_elem or article_elem or content_id or content_class or soup
    
    sections = []
    current_heading = ""
    current_text_parts = []
    
    for element in scope.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'div']):
        if element.name in ['h1', 'h2', 'h3', 'h4']:
            if current_heading or current_text_parts:
                text = clean_text(' '.join(current_text_parts))
                if text:
                    sections.append({
                        'heading': current_heading,
                        'text': text
                    })
            
            current_heading = clean_text(element.get_text())
            current_text_parts = []
        else:
            text = element.get_text()
            if text.strip():
                current_text_parts.append(text)
    
    if current_heading or current_text_parts:
        text = clean_text(' '.join(current_text_parts))
        if text:
            sections.append({
                'heading': current_heading,
                'text': text
            })
    
    return sections
