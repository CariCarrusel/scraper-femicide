import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import logging
import time
from urllib.parse import urljoin

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tribuno_scraper.log'),
        logging.StreamHandler()
    ]
)

def scrape_tribuno_policiales(year):
    base_url = "https://eltribunodejujuy.com/seccion/policiales"
    articles = []
    page = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    while True:
        try:
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}/{page}"
            
            logging.info(f"Scraping página {page}: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encuentra todos los artículos en la página
            article_elements = soup.find_all('article') or soup.find_all(class_='article-item')
            
            if not article_elements:
                logging.info(f"No se encontraron más artículos en la página {page}")
                break
            
            found_articles_in_year = False
            
            for article in article_elements:
                try:
                    # Obtiene el enlace y título
                    link_element = article.find('a')
                    if not link_element:
                        continue
                        
                    link = urljoin(base_url, link_element['href'])
                    
                    # Extrae la fecha del enlace
                    # Formato esperado: .../2025-1-29-0-31-0-titulo-de-la-noticia
                    date_parts = link.split('/')[-1].split('-')[:3]
                    if len(date_parts) < 3:
                        continue
                        
                    article_year = int(date_parts[0])
                    
                    # Si el artículo no es del año buscado, continuamos
                    if article_year != year:
                        if article_year < year:
                            logging.info(f"Se alcanzó un año anterior ({article_year}), finalizando búsqueda")
                            return articles
                        continue
                    
                    found_articles_in_year = True
                    
                    # Obtiene el título
                    title_element = article.find('h2') or article.find('h3') or article.find(class_='title')
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    
                    # Términos de búsqueda relacionados con femicidios
                    search_terms = [
                        'femicidio', 'violencia de género', 'asesinato de mujer',
                        'violencia contra la mujer', 'muerte de mujer', 'género',
                        'femicida', 'violencia machista', 'violencia familiar',
                        'abuso sexual', 'asesinato', 'crimen', 
                        'homicidio', 'mató', 'asesinó', 'hallaron muerta',
                        'encontraron muerta', 'cadáver de mujer', 'cuerpo de mujer'
                    ]
                    
                    if any(term in title.lower() for term in search_terms):
                        # Scrapea la página individual del artículo para más detalles
                        try:
                            logging.info(f"Scrapeando artículo: {link}")
                            article_response = requests.get(link, headers=headers, timeout=10)
                            article_soup = BeautifulSoup(article_response.content, 'html.parser')
                            
                            # Intenta obtener el contenido del artículo
                            content_element = article_soup.find(class_='entry-content') or article_soup.find(class_='article-content')
                            content = content_element.text.strip() if content_element else "No content available"
                            
                            article_data = {
                                'title': title,
                                'link': link,
                                'content': content,
                                'source': 'El Tribuno Jujuy',
                                'date': f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                            }
                            
                            articles.append(article_data)
                            logging.info(f"Artículo guardado: {title} - {link}")
                            
                            # Espera entre requests de artículos individuales
                            time.sleep(2)
                            
                        except Exception as e:
                            logging.error(f"Error scraping artículo individual {link}: {str(e)}")
                
                except Exception as e:
                    logging.error(f"Error procesando artículo: {str(e)}")
                    continue
            
            if not found_articles_in_year:
                logging.info(f"No se encontraron artículos del año {year} en la página {page}")
                if article_year < year:
                    break
            
            page += 1
            time.sleep(3)  # Espera entre páginas
            
        except requests.RequestException as e:
            logging.error(f"Error en la página {page}: {str(e)}")
            break
            
        except Exception as e:
            logging.error(f"Error inesperado: {str(e)}")
            break
    
    return articles

def main():
    year = 2024  # Puedes modificar el año aquí
    
    try:
        logging.info(f"Iniciando scraping de El Tribuno Jujuy para el año {year}")
        articles = scrape_tribuno_policiales(year)
        
        # Guarda los resultados
        filename = f"tribuno_femicidios_{year}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'link', 'content', 'source', 'date'])
            writer.writeheader()
            for article in articles:
                writer.writerow(article)
        
        logging.info(f"Se encontraron {len(articles)} artículos relacionados con femicidios en {year}")
        logging.info(f"Los resultados se guardaron en {filename}")
        
    except Exception as e:
        logging.error(f"Error en la ejecución principal: {str(e)}")

if __name__ == "__main__":
    main()
