from Wikipedia_Clone import *

def main():
    url = 'https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2'
    configuration = config.config(url)
    # configuration = config.config(url, use_default=True)
    configuration.procedure()
    # configuration.download_file()

    eda = wiki_explorer.WikiExplorer(configuration)
    if eda.file_absolute is not None:
        # eda.peek(only_articles=True,
        #         exclude_redirects=True,
        #         trunc_size=1000,
        #         )
        eda.process_and_report(limit=10)
        eda.save_to_csv(output_filename="wiki_edges.csv", limit=10)
if __name__ == "__main__":
    main()
