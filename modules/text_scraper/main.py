import re

from mechanicalsoup import StatefulBrowser


def extract_text_from_url(url: str):
    # Create a MechanicalSoup browser instance
    browser = StatefulBrowser()

    try:
        # Open the URL and fetch the page
        browser.open(url)
        page = browser.page

        # Extract text from the article tag, removing other tags
        article = page.select_one('article')
        if article:
            text = article.get_text()
            cleaned_text = re.sub(r'\n+', '\n', text)  # Replace multiple consecutive newlines with a single newline
            cleaned_text = re.sub(r'^\s+', '', cleaned_text, flags=re.MULTILINE)  # Remove leading whitespace on each line
            return cleaned_text.strip()
        else:
            print(f"No 'article' tag found on {url}")
            return None

    except Exception as e:
        print(f"Error while processing {url}: {e}")
        return None
    finally:
        browser.close()


def extract_links_from_nav(url: str):
    # Create a MechanicalSoup browser instance
    browser = StatefulBrowser()
    try:
        # Open the URL and fetch the page
        browser.open(url)

        # Find the <nav> element, or adjust the CSS selector to match your specific HTML structure
        nav_elements = browser.page.select('nav')

        extracted_links = []
        if nav_elements:
            for nav_element in nav_elements[2:]:

                # Find all <a> elements within the <nav> element
                links = nav_element.find_all('a')

                # Extract and print the href attributes of the links
                for link in links:
                    href = link.get('href').replace(".", "")
                    if href:
                        print(f"Found Link: {url}{href}")
                        extracted_links.append(url + href)
        else:
            print("Found no nav elements")

        return list(set(extracted_links))
    except Exception as e:
        print(f"Error while processing {url}: {e}")
        return []
    finally:
        browser.close()
