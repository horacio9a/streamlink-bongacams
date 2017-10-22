# Bongacams Streamlink FFMPG/FFPLAY Plugin v.1.0.0 by @horacio9a - Credits to @sdfwv for Python 2.7.13

import sys, os, json, re, time, datetime, command

from streamlink.compat import urljoin, urlparse, urlunparse
from streamlink.exceptions import PluginError, NoStreamsError
from streamlink.plugin.api import validate, http, useragents
from streamlink.plugin import Plugin
from streamlink.stream import HLSStream
from streamlink.utils import update_scheme
from colorama import init, Fore, Back, Style
from termcolor import colored
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('config.cfg')

init()
print(colored(" => START <= ", "yellow", "on_blue"))
print

CONST_AMF_GATEWAY_LOCATION = '/tools/amf.php'
CONST_AMF_GATEWAY_PARAM = 'x-country'
CONST_DEFAULT_COUNTRY_CODE = 'en'

CONST_HEADERS = {}
CONST_HEADERS['User-Agent'] = useragents.CHROME

url_re = re.compile(r"(http(s)?://)?(\w{2}.)?(bongacams\.com)/([\w\d_-]+)")

amf_msg_schema = validate.Schema({
    "status": "success",
    "userData": {
        "username": validate.text
    },
    "localData": {
        "videoServerUrl": validate.text
    },
    "performerData": {
        "username": validate.text,
    }
})

class bongacams(Plugin):
    @classmethod
    def can_handle_url(self, url):
        return url_re.match(url)

    def _get_streams(self):
        match = url_re.match(self.url)

        stream_page_scheme = 'https'
        stream_page_domain = match.group(4)
        stream_page_path = match.group(5)
        country_code = CONST_DEFAULT_COUNTRY_CODE

        # create http session and set headers
        http_session = http
        http_session.headers.update(CONST_HEADERS)

        # get cookies
        r = http_session.get(urlunparse((stream_page_scheme, stream_page_domain, stream_page_path, '', '', '')))

        # redirect to profile page means stream is offline
        if '/profile/' in r.url:
            print(colored("\n => Performer is OFFLINE <=","yellow","on_red"))
            print
            raise NoStreamsError(self.url)
        if not r.ok:
            self.logger.debug("Status code for {0}: {1}", r.url, r.status_code)
            raise NoStreamsError(self.url)
        if len(http_session.cookies) == 0:
            raise PluginError("Can't get a cookies")

        if urlparse(r.url).netloc != stream_page_domain:
            # then redirected to regional subdomain
            country_code = urlparse(r.url).netloc.split('.')[0].lower()

        # time to set variables
        baseurl = urlunparse((stream_page_scheme, urlparse(r.url).netloc, '', '', '', ''))
        amf_gateway_url = urljoin(baseurl, CONST_AMF_GATEWAY_LOCATION)
        stream_page_url = urljoin(baseurl, stream_page_path)

        headers = {
            'User-Agent': useragents.CHROME,
            'Referer': stream_page_url,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }

        data = 'method=getRoomData&args%5B%5D={0}&args%5B%5D=false'.format(stream_page_path)
        self.logger.debug('DATA: {0}'.format(str(data)))
        # send request and close http-session
        r = http_session.post(url=amf_gateway_url,
                              headers=headers,
                              params={CONST_AMF_GATEWAY_PARAM: country_code},
                              data=data)
        http_session.close()

        if r.status_code != 200:
            raise PluginError("unexpected status code for {0}: {1}", r.url, r.status_code)

        stream_source_info = amf_msg_schema.validate(json.loads(r.text))
        self.logger.debug("source stream info:\n{0}", stream_source_info)

        if not stream_source_info:
            return

        performer = stream_source_info['performerData']['username']
        print (colored("\n => Performer => {} <=", "yellow", "on_blue")).format(performer)
        urlnoproto = stream_source_info['localData']['videoServerUrl']
        urlnoproto = update_scheme('https://', urlnoproto)
        print (colored("\n => Server URL => {} <=", "yellow", "on_blue")).format(urlnoproto)
        hls_url = '{0}/hls/stream_{1}/playlist.m3u8'.format(urlnoproto, performer)

        if hls_url:
         try:
          for s in HLSStream.parse_variant_playlist(self.session, hls_url, headers=headers).items():
           while True:
            try:
             print
             mode = int(raw_input(colored(" => Select mode: REC(1) or PLAY(0) => ", "yellow", "on_blue")))
             break
            except ValueError:
             print(colored("\n => Input must be a number <=", "yellow", "on_red"))
           if mode == 0:
             mod = 'PLAY'
           if mode == 1:
             mod = 'REC'

           timestamp = str(time.strftime("%d%m%Y-%H%M%S"))
           stime = str(time.strftime("%H:%M:%S"))
           path = config.get('folders', 'output_folder')
           filename = performer + '_BC_' + timestamp + '.flv'
           pf = (path + filename)
           ffmpeg = config.get('files', 'ffmpeg')
           ffplay = config.get('files', 'ffplay')

           if mod == 'PLAY':
            print
            print (colored(" => PLAY => {} <=", "yellow", "on_magenta")).format(filename)
            print
            command = ('start {} -i {} -infbuf -autoexit -window_title "{} * {} * {}"'.format(ffplay,hls_url,performer,stime,urlnoproto))
            os.system(command)
            print(colored(" => END <= ", "yellow","on_blue"))
            sys.exit()

           if mod == 'REC':
            print
            print (colored(" => PLAY => {} <=", "white", "on_magenta")).format(filename)
            print
            command = ('start {} -i {} -infbuf -autoexit -window_title "{} * {} * {}"'.format(ffplay,hls_url,performer,stime,urlnoproto))
            os.system(command)
            print (colored(" => REC => {} <=","yellow","on_red")).format(filename)
            print
            command = ('start {} -i {} -c:v copy -c:a aac -b:a 160k {}'.format(ffmpeg,hls_url,pf))
            os.system(command)
            print(colored(" => END <= ", "yellow","on_blue"))
            sys.exit()

         except Exception as e:
            if '404' in str(e):
               print(colored("\n => Performer is AWAY or PRIVATE <=","yellow","on_red"))
               print
            else:
               self.logger.error(str(e))
            return

__plugin__ = bongacams
