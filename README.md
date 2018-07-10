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

## Examples
Show a list of supported sites to select from where to download 'One Piece':
> `./smd.py 'One Piece'`

Search mangaall.net for mangas containing the word 'Death' in its name, then select which one to download:
> `./smd.py -s mangaall 'Death'`

Show a list of sites with in English language, to select from where to download 'Bleach':
> `./smd.py --lang en Bleach`

Download from 10th chapter to 20th of 'Naruto' from MangaHere:
> `./smd.py --start 10 --stop 20 -s mangahere Naruto`

List supported Spanish sites:
> `./smd.py --lang es -l`

To see all available options use:
> `./smd.py -h`

## Dependencies
This tool uses BeautifulSoup to pull data out of HTML pages, thanks to Leonard Richardson. Use this command to install it:
> `pip install beautifulsoup4`

## Support for new sites
If your favorite site isn't supported yet, open an [issue](https://github.com/adbenitez/smd/issues/new) to request it.
