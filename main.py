#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BoxTool v5.0
作者：Seem
"""
import os, sys, threading, time
from pathlib import Path

os.environ["KIVY_AUDIO"] = ""
os.environ["KIVY_WINDOW"] = "sdl2"
os.environ["KIVY_GL_BACKEND"] = "sdl2"

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.metrics import dp

# ---- 字体 ----
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "simhei.ttf")
HAS_FONT = os.path.exists(FONT_PATH)
if HAS_FONT:
    LabelBase.register(name="ZH", fn_regular=FONT_PATH)
FONT = "ZH" if HAS_FONT else "Roboto"

# ---- 窗口设置 ----
Window.set_title("BoxTool v1.0 - 渗透工具箱")
Window.size = (1024, 720)
Window.minimum_width, Window.minimum_height = (900, 650)
Window.clearcolor = (0.93, 0.94, 0.96, 1)

# ---- 导入引擎 ----
sys.path.insert(0, str(Path(__file__).parent))
try:
    import engine
    ENGINE_OK = True
    ENGINE_ERR = ""
except Exception as e:
    ENGINE_OK = False
    ENGINE_ERR = str(e)

# ============== QQ 风格颜色表 ==============
class C:
    TITLE   = (0.15, 0.52, 0.88, 1)
    SIDE    = (0.91, 0.93, 0.95, 1)
    BTN     = (0.18, 0.58, 0.92, 1)
    BTN_P   = (0.12, 0.44, 0.78, 1)
    DARK    = (0.16, 0.18, 0.22, 1)
    LIGHT   = (1, 1, 1, 1)
    GRAY    = (0.50, 0.52, 0.58, 1)
    BORDER  = (0.74, 0.77, 0.82, 1)
    GREEN   = (0.18, 0.80, 0.30, 1)
    RED     = (0.88, 0.25, 0.25, 1)
    ORANGE  = (0.95, 0.58, 0.10, 1)
    WHITE   = (1, 1, 1, 1)

# ============== 自定义 QQ 风格组件 ==============
class QQButton(Button):
    """QQ 风格圆角渐变按钮"""
    def __init__(self, bg=None, **kw):
        self._bg = bg or C.BTN
        super().__init__(**kw)
        self.font_name = FONT
        self.font_size = dp(13)
        self.color = C.LIGHT
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint_y = None
        self.height = dp(40)
        self.bind(pos=self._draw, size=self._draw, state=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 0.10)
            RoundedRectangle(pos=(self.x + 2, self.y - 2),
                           size=self.size, radius=[dp(6)])
            Color(*(C.BTN_P if self.state == "down" else self._bg))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(1, 1, 1, 0.18)
            RoundedRectangle(pos=(self.x, self.y + self.height * 0.55),
                           size=(self.width, self.height * 0.45),
                           radius=[dp(6), dp(6), 0, 0])

class SideButton(Button):
    """侧边栏功能按钮"""
    def __init__(self, cb=None, tag="", **kw):
        self._tag = tag
        self._cb = cb
        self._sel = False
        super().__init__(**kw)
        self.font_name = FONT
        self.font_size = dp(12.5)
        self.color = C.DARK
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint_y = None
        self.height = dp(40)
        self.halign = "left"
        self.valign = "center"
        self.padding = [dp(16), 0]
        self.bind(pos=self._draw, size=self._draw, on_release=self._do)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == "down":
                Color(*C.BTN)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            elif self._sel:
                Color(0.18, 0.58, 0.92, 0.08)
                Rectangle(pos=self.pos, size=self.size)
                Color(*C.BTN)
                Rectangle(pos=(self.x, self.y), size=(dp(3.5), self.height))

    def _do(self, *a):
        if self._cb:
            self._cb(self._tag)

    @property
    def selected(self):
        return self._sel

    @selected.setter
    def selected(self, v):
        self._sel = v
        self._draw()

class GroupHeader(Button):
    """折叠分组标题"""
    def __init__(self, tag="", **kw):
        self._tag = tag
        self._exp = True
        self._orig = kw.pop("text", "")
        super().__init__(**kw)
        self.font_name = FONT
        self.font_size = dp(11.5)
        self.color = C.GRAY
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint_y = None
        self.height = dp(30)
        self.halign = "left"
        self.valign = "center"
        self.padding = [dp(10), 0]
        self.text = self.text or self._orig
        self.bind(pos=self._draw, size=self._draw, on_release=self._tg)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 0.04)
            Rectangle(pos=self.pos, size=self.size)

    def _tg(self, *a):
        self._exp = not self._exp
        h = self.text.lstrip("\u25bc\u25b6 ")
        self.text = ("\u25bc " if self._exp else "\u25b6 ") + h
        if hasattr(self.parent, "toggle_group"):
            self.parent.toggle_group(self._tag, self._exp)

class SidebarList(BoxLayout):
    """侧边栏功能列表"""
    def __init__(self, on_select=None, **kw):
        self._cb = on_select
        self._grps = {}
        self._btns = {}
        super().__init__(orientation="vertical", size_hint_y=None, **kw)

    def add_group(self, title, tag, items):
        wg = []
        bd = {}
        h = GroupHeader(text="\u25bc " + title, tag=tag, size_hint_y=None, height=dp(30))
        wg.append(h)
        self.add_widget(h)
        for txt, t in items:
            b = SideButton(text="  " + txt, tag=t, cb=self._cb)
            wg.append(b)
            bd[t] = b
            self.add_widget(b)
            self._btns[t] = b
        self._grps[tag] = {"w": wg, "btns": bd}

    def toggle_group(self, tag, exp):
        if tag not in self._grps:
            return
        for w in self._grps[tag]["w"]:
            if isinstance(w, SideButton):
                w.height = dp(40) if exp else 0
                w.opacity = 1 if exp else 0
                w.disabled = not exp

    def select(self, tag):
        for k, b in self._btns.items():
            b.selected = (k == tag)

# ============== 主界面 ==============
class MainScreen(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self._extra = {}
        self._current_tag = None
        self._build()

    def _build(self):
        # ---- 标题栏 ----
        tb = BoxLayout(size_hint_y=None, height=dp(64), padding=[dp(18), 0, dp(14), 0])
        
        tex = Texture.create(size=(1, 64))
        buf = bytearray()
        for i in range(64):
            r = int(38 + (24 - 38) * i / 63)
            g = int(132 + (102 - 132) * i / 63)
            b = int(220 + (184 - 220) * i / 63)
            buf.extend([r, g, b, 255])
        tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
        
        with tb.canvas.before:
            self._tbr = Rectangle(size=tb.size, texture=tex)
            tb.bind(pos=lambda o, v: setattr(self._tbr, "pos", v),
                    size=lambda o, v: setattr(self._tbr, "size", v))
        
        av = Widget(size_hint_x=None, width=dp(42))
        with av.canvas:
            Color(*C.GREEN)
            Ellipse(pos=(dp(3), dp(7)), size=(dp(34), dp(34)))
            Color(*C.LIGHT)
            RoundedRectangle(pos=(dp(14), dp(17)), size=(dp(16), dp(8)), radius=[dp(4), dp(4), 0, 0])
        tb.add_widget(av)
        
        tb.add_widget(Label(text="[b]BoxTool v1.0 作者：Seem[/b]  ", markup=True,
                          font_size=dp(11), font_name=FONT, color=C.LIGHT,
                          size_hint_x=None, width=dp(200)))
        tb.add_widget(Label(text="渗透测试工具箱", font_size=dp(25),
                          font_name=FONT, color=(1, 1, 1, 0.7)))
        tb.add_widget(Widget())
        tb.add_widget(Label(text="● 在线", font_size=dp(11), font_name=FONT,
                          color=C.GREEN, size_hint_x=None, width=dp(80)))
        self.add_widget(tb)

        # ---- 主体 ----
        body = BoxLayout()

        # 左侧边栏
        sb = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(220))
        with sb.canvas.before:
            Color(*C.SIDE)
            self._sbr = Rectangle(pos=sb.pos, size=sb.size)
            sb.bind(pos=lambda o, v: setattr(self._sbr, "pos", v),
                    size=lambda o, v: setattr(self._sbr, "size", v))

        # 搜索框
        sr = BoxLayout(size_hint_y=None, height=dp(44), padding=[dp(10), dp(6)])
        with sr.canvas.before:
            Color(1, 1, 1, 1)
            self._sbg = RoundedRectangle(pos=sr.pos, size=sr.size, radius=[dp(16)])
            sr.bind(pos=lambda o, v: setattr(self._sbg, "pos", v),
                    size=lambda o, v: setattr(self._sbg, "size", v))
        self._si = TextInput(hint_text="Q 搜索功能...", multiline=False,
                            background_color=(0, 0, 0, 0),
                            foreground_color=C.DARK,
                            cursor_color=C.BTN, font_name=FONT,
                            font_size=dp(12), padding=[dp(12), dp(8)])
        sr.add_widget(self._si)
        sb.add_widget(sr)

        # 功能列表
        sv = ScrollView(bar_width=dp(5), bar_color=(0.7, 0.7, 0.7, 0.5))
        self._tl = SidebarList(on_select=self._sel)
        self._tl.bind(minimum_height=self._tl.setter("height"))
        self._tl.add_group("■ 核心模块", "core", [
            ("🔍 侦察信息收集", "recon"),
            ("📡 专业端口扫描", "scan"),
            ("🌐 Web 渗透测试", "web"),
            ("🔐 密码破解工具", "brute"),
        ])
        self._tl.add_group("■ 高级模块", "adv", [
            ("🎯 Metasploit 渗透", "msf"),
            ("📶 WiFi 渗透测试", "wifi"),
            ("🛡️ 漏洞扫描器", "vulnscanner"),
            ("📊 报告生成", "report"),
        ])
        self._tl.add_group("■ 新增模块", "new", [
            ("🌍 Shodan 侦察", "shodan"),
            ("🤖 AI Web 渗透", "ai"),
        ])
        self._tl.add_group("■ 工具箱", "utils", [
            ("🧰 辅助工具", "utils"),
        ])
        sv.add_widget(self._tl)
        sb.add_widget(sv)

        # 状态栏 - 修复白色遮挡问题
        ft = BoxLayout(size_hint_y=None, height=dp(32), padding=[dp(12), dp(2)])
        with ft.canvas.before:
            Color(0.88, 0.90, 0.93, 1)
            self._ftr = Rectangle(pos=ft.pos, size=ft.size)
            ft.bind(pos=lambda o, v: setattr(self._ftr, "pos", v),
                   size=lambda o, v: setattr(self._ftr, "size", v))
        self._st = Label(text="就绪", font_size=dp(10), font_name=FONT,
                        color=C.GRAY, halign="left", valign="middle")
        ft.add_widget(self._st)
        sb.add_widget(ft)
        body.add_widget(sb)

        # 右侧内容区
        self._ct = BoxLayout(orientation="vertical", padding=dp(10))
        with self._ct.canvas.before:
            Color(0.98, 0.98, 0.99, 1)
            self._ctr = RoundedRectangle(pos=self._ct.pos, size=self._ct.size, radius=[dp(8)])
        self._ct.bind(pos=self._up_ct, size=self._up_ct)
        self._welcome()
        body.add_widget(self._ct)
        self.add_widget(body)

    def _up_ct(self, instance, value):
        self._ctr.pos = (self._ct.x + dp(8), self._ct.y + dp(8))
        self._ctr.size = (self._ct.width - dp(16), self._ct.height - dp(16))

    def _welcome(self):
        self._ct.clear_widgets()
        w = BoxLayout(orientation="vertical", padding=dp(50), spacing=dp(16))
        w.add_widget(Widget())
        w.add_widget(Label(text="[b]BT[/b]", markup=True, font_size=dp(48),
                          color=C.BTN, font_name=FONT))
        w.add_widget(Label(text="[b]BoxTool v1.0[/b]", markup=True,
                          font_size=dp(30), color=C.TITLE, font_name=FONT))
        w.add_widget(Label(text="渗透测试工具箱",
                          font_size=dp(14), color=C.GRAY, font_name=FONT))
        w.add_widget(Label(text="选择左侧功能开始使用",
                          font_size=dp(13), color=C.GRAY, font_name=FONT))
        st = GridLayout(cols=3, spacing=dp(25), size_hint_y=None, height=dp(90),
                       padding=[dp(20), dp(15)])
        for n, t in [("10", "功能模块"), ("50+", "渗透工具"), ("~", "无限")]:
            b = BoxLayout(orientation="vertical")
            b.add_widget(Label(text=n, font_size=dp(26), color=C.BTN,
                              font_name=FONT, bold=True))
            b.add_widget(Label(text=t, font_size=dp(12), color=C.GRAY,
                              font_name=FONT))
            st.add_widget(b)
        w.add_widget(st)
        w.add_widget(Widget())
        self._ct.add_widget(w)

    def _sel(self, tag):
        self._tl.select(tag)
        self._current_tag = tag
        self._st.text = f"当前：{tag}"
        self._load(tag)

    def _load(self, tag):
        self._ct.clear_widgets()
        self._extra = {}
        box = BoxLayout(orientation="vertical", padding=[dp(18), dp(14)], spacing=dp(9))

        titles = {
            "recon": "🔍 侦察信息收集", "scan": "📡 专业端口扫描",
            "web": "🌐 Web 渗透测试", "brute": "🔐 密码破解工具",
            "msf": "🎯 Metasploit 渗透", "wifi": "📶 WiFi 渗透测试",
            "vulnscanner": "🛡️ 漏洞扫描器", "report": "📊 报告生成",
            "shodan": "🌍 Shodan 侦察", "ai": "🤖 AI Web 渗透",
            "utils": "🧰 辅助工具"
        }
        hdr = BoxLayout(size_hint_y=None, height=dp(44))
        hdr.add_widget(Label(text="[b]" + titles.get(tag, tag) + "[/b]",
                           markup=True, font_size=dp(20), color=C.TITLE,
                           font_name=FONT, size_hint_x=None, width=dp(300)))
        box.add_widget(hdr)

        tools, hint = self._tools(tag)
        grid = GridLayout(cols=3, spacing=dp(9), size_hint_y=None)
        n = len(tools)
        grid.height = max((n - 1) // 3 + 1, 1) * dp(48) + dp(10)
        for txt, fn in tools:
            b = QQButton(text=txt)
            b.bind(on_release=lambda _, f=fn: self._go(tag, f))
            grid.add_widget(b)
        box.add_widget(grid)

        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(9))
        self._inp = TextInput(hint_text=hint, multiline=False,
                            font_name=FONT, font_size=dp(12.5),
                            background_color=C.WHITE,
                            foreground_color=C.DARK,
                            cursor_color=C.BTN, padding=[dp(12), dp(9)],
                            size_hint_x=0.75)
        row.add_widget(self._inp)
        go = QQButton(text="▶ 执行", bg=C.GREEN, size_hint_x=0.25)
        go.bind(on_release=lambda _: self._go(tag, "_auto"))
        row.add_widget(go)
        box.add_widget(row)

        if tag == "shodan":
            # API Key 输入
            ek = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(9))
            self._extra["api"] = TextInput(hint_text="Shodan API Key",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.7)
            ek.add_widget(self._extra["api"])
            setb = QQButton(text="✓ 设置", bg=C.ORANGE, size_hint_x=0.3)
            setb.bind(on_release=lambda _: self._set_sk())
            ek.add_widget(setb)
            box.add_widget(ek)
            
            # 位置/组织输入
            ek2 = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(9))
            self._extra["location"] = TextInput(hint_text="城市/组织 (如 Nanjing 或 Nanjing University)",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=1.0)
            ek2.add_widget(self._extra["location"])
            box.add_widget(ek2)

        if tag == "brute":
            # 目标 IP 输入
            ek = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(9))
            self._extra["user"] = TextInput(hint_text="用户名 (默认：root/admin)",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.5)
            ek.add_widget(self._extra["user"])
            # 自动使用内置字典，无需手动输入路径
            box.add_widget(ek)
            
            # 字典信息提示
            dict_info = BoxLayout(size_hint_y=None, height=dp(30), padding=[dp(5), 0])
            dict_label = Label(
                text="[color=666666]使用内置字典：top_passwords.txt (100 个常用密码) | top_usernames.txt[/color]",
                markup=True, font_size=dp(10), font_name=FONT,
                color=C.GRAY, halign="left", size_hint_x=1.0
            )
            dict_info.add_widget(dict_label)
            box.add_widget(dict_info)

        if tag == "utils":
            # 字典生成选项
            ek = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(9))
            self._extra["dict_mode"] = TextInput(hint_text="模式：numeric/lower/mixed/smart (密码) | common/admin (用户名)",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.5)
            ek.add_widget(self._extra["dict_mode"])
            self._extra["dict_size"] = TextInput(hint_text="大小 (MB): 1/10/100 (默认 1MB)",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.5)
            ek.add_widget(self._extra["dict_size"])
            box.add_widget(ek)
            
            dict_info = BoxLayout(size_hint_y=None, height=dp(30), padding=[dp(5), 0])
            dict_label = Label(
                text="[color=666666]生成的字典自动保存到 wordlists/ 文件夹，爆破工具自动调用[/color]",
                markup=True, font_size=dp(10), font_name=FONT,
                color=C.GRAY, halign="left", size_hint_x=1.0
            )
            dict_info.add_widget(dict_label)
            box.add_widget(dict_info)

        if tag == "wifi":
            ek = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(9))
            self._extra["iface"] = TextInput(hint_text="接口 (默认 wlan0mon)",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.4)
            ek.add_widget(self._extra["iface"])
            self._extra["tmac"] = TextInput(hint_text="目标 MAC",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.3)
            ek.add_widget(self._extra["tmac"])
            self._extra["gmac"] = TextInput(hint_text="网关 MAC",
                multiline=False, font_name=FONT, font_size=dp(12),
                background_color=C.WHITE, foreground_color=C.DARK,
                cursor_color=C.BTN, padding=[dp(10), dp(7)], size_hint_x=0.3)
            ek.add_widget(self._extra["gmac"])
            box.add_widget(ek)

        # 输出区域
        box.add_widget(Widget(size_hint_y=1))
        out_frame = BoxLayout(size_hint_y=None, height=dp(280))
        with out_frame.canvas.before:
            Color(1, 1, 1, 1)
            self._outbg = RoundedRectangle(pos=out_frame.pos, size=out_frame.size, radius=[dp(5)])
            out_frame.bind(pos=lambda o, v: setattr(self._outbg, "pos", v),
                          size=lambda o, v: setattr(self._outbg, "size", v))
        sv2 = ScrollView(bar_width=dp(5), bar_color=(0.7, 0.7, 0.7, 0.5))
        self._out = Label(text="▶ 准备就绪...", font_size=dp(12),
                        color=C.DARK, font_name=FONT,
                        size_hint=(1, None),
                        halign="left", valign="top",
                        padding=[dp(10), dp(8)],
                        text_size=(dp(500), None))
        self._out.height = dp(260)
        sv2.add_widget(self._out)
        out_frame.add_widget(sv2)
        box.add_widget(out_frame)
        
        self._ct.add_widget(box)

    def _tools(self, tag):
        m = {
            "recon": ([
                ("Whois 查询", "whois"), ("DNS 收集", "dns"),
                ("子域名枚举", "sub"), ("端口扫描", "port"),
            ], "输入域名/IP..."),
            "scan": ([
                ("存活扫描", "alive"), ("快速端口", "fast"),
                ("全端口 (1-10000)", "full"), ("漏洞扫描", "vuln_s"),
            ], "输入 IP 或网段 (如 192.168.1.0/24)..."),
            "web": ([
                ("SQLMap 扫描", "sql"), ("敏感文件检测", "sen"),
                ("WAF 检测", "waf"),
            ], "输入 URL(如 http://target.com)..."),
            "brute": ([
                ("SSH 爆破 (22)", "ssh"), ("FTP 爆破 (21)", "ftp"),
                ("Web 登录爆破", "web"), ("后台发现", "admin"),
                ("MySQL 爆破", "mysql"), ("Redis 爆破", "redis"),
            ], "输入目标 IP..."),
            "msf": ([
                ("HTTP 扫描", "vuln"), ("SMB 版本", "smb"),
                ("FTP 版本", "ftp_msf"), ("SSH 版本", "ssh_msf"),
                ("MySQL 版本", "mysql"), ("Web 目录", "dir"),
            ], "输入目标 IP..."),
            "wifi": ([
                ("获取网卡", "iface"), ("扫描 WiFi", "scan"),
                ("Deauth 攻击", "deauth"), ("抓取握手包", "hand"),
                ("破解握手包", "crack"),
            ], "输入参数 (SSID 等)..."),
            "vulnscanner": ([
                ("快速扫描 (-F)", "quick"), ("全面扫描 (-A)", "full"),
                ("Nmap 脚本 (--script=vuln)", "vuln_s2"), ("CVE 检测", "cve"),
                ("Web 路径扫描", "web"), ("Heartbleed", "hb"),
            ], "输入 IP 或 URL..."),
            "report": ([
                ("添加高危发现", "high"), ("添加中危发现", "med"),
                ("生成 HTML 报告", "html"), ("导出 JSON", "json"),
            ], "测试目标名称..."),
            "shodan": ([
                ("IP 信息", "ip"), ("域名查询", "domain"),
                ("关键词搜索", "kw"), ("漏洞设备搜索", "vuln"),
                ("地理位置搜索", "geo"),
                ("全部摄像头", "cam_all"),
                ("品牌摄像头", "cam_brand"),
                ("RTSP 摄像头", "cam_rtsp"),
                ("学校摄像头", "cam_school"),
                ("按组织搜索", "cam_org"),
            ], "输入城市名 (如 Nanjing) 或组织名 (如 Nanjing University)..."),
            "ai": ([
                ("信息爬取", "crawl"), ("漏洞扫描", "vuln_s3"),
                ("一键自动化渗透", "auto"),
            ], "输入 URL(如 http://target.com)..."),
            "utils": ([
                ("MD5 哈希", "md5"), ("SHA256 哈希", "sha"),
                ("Base64 编码", "b64e"), ("Base64 解码", "b64d"),
                ("URL 编码", "url_e"), ("URL 解码", "url_d"),
                ("生成密码字典", "dict_pwd"),
                ("生成用户名字典", "dict_user"),
                ("智能密码字典", "dict_smart"),
            ], "输入参数 (密码字典：模式/长度/大小 | 用户名：模式)..."),
        }
        return m.get(tag, ([], "..."))

    def _eg(self, k, d=""):
        o = self._extra.get(k)
        return o.text if o else d

    def _set_out(self, msg):
        def _(dt):
            self._out.text = str(msg)[:4000]
            self._out.text_size = (self._out.width - dp(20), None)
        Clock.schedule_once(_, 0)

    def _set_sk(self):
        k = self._eg("api")
        if hasattr(engine, 'ShodanModule'):
            engine.ShodanModule.set_api_key(k)
        self._set_out("✓ Shodan API Key 已设置!")

    def _go(self, mod, fn):
        t = self._inp.text.strip() if hasattr(self, "_inp") and self._inp else ""
        u = self._eg("user", "")  # 爆破用户名（可选）
        iface = self._eg("iface", "wlan0mon")
        tmac = self._eg("tmac", t)
        gmac = self._eg("gmac", "")
        loc = self._eg("location", "")  # Shodan 位置/组织

        self._out.text = "... 执行中 ..."
        base = os.path.dirname(__file__)

        def work():
            try:
                r = ""
                if mod == "recon":
                    if fn == "whois":    r = engine.ReconModule.whois_lookup(t)
                    elif fn == "dns":    r = engine.ReconModule.dns_collect(t)
                    elif fn == "sub":    r = engine.ReconModule.subdomain_enum(t)
                    elif fn == "port":   r = engine.ReconModule.port_scan(t)
                    elif fn == "_auto":  r = engine.ReconModule.port_scan(t)

                elif mod == "scan":
                    if fn == "alive":    r = engine.ScanModule.alive_scan(t)
                    elif fn == "fast":   r = engine.ScanModule.fast_scan(t)
                    elif fn == "full":   r = engine.ScanModule.full_scan(t)
                    elif fn == "vuln_s": r = engine.ScanModule.vuln_scan(t)
                    elif fn == "_auto":  r = engine.ScanModule.fast_scan(t)

                elif mod == "web":
                    if fn == "sql":      r = engine.WebModule.sqlmap_scan(t)
                    elif fn == "sen":    r = engine.WebModule.sensitive_file_check(t)
                    elif fn == "waf":    r = engine.WebModule.waf_detection(t)
                    elif fn == "_auto":  r = engine.WebModule.sensitive_file_check(t)

                elif mod == "brute":
                    # 自动使用内置字典，无需手动指定
                    if fn == "ssh":      r = engine.BruteModule.ssh_bruteforce(t, 22, u if u else None)
                    elif fn == "ftp":    r = engine.BruteModule.ftp_bruteforce(t, 21, u if u else None)
                    elif fn == "web":    r = "[!] Web 爆破需要自定义表单，请使用高级功能"
                    elif fn == "admin":  r = engine.BruteModule.admin_bruteforce(t)
                    elif fn == "mysql":  r = engine.BruteModule.mysql_bruteforce(t, 3306, u if u else None)
                    elif fn == "redis":  r = engine.BruteModule.redis_bruteforce(t, 6379)
                    elif fn == "_auto":  r = engine.BruteModule.ssh_bruteforce(t, 22)

                elif mod == "msf":
                    if fn == "vuln":     r = engine.MetasploitModule.vuln_scan(t)
                    elif fn == "smb":    r = engine.MetasploitModule.smb_check(t)
                    elif fn == "ftp_msf": r = engine.MetasploitModule.ftp_check(t)
                    elif fn == "ssh_msf": r = engine.MetasploitModule.ssh_check(t)
                    elif fn == "mysql":  r = engine.MetasploitModule.mysql_check(t)
                    elif fn == "dir":    r = engine.MetasploitModule.web_dir_scan(t)
                    elif fn == "_auto":  r = engine.MetasploitModule.vuln_scan(t)

                elif mod == "wifi":
                    if fn == "iface":    r = engine.WifiModule.get_wireless_interfaces()
                    elif fn == "scan":   r = engine.WifiModule.scan_wifi(iface, 10)
                    elif fn == "deauth": r = engine.WifiModule.deauth_attack(tmac, gmac, iface, 50)
                    elif fn == "hand":   r = engine.WifiModule.capture_handshake(iface)
                    elif fn == "crack":  r = engine.WifiModule.crack_handshake(t, wl) if wl else "[!] 需要握手包 + 字典路径"
                    elif fn == "_auto":  r = engine.WifiModule.get_wireless_interfaces()

                elif mod == "vulnscanner":
                    if fn == "quick":    r = engine.VulnScannerModule.quick_scan(t)
                    elif fn == "full":   r = engine.VulnScannerModule.full_scan(t)
                    elif fn == "vuln_s2": r = engine.VulnScannerModule.vuln_scan(t)
                    elif fn == "cve":    r = engine.VulnScannerModule.cve_scan(t)
                    elif fn == "web":    r = engine.VulnScannerModule.web_vuln_scan(t)
                    elif fn == "hb":     r = engine.VulnScannerModule.heartbleed_check(t)
                    elif fn == "_auto":  r = engine.VulnScannerModule.quick_scan(t)

                elif mod == "report":
                    nt = t or "未指定"
                    if fn == "high":
                        try: engine.ReportModule.add_finding("高危", nt, "high")
                        except: pass
                        r = "[+] 已添加高危发现"
                    elif fn == "med":
                        try: engine.ReportModule.add_finding("中危", nt, "medium")
                        except: pass
                        r = "[+] 已添加中危发现"
                    elif fn == "html":
                        p = os.path.join(base, "pentest_report.html")
                        r = engine.ReportModule.generate_report(nt, [], p)
                    elif fn == "json":
                        p = os.path.join(base, "pentest_report.json")
                        r = engine.ReportModule.export_json(p)
                    elif fn == "_auto":
                        p = os.path.join(base, "pentest_report.html")
                        r = engine.ReportModule.generate_report(nt, [], p)

                elif mod == "shodan":
                    if fn == "ip":       r = engine.ShodanModule.ip_info(t)
                    elif fn == "domain": r = engine.ShodanModule.domain_search(t)
                    elif fn == "kw":     r = engine.ShodanModule.keyword_search(t)
                    elif fn == "vuln":   r = engine.ShodanModule.vuln_search(t)
                    elif fn == "geo":    r = engine.ShodanModule.geo_search(39.9, 116.4)
                    elif fn == "cam_all":    r = engine.ShodanModule.camera_search('all', location=loc)
                    elif fn == "cam_brand":  r = engine.ShodanModule.camera_search('hikvision', location=loc)
                    elif fn == "cam_rtsp":   r = engine.ShodanModule.camera_search('rtsp', location=loc)
                    elif fn == "cam_school": r = engine.ShodanModule.camera_search('school', location=loc)
                    elif fn == "cam_org":    r = engine.ShodanModule.camera_search('all', org=loc)
                    elif fn == "_auto":  r = engine.ShodanModule.ip_info(t)

                elif mod == "ai":
                    if fn == "crawl":    r = engine.AIModule.info_crawl(t)
                    elif fn == "vuln_s3": r = engine.AIModule.vuln_scan(t)
                    elif fn == "auto":   r = engine.AIModule.auto_pentest(t)
                    elif fn == "_auto":  r = engine.AIModule.auto_pentest(t)

                elif mod == "utils":
                    if fn == "md5":      r = engine.UtilsModule.md5_hash(t)
                    elif fn == "sha":    r = engine.UtilsModule.sha256_hash(t)
                    elif fn == "b64e":   r = engine.UtilsModule.base64_encode(t)
                    elif fn == "b64d":   r = engine.UtilsModule.base64_decode(t)
                    elif fn == "url_e":  r = engine.UtilsModule.url_encode(t)
                    elif fn == "url_d":  r = engine.UtilsModule.url_decode(t)
                    elif fn == "dict_pwd":
                        # 生成密码字典
                        mode = self._eg("dict_mode", "smart")
                        size_mb = self._eg("dict_size", "1")
                        try:
                            size = float(size_mb)
                        except:
                            size = 1.0
                        r = engine.UtilsModule.generate_password_dict(f'custom_{mode}_{int(size*1000)}kb.txt', 
                                                                      mode=mode, size_mb=size)
                    elif fn == "dict_user":
                        # 生成用户名字典
                        mode = self._eg("dict_mode", "common")
                        r = engine.UtilsModule.generate_username_dict(f'custom_users_{mode}.txt', mode=mode)
                    elif fn == "dict_smart":
                        # 智能密码字典
                        size_mb = self._eg("dict_size", "1")
                        try:
                            size = float(size_mb)
                        except:
                            size = 1.0
                        r = engine.UtilsModule.generate_smart_dict(f'smart_{int(size)}mb.txt', target_mb=size)
                    elif fn == "_auto":  r = engine.UtilsModule.md5_hash(t) if t else "请输入文本!"

                else:
                    r = f"[!] 未知模块：{mod}"

                self._set_out(str(r)[:4000])

            except Exception as e:
                self._set_out(f"✘ 错误：{e}")

        threading.Thread(target=work, daemon=True).start()

class BoxToolApp(App):
    def build(self):
        if not ENGINE_OK:
            return Label(text=f"引擎加载失败:\n{ENGINE_ERR}",
                        color=C.DARK, font_name=FONT, font_size=dp(14))
        return MainScreen()

    def on_start(self):
        print("[BoxTool v1.0] 启动完成")

if __name__ == "__main__":
    BoxToolApp().run()
