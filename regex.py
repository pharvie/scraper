def get():
    regex = {
        'm3u_fmt': r'(mpegurl)|(m3u8?)|(octet-stream)|(plain)',
        'zip_fmt': r'zip',
        'html_fmt': r'html',
        'identity': r'(.+)(www\.)(.+)',
        'port': r'(.+?)(:\d{1,10})(.+)?',
        'top': r'(.+)\.((?:.(?!\.))+)$',
        'short': r'(ift\.tt)|(bit\.(ly)|(bit\.do\/))|(bc\.vc)|(goo\.gl)|(link\.tl)',
        'ip': r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])',
        'm3u': r'(\.m3u8?)|(&?type=m3u8?)',
        'streams': r'(\.ts)|(\.mp4)|(\.mkv)|(\.ch)|(\.mpg)|(\/mpegts)|(stream\/channelid\/\d{1,14})|(\/udp\/'
                    r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):\d{4})|'
                    r'(\/play\/[as]0?[\d\w]{1,2})|(\/live\?channelid)',
        'dl': r'(=download)|(dl=)|(\/playlist)$|(\/playlist\/)|(rndad=)',
        'ndl': r'(\/playlist\/page)|(tag\/playlist\/)',
        'zip': r'(\.zip)|(&?type=zip)',
        'raw': r'(pastebin\.com\/raw\/.{8})$',
        'invalid': r'(#)|(javascript:(%\d+)?void\(0\))|(^\/$)|(\.png)|(\.jpeg)',
        'ext': r'^#(EXT)|(MY)',
        'whitespace': r'^\s*$',
        'params': r'(.+?)(\??&.+)',
        'end': r'(.+)\/$',
        'ignore': r'(blogger)|(facebook)|(plus\.google)|(blogspot)|(linkedin)',
        'pure': r'^[\w\d]+$',
        'phrases': r'[\w\d]+',
        'metacharacters': r'^[\w\d]'
    }
    return regex