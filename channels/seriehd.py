# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para seriehd - based on guardaserie channel
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
# ------------------------------------------------------------
import urllib2
import re
import sys
import time

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "seriehd"
__category__ = "S"
__type__ = "generic"
__title__ = "Serie HD"
__language__ = "IT"

headers = [
    ['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'],
    ['Accept-Encoding', 'gzip, deflate']
]

host = "http://www.seriehd.org"


def isGeneric():
    return True


def mainlist(item):
    logger.info("[seriehd.py] mainlist")

    itemlist = [Item(channel=__channel__,
                     action="fichas",
                     title="[COLOR azure]Serie TV[/COLOR]",
                     url=host + "/serie-tv-streaming/",
                     thumbnail="http://i.imgur.com/rO0ggX2.png"),
                Item(channel=__channel__,
                     action="sottomenu",
                     title="[COLOR orange]Sottomenu...[/COLOR]",
                     url=host,
                     thumbnail="http://i37.photobucket.com/albums/e88/xzener/NewIcons.png"),
                Item(channel=__channel__,
                     action="search",
                     title="[COLOR green]Cerca...[/COLOR]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def search(item, texto):
    logger.info("[seriehd.py] search")

    item.url = host + "/?s=" + texto

    try:
        return fichas(item)

    ## Se captura la excepción, para no interrumpir al buscador global si un canal falla.
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sottomenu(item):
    logger.info("[seriehd.py] sottomenu")
    itemlist = []

    data = anti_cloudflare(item.url)

    patron = '<a href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl))

    ## Elimina 'Serie TV' de la lista de 'sottomenu'
    itemlist.pop(0)

    return itemlist


def fichas(item):
    logger.info("[seriehd.py] fichas")
    itemlist = []

    data = anti_cloudflare(item.url)

    ## ------------------------------------------------
    cookies = ""
    matches = re.compile('(.seriehd.org.*?)\n', re.DOTALL).findall(config.get_cookie_data())
    for cookie in matches:
        name = cookie.split('\t')[5]
        value = cookie.split('\t')[6]
        cookies += name + "=" + value + ";"
    headers.append(['Cookie', cookies[:-1]])
    import urllib
    _headers = urllib.urlencode(dict(headers))
    ## ------------------------------------------------

    patron = '<h2>(.*?)</h2>\s*'
    patron += '<img src="(.*?)" alt=".*?"/>\s*'
    patron += '<A HREF="(.*?)">'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedthumbnail, scrapedurl in matches:
        scrapedthumbnail += "|" + _headers

        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail))

    patron = "<span class='current'>\d+</span><a rel='nofollow' class='page larger' href='([^']+)'>\d+</a>"
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title="[COLOR orange]Successivo>>[/COLOR]",
                 url=next_page))

    return itemlist


def episodios(item):
    logger.info("[seriehd.py] episodios")

    itemlist = []

    data = anti_cloudflare(item.url)

    patron = '<select name="stagione" id="selSt">(.*?)</select>'
    seasons_data = scrapertools.find_single_match(data, patron)
    seasons = re.compile('data-stagione="(\d+)"', re.DOTALL).findall(seasons_data)

    for scrapedseason in seasons:

        patron = '<div class="list[^"]+" data-stagione="' + scrapedseason + '">(.*?)</div>'
        episodes_data = scrapertools.find_single_match(data, patron)
        episodes = re.compile('data-id="(\d+)"', re.DOTALL).findall(episodes_data)

        for scrapedepisode in episodes:

            season = str(int(scrapedseason) + 1)
            episode = str(int(scrapedepisode) + 1)
            if len(episode) == 1: episode = "0" + episode

            title = season + "x" + episode

            ## Le pasamos a 'findvideos' la url con dos partes divididas por el caracter "?"
            ## [host+path]?[argumentos]?[Referer]
            url = item.url + "?st_num=" + scrapedseason + "&pt_num=" + scrapedepisode + "?" + item.url

            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     title=title, url=url,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     thumbnail=item.thumbnail))

    if config.get_library_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=__channel__,
                 title=item.title,
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))
        itemlist.append(
            Item(channel=item.channel,
                 title="Scarica tutti gli episodi della serie",
                 url=item.url,
                 action="download_all_episodes",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[seriehd.py] findvideos")

    itemlist = []

    url = item.url.split('?')[0]
    post = item.url.split('?')[1]
    referer = item.url.split('?')[2]

    headers.append(['Referer', referer])

    data = scrapertools.cache_page(url, post=post, headers=headers)

    patron = '<iframe id="iframeVid" width="100%" height="500px" src="([^"]+)" allowfullscreen></iframe>'
    url = scrapertools.find_single_match(data, patron)

    server = url.split('/')[2]

    title = "[" + server + "] " + item.title

    itemlist.append(
        Item(channel=__channel__,
             action="play",
             title=title,
             url=url,
             fulltitle=item.fulltitle,
             show=item.show,
             thumbnail=item.thumbnail,
             folder=False))

    return itemlist


def play(item):
    logger.info("[seriehd.py] play")

    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.show
        videoitem.show = item.show
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__

    return itemlist


def anti_cloudflare(url):
    # global headers

    try:
        resp_headers = scrapertools.get_headers_from_response(url, headers=headers)
        resp_headers = dict(resp_headers)
    except urllib2.HTTPError, e:
        resp_headers = e.headers

    if 'refresh' in resp_headers:
        time.sleep(int(resp_headers['refresh'][:1]))

        scrapertools.get_headers_from_response(host + "/" + resp_headers['refresh'][7:], headers=headers)

    return scrapertools.cache_page(url, headers=headers)
