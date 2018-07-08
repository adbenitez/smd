<p align="center"><img align="center" src="logo/logo.png" alt="smd logo"/></p>
<h1 align="center">Simple Manga Downloader</h1>
<p align="center">
A tool to search and automatically download manga from web sites, with support for several sites and languages.
</p>

## Currently supported sites
* Deutsch (DE):
  * ninemanga-de
* English (EN):
  * ninemanga-en
  * mangareader
  * mangaall
  * manganelo
* Español (ES):
  * ninemanga-es
  * heavenmanga
  * mangadoor
* Italiano (IT):
  * ninemanga-it
* Português (PT):
  * ninemanga-br
* Русский (RU):
  * ninemanga-ru

## Examples
Download 'Death Note' from mangaall.net:
> `./smd.py -s mangaall 'Death Note'`

Download 'Bleach' from any site in English:
> `./smd.py --lang en Bleach`

Download from 10th chapter to 20th of 'Naruto':
> `./smd.py --start 10 --stop 20 Naruto`

List supported Spanish sites:
> `./smd.py --lang es -l`

Show help:
> `./smd.py -h`

## Dependencies
This tool uses BeautifulSoup to pull data out of HTML pages, thanks to Leonard Richardson. Use this command to install it:
> `pip install beautifulsoup4`

## Support for new sites
If your favorite site isn't supported yet, open an [issue](https://github.com/adbenitez/jNotifyOSD/issues/new) to request it.
