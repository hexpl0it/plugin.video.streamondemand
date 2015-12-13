# -*- coding: utf-8 -*-
#------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para thelordofstreaming - Thank you robalo!
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
#------------------------------------------------------------
import re
import sys

from core import logger
from core import config
from core import scrapertools
from core.item import Item

__channel__ = "lordofstreaming"
__category__ = "S"
__type__ = "generic"
__title__ = "The Lord Of Streaming"
__language__ = "IT"

headers = [
    ['Host','www.thelordofstreaming.it'],
    ['User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'],
    ['Accept-Encoding','gzip, deflate']
]

DEBUG = config.get_setting("debug")

host = "http://www.thelordofstreaming.it"

def isGeneric():
    return True

def mainlist( item ):
    logger.info( "streamondemand.channels.lordofstreaming mainlist" )

    itemlist = []

    itemlist.append( Item( channel=__channel__, action="news", title="[COLOR azure]Novità[/COLOR]", url=host , thumbnail="http://i58.tinypic.com/2zs64cz.jpg" ) )
    itemlist.append( Item( channel=__channel__, action="series", title="[COLOR azure]Serie TV[/COLOR]", url=host + "/category/serie-tv/" , thumbnail="http://i58.tinypic.com/2zs64cz.jpg" ) )
    itemlist.append( Item( channel=__channel__, action="movies", title="[COLOR azure]Film[/COLOR]", url=host + "/category/movie/" , thumbnail="http://i58.tinypic.com/2zs64cz.jpg" ) )
    itemlist.append( Item( channel=__channel__, action="search", title="[COLOR yellow]Cerca...[/COLOR]" , thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search" ) )

    return itemlist

def search(item, texto):
    logger.info("streamondemand.channels.guardaserie search")

    item.url=host + "/?s=" + texto

    return cerca( item )

    try:
        ## Se tiene que incluir aquí el nuevo scraper o crear una nueva función para ello
        return cerca( item )

    ## Se captura la excepción, para no interrumpir al buscador global si un canal falla.
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def series( item ):
    logger.info( "streamondemand.channels.guardaserie fichas" )

    itemlist = []

    data = scrapertools.cache_page( item.url )

    data = scrapertools.find_single_match( data, '<a[^>]+>Serie Tv</a><ul>(.*?)</ul>' )

    patron  = '<li><a href="([^"]+)[^>]+>([^<]+)</a></li>'

    matches = re.compile( patron, re.DOTALL ).findall( data )

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append( Item( channel=__channel__, action="episodios", title= scrapedtitle , fulltitle=scrapedtitle, show=scrapedtitle, url=scrapedurl ) )

    return itemlist

def movies( item ):
    logger.info( "streamondemand.channels.guardaserie fichas" )

    itemlist = []

    data = scrapertools.cache_page( item.url )

    data = scrapertools.find_single_match( data, '<a[^>]+>Anime</a><ul>(.*?)</ul>' )

    patron  = '<li><a href="([^"]+)[^>]+>([^<]+)</a></li>'

    matches = re.compile( patron, re.DOTALL ).findall( data )

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append( Item( channel=__channel__, action="episodios", title= scrapedtitle , fulltitle=scrapedtitle, show=scrapedtitle, url=scrapedurl, thumbnail="http://www.itrentenni.com/wp-content/uploads/2015/02/tv-series.jpg" ) )

    return itemlist


def cerca( item ):
    logger.info( "streamondemand.channels.guardaserie fichas" )

    itemlist = []

    data = scrapertools.cache_page( item.url )

    patron  = '<h1 class="entry-title"><a href="(.*?)" rel="bookmark">(.*?)<\/a><\/h1>'

    matches = re.compile( patron, re.DOTALL ).findall( data )

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if bool(re.search('.*Serie TV', scrapedtitle)) :
            itemlist.append( Item( channel=__channel__, action="stagioni",title= scrapedtitle , fulltitle=scrapedtitle, url=scrapedurl, show=scrapedtitle) )

    return itemlist

def stagioni(item):
    logger.info("streamondemand.channels.guardaserie stagioni")

    itemlist = []

    data = scrapertools.cache_page( item.url )

    patron  = '<p.*?> *<strong> *<em> *(.*?) *<\/em> *<\/strong> *<span style="color: #ff0000;"> *(.*?) *<\/span> *<br *\/>(.*?) *< *\/p>'

    seasons_episodes = re.compile( patron, re.DOTALL ).findall( data )

    for scrapedseason, scrapedelanguage, htmlEpisodi in seasons_episodes:
        scrapedseason = scrapertools.decodeHtmlentities(scrapedseason)
        scrapedelanguage = scrapertools.decodeHtmlentities(scrapedelanguage)
        itemlist.append( Item( channel=__channel__, title= scrapedseason + " " + scrapedelanguage, fulltitle=scrapedseason + " " + scrapedelanguage, show=scrapedseason + " " + scrapedelanguage, folder=False ) )
        itemlist += episodi(htmlEpisodi)

    if config.get_library_support():
        itemlist.append( Item(channel=__channel__, title="[COLOR azure]Aggiungi [/COLOR]" + item.title + "[COLOR azure] alla libreria di Kodi[/COLOR]", url=item.url, action="add_serie_to_library", extra="episodios", show=item.show) )
        itemlist.append( Item(channel=__channel__, title="[COLOR azure]Scarica tutti gli episodi della serie[/COLOR]", url=item.url, action="download_all_episodes", extra="episodios", show=item.show) )

    return itemlist

def episodi(data):
    logger.info("streamondemand.channels.guardaserie episodi")

    itemlist = []

    seasons_episodes = re.compile( '(\d+×\d+) *(<a href=".*?\n)', re.DOTALL ).findall( data )

    for episodesnumber, episodeslinks in seasons_episodes:
        episodeslinks = scrapertools.decodeHtmlentities(episodeslinks)
        links = re.compile( '<a href="(.*?)".*?>(.*?)<', re.DOTALL ).findall( episodeslinks )
        for link, host in links:
            itemlist.append( Item( channel=__channel__, action="play",server=host, title= episodesnumber + " - " + host, url=link, fulltitle=episodesnumber + " - " + host, show=episodesnumber + " - " + host) )

    return itemlist
