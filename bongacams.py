# Bongacams Streamlink RTMPDUMP Remote 24/7 Plugin v.1.0.3 by @horacio9a for Python 2.7.14 - Credits also to @sdfwv
# coding: utf-8

import sys, os, json, re, time, datetime, random, command
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

CONST_AMF_GATEWAY_LOCATION = '/tools/amf.php'
CONST_AMF_GATEWAY_PARAM = 'x-country'
CONST_DEFAULT_COUNTRY_CODE = 'en'

CONST_HEADERS = {}
CONST_HEADERS['User-Agent'] = useragents.CHROME

url_re = re.compile(r'(http(s)?://)?(\w{2}.)?(bongacams\.com)/([\w\d_-]+)')

amf_msg_schema = validate.Schema(
 {'status': 'success','userData': 
  {'username': validate.text},'localData': 
   {'videoServerUrl': validate.text},'performerData': 
    {'username': validate.text,'displayName': validate.text,'userId': validate.get}})

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
           print(colored('\n => Performer is OFFLINE <=','yellow','on_red'))
           print(colored('\n => END <= ', 'yellow','on_blue'))
           time.sleep(6)
           sys.exit()

        if not r.ok:
            self.logger.debug('Status code for {0}: {1}', r.url, r.status_code)
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
            raise PluginError('unexpected status code for {0}: {1}', r.url, r.status_code)

        stream_source_info = amf_msg_schema.validate(json.loads(r.text))
        self.logger.debug('source stream info:\n{0}', stream_source_info)

        if not stream_source_info:
            return

        performer = stream_source_info['performerData']['username']
        real_name = stream_source_info['performerData']['displayName']
        performer_id = stream_source_info['performerData']['userId']
        print (colored('\n => Performer => {} <=', 'yellow', 'on_blue')).format(real_name)
        print (colored('\n => Performer ID => {} <=', 'yellow', 'on_blue')).format(performer_id)
        urlnoproto = stream_source_info['localData']['videoServerUrl']
        urlnoproto = update_scheme('https://', urlnoproto)
        hls_url = '{0}/hls/stream_{1}/playlist.m3u8'.format(urlnoproto, performer)
        server = re.sub('https://', '', urlnoproto)
        print (colored('\n => Server => {} <=', 'yellow', 'on_blue')).format(server)

        if hls_url:
         try:
          for s in HLSStream.parse_variant_playlist(self.session, hls_url, headers=headers).items():
           timestamp = str(time.strftime('%d%m%Y-%H%M%S'))
           path = config.get('folders', 'output_folder_BC')
           fn = real_name + '_BC_' + timestamp + '.flv'
           pf = (path + fn)
           rtmp = config.get('files', 'rtmpdump')
           uidn = random.randint(1000000,9999999)
           uid = '150318{}'.format(uidn)
           print (colored('\n => RTMP-24/7-REC => {} <=', 'yellow', 'on_red')).format(fn)
           command = '{} -r"rtmp://{}/bongacams" -m 2 -q -y"stream_{}?uid={}" -o"{}"'.format(rtmp,server,performer,uid,pf)
           os.system(command)
           print(colored('\n => END <= ', 'yellow','on_blue'))
           sys.exit()

         except Exception as e:
          if '404' in str(e):
           print(colored('\n => Performer is AWAY or PRIVATE <=','yellow','on_red'))
           print(colored('\n => END <= ', 'yellow','on_blue'))
           time.sleep(6)
           sys.exit()

__plugin__ = bongacams
