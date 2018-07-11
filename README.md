<p align="center"><img align="center" src="logo/logo.png" alt="smd logo"/></p>
<h1 align="center">Simple Manga Downloader</h1>
<p align="center">
A tool to search and automatically download manga from web sites, with support for several sites and languages.
</p>

## Currently supported sites
* Deutsch (DE):
  * NineManga-de
* English (EN):
  * NineManga-en
  * MangaReader
  * MangaAll
  * MangaNelo
  * MangaHere
* Español (ES):
  * NineManga-es
  * HeavenManga
  * MangaDoor
* Italiano (IT):
  * NineManga-it
* Português (PT):
  * NineManga-br
* Русский (RU):
  * NineManga-ru

## Installation
To run this program you need to have **python3** installed in your machine, for a python installation guide look [here](http://docs.python-guide.org/en/latest/starting/installation/).

To install **smd** open your terminal and execute the following command:
> `pip install smd`

For help installing packages look [here](https://packaging.python.org/tutorials/installing-packages/).

## Examples
To select site and manga interactively just run:
> `smd`

To search (and download) 'One Piece' and select site interactively:
> `smd 'One Piece'`

To search mangaall.net for mangas containing the word 'love' in its name, and select which one to download:
> `smd -s mangaall love`

To select a site with English language, and search/download 'Bleach':
> `smd --lang en Bleach`

To select site interactively and download from chapter 10th to 20th of 'Naruto':
> `smd --start 10 --stop 20 Naruto`

List all supported sites:
> `smd -l`

List supported Spanish sites:
> `smd --lang es -l`

To see all available options use:
> `smd -h`

## Dependencies
This tool uses **BeautifulSoup** to pull data out of HTML pages, thanks to Leonard Richardson. You don't have to install the dependencies manually unless you are installing from source.

## Support for new sites
If your favorite site isn't supported yet, open an [issue](https://github.com/adbenitez/smd/issues/new) to request it.
