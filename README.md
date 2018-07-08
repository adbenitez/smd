# Simple Manga Downloader

A command line program to automatically download manga from web sites.

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

`./smd.py -s mangaall 'Death Note'`

Download 'Bleach' from any site in English:

`./smd.py --lang en Bleach`

Download from 10th chapter to 20th of 'Naruto':

`./smd.py --start 10 --stop 20 Naruto`

List supported Spanish sites:

`./smd.py --lang es -l`

Show help:

`./smd.py -h`

## Dependencies
This tool uses BeautifulSoup to pull data out of HTML pages, thanks to Leonard Richardson.

## Support for new sites
If your favorite site isn't supported yet, open an issue to request it.
