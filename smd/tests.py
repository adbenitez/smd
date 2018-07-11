# -*- coding: utf-8 -*-
'''Some basic tests, to detect broken sites'''

import os

if __name__ == '__main__':
    os.system('smd -s ninemanga-en "one piece"')
    print()
    os.system('smd -s HEAVENMANGA naruto')
    print()
    os.system('smd -s MangaReader Death')
    print()
    os.system('smd -s mangaall skip')
    print()
    os.system('smd -s mangadoor bleach')
    print()
    os.system('smd -s manganelo black')
    print()
    os.system('smd -s mangahere lol')
    print()
