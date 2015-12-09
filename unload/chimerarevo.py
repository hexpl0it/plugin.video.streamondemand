# -*- coding: utf-8 -*-
#------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para chimerarevo
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "chimerarevo"
__category__ = "D"
__type__ = "generic"
__title__ = "chimerarevo (IT)"
__language__ = "IT"

headers = [
    ['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Referer', 'http://www.chimerarevo.com/'],
    ['Connection', 'keep-alive']
]

DEBUG = config.get_setting("debug")

def isGeneric():
    return True

def mainlist(item):
    logger.info("streamondemand.chimerarevo mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="[COLOR azure]News, guide e recensioni tecnologiche[/COLOR]", action="peliculas", url="http://www.chimerarevo.com/video/", thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"))

    
    return itemlist

def peliculas(item):
    logger.info("streamondemand.chimerarevo peliculas")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url,headers=headers)

    # Extrae las entradas (carpetas)
    patron = '<article[^>]+>.*?'
    patron+= 'href="([^"]+)".*?'
    patron+= 'ng-src="([^"]+)".*?'
    patron+= '<h2[^>]+>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedtitle = scrapedtitle.strip()
        scrapedplot = scrapedtitle
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="findvideos", fulltitle=scrapedtitle, show=scrapedtitle, title=scrapedtitle, url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    # Extrae el paginador
    patronvideos  = '<span ng-if="(.*?)">Mostra più Post'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches)>0:
        scrapedurl = urlparse.urljoin(item.url,matches[0])
        itemlist.append( Item(channel=__channel__, action="peliculas", title="[COLOR orange]Avanti >>[/COLOR]" , url=scrapedurl , folder=True) )

    return itemlist

