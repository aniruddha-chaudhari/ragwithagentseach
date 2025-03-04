from langchain_community.document_loaders import WebBaseLoader

def load_web_document(url):
    """
    Load a document from a specified URL using WebBaseLoader.

    Args:
    - url (str): The URL of the webpage to load.

    Returns:
    - docs: The loaded document(s).
    """
    loader = WebBaseLoader(url)
    docs = loader.load()
    return docs

# Example usage
url = "https://timesofindia.indiatimes.com/city/mumbai/pocso-case-20-years-ri-for-father-after-fearless-deposition-by-thane-girl/articleshow/118688947.cms"
docs = load_web_document(url)
print(docs)
