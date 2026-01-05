from Wikipedia_Clone import *

def main():
    url = 'https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2'
    configuration = config.config(url)
    # configuration = config.config(url, use_default=True)
    configuration.procedure()
    # configuration.download_file()

    eda = wiki_explorer.WikiExplorer(configuration)
    eda.peek(only_articles=True,
             exclude_redirects=True,
             trunc_size=1000)

if __name__ == "__main__":
    main()
