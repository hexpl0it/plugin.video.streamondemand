# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para vediserie - based on seriehd channel
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
# ------------------------------------------------------------
import urllib2
import re
import sys
import time
import binascii

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "vediserie"
__category__ = "S"
__type__ = "generic"
__title__ = "Vedi Serie"
__language__ = "IT"

headers = [
    ['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'],
    ['Accept-Encoding', 'gzip, deflate']
]

host = "http://www.vediserie.com"


def isGeneric():
    return True


def mainlist(item):
    logger.info("[vediserie.py] mainlist")

    itemlist = [Item(channel=__channel__,
                     action="fichas",
                     title="[COLOR azure]Serie TV[/COLOR]",
                     url=host,
                     thumbnail="http://i.imgur.com/rO0ggX2.png"),
                Item(channel=__channel__,
                     action="list_a_z",
                     title="[COLOR orange]Ordine Alfabetico A-Z[/COLOR]",
                     url="http://www.vediserie.com/lista-completa-serie-tv/",
                     thumbnail="http://i37.photobucket.com/albums/e88/xzener/NewIcons.png"),
                Item(channel=__channel__,
                     action="search",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def search(item, texto):
    logger.info("[vediserie.py] search")

    item.url = host + "/?s=" + texto

    try:
        return fichas(item)

    ## Se captura la excepción, para no interrumpir al buscador global si un canal falla.
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_a_z(item):
    logger.info("[vediserie.py] ordine alfabetico")
    itemlist = []

    data = anti_cloudflare(item.url)

    patron = '<li><a href="(.*?)" title="(.*?)">.*?</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl))

    return itemlist

def fichas(item):
    logger.info("[vediserie.py] fichas")
    itemlist = []

    data = anti_cloudflare(item.url)

    ## ------------------------------------------------
    cookies = ""
    matches = re.compile('(.vediserie.com.*?)\n', re.DOTALL).findall(config.get_cookie_data())
    for cookie in matches:
        name = cookie.split('\t')[5]
        value = cookie.split('\t')[6]
        cookies += name + "=" + value + ";"
    headers.append(['Cookie', cookies[:-1]])
    import urllib
    _headers = urllib.urlencode(dict(headers))
    ## ------------------------------------------------

    patron  = '<h2>[^>]+>\s*'
    patron += '<img[^=]+=[^=]+=[^=]+="(.*?)"[^>]+>\s*'
    patron += '<A HREF=(.*?)>[^>]+>[^>]+>[^>]+>\s*'
    patron += '[^>]+>[^>]+>(.*?)</[^>]+>[^>]+>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedthumbnail += "|" + _headers
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if scrapedtitle.startswith('<span class="year">'):
            scrapedtitle = scrapedtitle[19:]
        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail))

    patron = '<a class="nextpostslink" rel="next" href="(.*?)">»</a>'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title="[COLOR orange]Successivo>>[/COLOR]",
                 url=next_page))

    return itemlist

def episodios(item):
    logger.info("[vediserie.py] episodios")

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
                     title=title,
                     url=url,
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
    logger.info("[vediserie.py] findvideos")

    url = item.url.split('?')[0]
    post = item.url.split('?')[1]
    referer = item.url.split('?')[2]

    headers.append(['Referer', referer])

    data = scrapertools.cache_page(url, post=post, headers=headers)

    patron = '<iframe id="iframeVid" width="100%" height="500px" src="([^"]+)" allowfullscreen></iframe>'
    url = scrapertools.find_single_match(data, patron)

    if 'hdpass.link' in url:
        data = scrapertools.cache_page(url, headers=headers)

        patron = '<iframe width="100%" height="100%" src="([^"]+)" frameborder="0" scrolling="no" allowfullscreen />'
        url_tmp = scrapertools.find_single_match(data, patron)

        if url_tmp == '':
            data = scrapertools.cache_page(url + '&randid=0', headers=headers)
            patron = r'; eval\(unescape\("(.*?)",(\[".*?;"\]),(\[".*?\])\)\);'
            [(par1, par2, par3)] = re.compile(patron, re.DOTALL).findall(data)
            par2 = eval(par2, {'__builtins__': None}, {})
            par3 = eval(par3, {'__builtins__': None}, {})
            url = unescape(par1, par2, par3)
            url = scrapertools.find_single_match(url, r'tvar Data = \\"([^\\]+)\\";')
            url = binascii.unhexlify(url).replace(r'\/', '/')
        else:
            url = url_tmp

    itemlist = servertools.find_video_items(data=url)

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
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


def unescape(par1, par2, par3):
    var1 = par1
    for ii in xrange(0, len(par2)):
        var1 = re.sub(par2[ii], par3[ii], var1)

    var1 = re.sub("%26", "&", var1)
    var1 = re.sub("%3B", ";", var1)
    return var1.replace('<!--?--><?', '<!--?-->')
