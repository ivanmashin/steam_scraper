from setuptools import setup

setup(
    name='SteamScraper',
    version='0.1',
    url='https://github.com/MashinIvan/steam_parser',
    description='Steam games scraping tool',
    install_requires=[
        'requests',
        'beautifulsoup4',
        'lxml'
    ]
)