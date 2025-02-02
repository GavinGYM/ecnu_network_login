import js2py
import hmac
import hashlib
import requests
import time
import json
import socket


def get_host_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_timestamp() -> int:
    return int(round(time.time() * 1000))


def get_token(username: str, ip: str, timestamp: int) -> str:
    content = json.loads(requests.get(f"https://login.ecnu.edu.cn/cgi-bin/get_challenge?callback=x&username={username}&ip={ip}&_={timestamp}").content[2:-1]) 
    return content['challenge']


def hmac_md5(password: str, token: str) -> str:
    mac = hmac.new(token.encode(), password.encode(), hashlib.md5) 
    mac.digest()
    return mac.hexdigest()


def get_info(username: str, password: str, ip: str, token: str) -> str:
    context = js2py.EvalJs()
    context.execute('''
var _PADCHAR = '=';
function encode(str, key) {
    if (str === '') return '';
    var v = s(str, true);
    var k = s(key, false);
    if (k.length < 4) k.length = 4;
    var n = v.length - 1,
        z = v[n],
        y = v[0],
        c = 0x86014019 | 0x183639A0,
        m,
        e,
        p,
        q = Math.floor(6 + 52 / (n + 1)),
        d = 0;

    while (0 < q--) {
        d = d + c & (0x8CE0D9BF | 0x731F2640);
        e = d >>> 2 & 3;

        for (p = 0; p < n; p++) {
            y = v[p + 1];
            m = z >>> 5 ^ y << 2;
            m += y >>> 3 ^ z << 4 ^ (d ^ y);
            m += k[p & 3 ^ e] ^ z;
            z = v[p] = v[p] + m & (0xEFB8D130 | 0x10472ECF);
        }

        y = v[0];
        m = z >>> 5 ^ y << 2;
        m += y >>> 3 ^ z << 4 ^ (d ^ y);
        m += k[p & 3 ^ e] ^ z;
        z = v[n] = v[n] + m & (0xBB390742 | 0x44C6F8BD);
    }

    return l(v, false);
}

function s(a, b) {
    var c = a.length;
    var v = [];

    for (var i = 0; i < c; i += 4) {
        v[i >> 2] = a.charCodeAt(i) | a.charCodeAt(i + 1) << 8 | a.charCodeAt(i + 2) << 16 | a.charCodeAt(i + 3) << 24;
    }

    if (b) v[v.length] = c;
    return v;
}

function l(a, b) {
    var d = a.length;
    var c = d - 1 << 2;

    if (b) {
        var m = a[d - 1];
        if (m < c - 3 || m > c) return null;
        c = m;
    }

    for (var i = 0; i < d; i++) {
        a[i] = String.fromCharCode(a[i] & 0xff, a[i] >>> 8 & 0xff, a[i] >>> 16 & 0xff, a[i] >>> 24 & 0xff);
    }

    return b ? a.join('').substring(0, c) : a.join('');
}

function _getbyte(s, i) {
    var x = s.charCodeAt(i);
    if (x > 255) {
        throw "INVALID_CHARACTER_ERR: DOM Exception 5"
    }
    return x
}
function base64(s) {
    var _ALPHA = "LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA";
    if (arguments.length !== 1) {
        throw "SyntaxError: exactly one argument required"
    }
    s = String(s);
    var i, b10, x = [], imax = s.length - s.length % 3;
    if (s.length === 0) {
        return s
    }
    for (i = 0; i < imax; i += 3) {
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8) | _getbyte(s, i + 2);
        x.push(_ALPHA.charAt(b10 >> 18));
        x.push(_ALPHA.charAt((b10 >> 12) & 63));
        x.push(_ALPHA.charAt((b10 >> 6) & 63));
        x.push(_ALPHA.charAt(b10 & 63))
    }
    switch (s.length - imax) {
        case 1:
            b10 = _getbyte(s, i) << 16;
            x.push(_ALPHA.charAt(b10 >> 18) + _ALPHA.charAt((b10 >> 12) & 63) + _PADCHAR + _PADCHAR);
            break;
        case 2:
            b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8);
            x.push(_ALPHA.charAt(b10 >> 18) + _ALPHA.charAt((b10 >> 12) & 63) + _ALPHA.charAt((b10 >> 6) & 63) + _PADCHAR);
            break
    }
    return x.join("")
}
    ''')
    result = context.encode("{\"username\":\"" + username + "\",\"password\":\"" + password + "\",\"ip\":\"" + ip + "\",\"acid\":\"1\",\"enc_ver\":\"srun_bx1\"}", token)
    result = "{SRBX1}" + context.base64(result)
    return result


def get_chksum(token: str, username: str, password_hmd5: str, ip: str, info: str) -> str:
    all = token + username + token + password_hmd5 + token + "1" + token + ip + token + "200" + token + "1" + token + info
    return hashlib.sha1(all.encode()).hexdigest()
