from Wikipedia_Clone import *

def main():
    url = 'https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2'
    configuration = config.config(url)
    configuration.make_dir(configuration.path_default)
    configuration.procedure()
    # configuration.download_file()

if __name__ == "__main__":
    main()