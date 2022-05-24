try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
config = {
    'description': "2022 Eviction and Fair Market Rent Analysis", 
    'author': 'Amelia Ingram, Joshua Megnauth, Abby Strick, and Rameasa Arna', 
    'url': 'https://github.com/amelia-ingram/eviction-rent',
    'download_url': 'https://github.com/amelia-ingram/eviction-rent',
    'author_email': 'amelia.ingram24@qmail.cuny.edu',
    'version': '0.1',
    'install_requires': 'NA',
    'packages': ['pandas', 'numpy', 'geopandas', 'folium'],
    'scripts': [],
    'name': 'eviction_analysis'
}

setup(**config)
