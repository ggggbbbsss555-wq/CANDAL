#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ssl
import json
import time
import math
import struct
import logging
import asyncio
import calendar
import platform
import random
import re
import shutil
import threading
import traceback
import itertools
import configparser
import contextlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Awaitable, Callable, Dict, Generic, Hashable, List, Literal, Mapping, Optional, Tuple, TypeVar

import certifi
import requests
import websocket
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from bs4.element import AttributeValueList
from fake_useragent import UserAgent

try:
    import orjson as _orjson
    HAS_ORJSON = True
except ImportError:
    _orjson = None
    HAS_ORJSON = False

# ==============================================================================
# SECTION 1: LOGGING & SSL SETUP
# ==============================================================================
def _prepare_logging():
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    websocket_logger = logging.getLogger("websocket")
    websocket_logger.setLevel(logging.INFO)
    websocket_logger.addHandler(logging.NullHandler())

_prepare_logging()
logger = logging.getLogger(__name__)

cert_path = certifi.where()
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = cert_path
cacert = os.environ.get('WEBSOCKET_CLIENT_CA_BUNDLE')

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.load_verify_locations(cert_path)


# ==============================================================================
# SECTION 1.5: EVENT-DRIVEN WAIT PRIMITIVES (replaces asyncio.sleep polling)
# ==============================================================================
# مستوحى من pyquotex._api._waits — يحل "مشكلة النوم" في الكود الأصلي.
# polling قصير مع timeout صارم بدلاً من asyncio.sleep ثابت؛ واستخدام
# asyncio.Event مباشرة عند توفّر حدث واضح.

async def wait_until(predicate: Callable[[], bool], *, timeout: float = 10.0,
                      poll_interval: float = 0.05) -> None:
    """يستدعي predicate() كل poll_interval ثانية حتى يُعيد True أو ينتهي timeout.

    يطلق asyncio.TimeoutError عند انتهاء المهلة. بديل فعّال لـ:
        while not condition:
            await asyncio.sleep(X)
    حيث يقلّل latency من X إلى poll_interval (50ms افتراضياً).
    """
    async def _loop():
        while not predicate():
            await asyncio.sleep(poll_interval)
    await asyncio.wait_for(_loop(), timeout=timeout)


async def wait_for_first_event(*events: asyncio.Event, timeout: float = 10.0) -> int:
    """ينتظر أول event يُطلق من القائمة ويعيد indexه. يطلق TimeoutError عند المهلة.

    بديل فعّال لـ:
        for _ in range(100):
            if cond_a: return A
            if cond_b: return B
            await asyncio.sleep(0.1)
    """
    if not events:
        raise ValueError("wait_for_first_event requires at least one event")
    tasks = [asyncio.ensure_future(e.wait()) for e in events]
    try:
        done, pending = await asyncio.wait(tasks, timeout=timeout,
                                           return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for i, t in enumerate(tasks):
            if t in done and t.result() and not t.cancelled():
                return i
        # إذا انتهى timeout
        raise asyncio.TimeoutError()
    except asyncio.CancelledError:
        for t in tasks:
            if not t.done():
                t.cancel()
        raise


def _schedule_event_set(event: Optional[asyncio.Event],
                        loop: Optional[asyncio.AbstractEventLoop]) -> None:
    """يطلق asyncio.Event بأمان من thread خارجي (مثل websocket thread).

    يستخدم run_coroutine_threadsafe مع coroutine وهمية فقط للحصول على
    callback آمن على الـ loop، أو thread-safe loop.call_soon_threadsafe.
    """
    if event is None or loop is None:
        return
    try:
        if not loop.is_closed() and loop.is_running():
            loop.call_soon_threadsafe(event.set)
    except RuntimeError:
        # الـ loop قد يكون أُغلق بين الفحص والتنفيذ — أهمل بهدوء
        pass


# ==============================================================================
# SECTION 2: CONSTANTS & SESSION
# ==============================================================================
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
base_dir = Path.cwd()
session_lock = threading.Lock()

def resource_path(relative_path: str) -> Path:
    global base_dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    return base_dir / relative_path

def load_session(email: str, user_agent: str = None) -> dict:
    if user_agent is None:
        try: user_agent = UserAgent().random
        except Exception: user_agent = USER_AGENT
    output_file = Path(resource_path("session.json"))
    with session_lock:
        all_sessions = {}
        if output_file.exists():
            try: all_sessions = json.loads(output_file.read_text())
            except json.JSONDecodeError: pass
        else:
            output_file.parent.mkdir(exist_ok=True, parents=True)
        if email not in all_sessions:
            all_sessions[email] = {"cookies": None, "token": None, "user_agent": user_agent}
        output_file.write_text(json.dumps(all_sessions, indent=4))
        return all_sessions.get(email)

def update_session(email: str, d: dict) -> dict:
    output_file = Path(resource_path("session.json"))
    with session_lock:
        current_sessions = {}
        if output_file.exists():
            try: current_sessions = json.loads(output_file.read_text())
            except json.JSONDecodeError: pass
        else:
            output_file.parent.mkdir(exist_ok=True, parents=True)
        current_sessions[email] = d
        output_file.write_text(json.dumps(current_sessions, indent=4))
        return current_sessions.get(email)

# ==============================================================================
# SECTION 3: HTTP NAVIGATOR (PROVEN WORKING METHOD)
# ==============================================================================
retry_strategy = Retry(
    total=3, backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    allowed_methods=["HEAD", "POST", "PUT", "GET", "OPTIONS"],
)

class CipherSuiteAdapter(HTTPAdapter):
    __attrs__ = ['ssl_context', 'max_retries', 'config', '_pool_connections', '_pool_maxsize', '_pool_block', 'source_address']
    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.cipherSuite = kwargs.pop('cipherSuite', 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')
        if not self.ssl_context:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket
            self.ssl_context.wrap_socket = self.wrap_socket
        if self.server_hostname:
            self.ssl_context.server_hostname = self.server_hostname
        if self.cipherSuite:
            self.ssl_context.set_ciphers(self.cipherSuite)
            self.ssl_context.set_ecdh_curve(self.ecdhCurve)
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        super().__init__(**kwargs)

    def wrap_socket(self, *args, **kwargs):
        if hasattr(self.ssl_context, 'server_hostname') and self.ssl_context.server_hostname:
            kwargs['server_hostname'] = self.ssl_context.server_hostname
            self.ssl_context.check_hostname = False
        else:
            self.ssl_context.check_hostname = True
        return self.ssl_context.orig_wrap_socket(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        kwargs['source_address'] = self.source_address
        return super().init_poolmanager(*args, **kwargs)

class Browser(Session):
    def __init__(self, *args, **kwargs):
        self.response = None
        self.default_headers = None
        self.ecdhCurve = kwargs.pop('ecdhCurve', 'prime256v1')
        self.cipherSuite = kwargs.pop('cipherSuite', 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        self.proxies = kwargs.pop('proxies', None)
        super().__init__(*args, **kwargs)
        self.headers.update(self.get_headers())
        self.mount('https://', CipherSuiteAdapter(ecdhCurve=self.ecdhCurve, cipherSuite=self.cipherSuite, server_hostname=self.server_hostname, source_address=self.source_address, ssl_context=ssl_context, max_retries=retry_strategy))

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self.close()
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): self.__exit__(exc_type, exc_val, exc_tb)

    def get_headers(self):
        self.default_headers = {"User-Agent": USER_AGENT}
        return self.default_headers

    def set_headers(self, headers=None):
        self.headers.update(self.default_headers)
        if headers: self.headers.update(headers)

    def get_cookies(self):
        return '; '.join(f'{i.name}={i.value}' for i in self.cookies)

    def get_soup(self):
        if self.response and not self.response.ok: raise RuntimeError(self.response.reason)
        return BeautifulSoup(self.response.content, "html.parser")

    def send_request(self, method, url, headers=None, **kwargs):
        merged_headers = self.headers.copy()
        if headers: merged_headers.update(headers)
        if self.proxies: kwargs['proxies'] = self.proxies
        self.response = self.request(method, url, headers=merged_headers, **kwargs)
        return self.response

# ==============================================================================
# SECTION 4: HTTP LOGIN & SETTINGS
# ==============================================================================
class Login(Browser):
    url = ""
    cookies = None
    ssid = None
    base_url = 'qxbroker.com'
    https_base_url = f'https://{base_url}'

    def __init__(self, api, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = api
        self.headers = self.get_headers()
        self.full_url = f"{self.https_base_url}/{api.lang}"

    def get_token(self):
        self.headers["Connection"] = "keep-alive"
        self.headers["Accept-Encoding"] = "gzip, deflate, br"
        self.headers["Accept-Language"] = "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3"
        self.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        self.headers["Referer"] = f"{self.full_url}/sign-in"
        self.headers["Upgrade-Insecure-Requests"] = "1"
        self.headers["Sec-Ch-Ua-Mobile"] = "?0"
        self.headers["Sec-Ch-Ua-Platform"] = '"Linux"'
        self.headers["Sec-Fetch-Site"] = "same-origin"
        self.headers["Sec-Fetch-User"] = "?1"
        self.headers["Sec-Fetch-Dest"] = "document"
        self.headers["Sec-Fetch-Mode"] = "navigate"
        self.headers["Dnt"] = "1"
        self.send_request("GET", f"{self.full_url}/sign-in/modal/")
        html = self.get_soup()
        match = html.find("input", {"name": "_token"})
        return None if not match else match.get("value")

    async def awaiting_pin(self, data, input_message):
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.headers["Referer"] = f"{self.full_url}/sign-in/modal"
        data["keep_code"] = 1
        try:
            code = input(input_message)
            if not code.isdigit():
                print("Please enter a valid code.")
                await self.awaiting_pin(data, input_message)
            data["code"] = code
        except KeyboardInterrupt:
            print("\nClosing program.")
            sys.exit()
        await asyncio.sleep(1)
        self.send_request(method="POST", url=f"{self.full_url}/sign-in/modal", data=data)

    def get_profile(self):
        self.response = self.send_request(method="GET", url=f"{self.full_url}/trade")
        if self.response:
            script = self.get_soup().find_all("script", {"type": "text/javascript"})
            script = script[0].get_text() if script else "{}"
            match = script.strip().replace(";", "").replace("window.settings = ", "")
            self.cookies = self.get_cookies()
            try:
                settings_dict = json.loads(match)
                self.ssid = settings_dict.get("token")
            except json.JSONDecodeError:
                self.ssid = None
            self.api.session_data["cookies"] = self.cookies
            self.api.session_data["token"] = self.ssid
            self.api.session_data["user_agent"] = self.headers["User-Agent"]
            update_session(self.api.username, self.api.session_data)
            return self.response, settings_dict if self.ssid else None
        return None, None

    async def _post(self, data):
        self.response = self.send_request(method="POST", url=f"{self.full_url}/sign-in/", data=data)
        required_keep_code = self.get_soup().find("input", {"name": "keep_code"})
        if required_keep_code:
            auth_body = self.get_soup().find("main", {"class": "auth__body"})
            input_message = f'{auth_body.find("p").text}: ' if auth_body.find("p") else "Enter the PIN code sent to your email: "
            await self.awaiting_pin(data, input_message)
            await asyncio.sleep(1)
            return self.success_login()
        return self.success_login()

    def success_login(self):
        if "trade" in str(self.response.url):
            return True, "Login successful."
        soup = self.get_soup()
        not_available = soup.select_one("#tab-1 > div > div.modal-sign__not-avalible__title")
        if not_available: return False, f"Service unavailable: {not_available.get_text(strip=True)}"
        error = soup.select_one("#tab-1 form > div:nth-child(2) > div")
        msg = error.get_text(strip=True) if error else "Unknown error"
        return False, f"Login failed. {msg}"

    async def __call__(self, username, password, user_data_dir=None):
        data = {"_token": self.get_token(), "email": username, "password": password, "remember": 1}
        status, msg = await self._post(data)
        if status: self.get_profile()
        return status, msg

class Settings(Browser):
    def __init__(self, api):
        super().__init__()
        self.set_headers()
        self.api = api
        self.headers = self.get_headers()

    def get_settings(self):
        self.headers["content-type"] = "application/json"
        self.headers["referer"] = f"{self.api.https_url}/{self.api.lang}/trade"
        self.headers["cookie"] = self.api.session_data.get("cookies", "")
        self.headers["user-agent"] = self.api.session_data.get("user_agent", "")
        response = self.send_request("GET", f"{self.api.https_url}/api/v1/cabinets/digest")
        return response.json()

# ==============================================================================
# SECTION 5: WEBSOCKET CLIENT & STATE (SYNC + EVENT REGISTRY INTEGRATION)
# ==============================================================================
class WebsocketStatus(IntEnum):
    DISCONNECTED = 0
    CONNECTED = 1
    CONNECTING = 2
    ERROR = -1

class AuthStatus(IntEnum):
    NOT_AUTHENTICATED = 0
    AUTHENTICATING = 1
    AUTHENTICATED = 2
    FAILED = -1

class ConnectionState:
    def __init__(self):
        self.SSID = None
        self.status = WebsocketStatus.DISCONNECTED
        self.auth_status = AuthStatus.NOT_AUTHENTICATED
        self.ssl_Mutual_exclusion = False
        self.ssl_Mutual_exclusion_write = False
        self.check_rejected_connection = False
        self.check_accepted_connection = False
        self.check_websocket_if_error = False
        self.check_websocket_if_connect = None
        self.websocket_error_reason = None

        # ===== EVENT-DRIVEN ADDITIONS =====
        # أحداث asyncio لاستبدال polling. تُهيّأ lazily من async context
        # عبر init_events() لتجنب "no running event loop" عند بناء الكائن.
        self.ws_connected_event: Optional[asyncio.Event] = None
        self.ws_closed_event: Optional[asyncio.Event] = None
        self.auth_accepted_event: Optional[asyncio.Event] = None
        self.auth_rejected_event: Optional[asyncio.Event] = None
        self.ws_error_event: Optional[asyncio.Event] = None
        # رابط الـ loop الحالي حتى نتمكن من إطلاق الأحداث من websocket thread
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def init_events(self) -> None:
        """يُنشئ الأحداث في الـ loop الحالي. يجب أن يُستدعى من async context."""
        if self.ws_connected_event is None:
            self.ws_connected_event = asyncio.Event()
        if self.ws_closed_event is None:
            self.ws_closed_event = asyncio.Event()
        if self.auth_accepted_event is None:
            self.auth_accepted_event = asyncio.Event()
        if self.auth_rejected_event is None:
            self.auth_rejected_event = asyncio.Event()
        if self.ws_error_event is None:
            self.ws_error_event = asyncio.Event()
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def reset_events(self) -> None:
        """يُعيد ضبط الأحداث قبل محاولة اتصال جديدة."""
        for ev in (self.ws_connected_event, self.ws_closed_event,
                   self.auth_accepted_event, self.auth_rejected_event,
                   self.ws_error_event):
            if ev is not None:
                ev.clear()

    # wrappers آمنة لإطلاق الأحداث من thread خارجي (websocket thread)
    def signal_ws_connected(self) -> None:
        _schedule_event_set(self.ws_connected_event, self._loop)

    def signal_ws_closed(self) -> None:
        _schedule_event_set(self.ws_closed_event, self._loop)

    def signal_auth_accepted(self) -> None:
        _schedule_event_set(self.auth_accepted_event, self._loop)

    def signal_auth_rejected(self) -> None:
        _schedule_event_set(self.auth_rejected_event, self._loop)

    def signal_ws_error(self) -> None:
        _schedule_event_set(self.ws_error_event, self._loop)

class WebsocketClient:
    def __init__(self, api):
        self.api = api
        self.state = api.state
        self.headers = {
            "User-Agent": self.api.session_data.get("user_agent", USER_AGENT),
            "Origin": self.api.https_url,
            "Host": f"ws2.{self.api.host}",
        }
        self.wss = websocket.WebSocketApp(
            self.api.wss_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_ping=self.on_ping,
            on_pong=self.on_pong,
            header=self.headers,
            cookie=self.api.session_data.get("cookies"),
        )

    def on_message(self, wss, msg):
        self.state.ssl_Mutual_exclusion = True
        # ===== STALE-WATCHDOG: تحديث وقت آخر رسالة مستلمة =====
        # الـ watchdog يستخدم هذا لاكتشاف صمت الاتصال مبكراً.
        try:
            if self.api is not None:
                self.api.last_message_at = time.time()
        except Exception:
            pass
        try:
            msg_str = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else str(msg)

            if msg_str == "2":
                try:
                    self.wss.send("3")
                except Exception:
                    pass
                self.state.ssl_Mutual_exclusion = False
                return
            if msg_str == "3":
                self.state.ssl_Mutual_exclusion = False
                return

            if "authorization/reject" in msg_str:
                logger.warning("Token rejected.")
                self.state.check_rejected_connection = True
                self.state.auth_status = AuthStatus.FAILED
                # ===== EVENT-DRIVEN FIX =====
                self.state.signal_auth_rejected()
            elif "s_authorization" in msg_str:
                self.state.check_accepted_connection = True
                self.state.check_rejected_connection = False
                self.state.auth_status = AuthStatus.AUTHENTICATED
                self.state.status = WebsocketStatus.CONNECTED
                print("\n" + "="*60)
                print("Connected to server successfully")
                print("="*60 + "\n")
                # ===== EVENT-DRIVEN FIX =====
                self.state.signal_auth_accepted()

            message = None
            if len(msg_str) > 1 and msg_str[1] in ('[', '{'):
                try:
                    message = json.loads(msg_str[1:])
                except Exception:
                    pass

            if message is not None:
                self._process_message_and_raise_events(message)

            if str(msg_str) == "41":
                self.state.check_websocket_if_connect = 0
        except Exception as e:
            logger.error("Unhandled error in on_message: %s", e)
        self.state.ssl_Mutual_exclusion = False

    def _process_message_and_raise_events(self, message):
        try:
            loop = self.api._async_loop
            if loop is None or not loop.is_running():
                return

            if isinstance(message, dict):
                asset = message.get("asset")
                if asset and (message.get("candles") or message.get("data") or message.get("history")):
                    self.api.candle_v2_data[asset] = message
                    self.api.candles.candles_data = message.get("candles") or message.get("data") or message.get("history")

                    asyncio.run_coroutine_threadsafe(
                        self.api.event_registry.set_event(f'candles_ready_{asset}', message),
                        loop
                    )

                    index = message.get("index")
                    if index is not None:
                        asyncio.run_coroutine_threadsafe(
                            self.api.event_registry.set_event(f'candles_ready_{asset}_{index}', message),
                            loop
                        )

            if isinstance(message, dict) and (message.get("liveBalance") or message.get("demoBalance")):
                self.api.account_balance = message

            if isinstance(message, list) and len(message) > 0 and isinstance(message[0], list) and len(message[0]) == 4:
                asset = message[0][0]
                self.api.realtime_candles[asset] = message[0]
        except Exception as e:
            logger.debug(f"Error processing message: {e}")

    def on_error(self, wss, error):
        global CONNECTION_ALIVE
        logger.error(error)
        self.state.websocket_error_reason = str(error)
        self.state.check_websocket_if_error = True
        self.state.status = WebsocketStatus.ERROR
        self.state.check_accepted_connection = False
        # ===== EVENT-DRIVEN FIX =====
        self.state.signal_ws_error()
        try:
            CONNECTION_ALIVE = False
        except Exception:
            pass

    def on_open(self, wss):
        logger.info("Websocket client connected.")
        self.state.check_websocket_if_connect = 1
        self.state.status = WebsocketStatus.CONNECTED
        # ===== EVENT-DRIVEN FIX =====
        self.state.signal_ws_connected()
        asset_name = self.api.current_asset or "EURUSD"
        period = self.api.current_period or 60
        self.wss.send('42["tick"]')
        self.wss.send('42["indicator/list"]')
        self.wss.send('42["drawing/load"]')
        self.wss.send('42["pending/list"]')
        self.wss.send(f'42["instruments/update",{{"asset":"{asset_name}","period":{period}}}]')
        self.wss.send(f'42["depth/follow","{asset_name}"]')
        self.wss.send('42["chart_notification/get"]')
        self.wss.send('42["instruments/get"]')
        self.wss.send('42["tick"]')

    def on_close(self, wss, close_status_code, close_msg):
        global CONNECTION_ALIVE
        logger.info("Websocket connection closed.")
        self.state.check_websocket_if_connect = 0
        self.state.status = WebsocketStatus.DISCONNECTED
        self.state.check_accepted_connection = False
        # ===== EVENT-DRIVEN FIX =====
        self.state.signal_ws_closed()
        try:
            CONNECTION_ALIVE = False
        except Exception:
            pass

    def on_ping(self, wss, ping_msg): pass
    def on_pong(self, wss, pong_msg): pass

# ==============================================================================
# SECTION 6: QUOTEX API CORE
# ==============================================================================
class CandlesObj:
    def __init__(self): self.__candles_data = None
    @property
    def candles_data(self): return self.__candles_data
    @candles_data.setter
    def candles_data(self, candles_data): self.__candles_data = candles_data

class EventRegistry:
    def __init__(self):
        self._events: Dict[str, asyncio.Event] = {}
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get_event(self, key: str) -> asyncio.Event:
        async with self._lock:
            if key not in self._events:
                self._events[key] = asyncio.Event()
            return self._events[key]

    async def set_event(self, key: str, data: Any = None):
        async with self._lock:
            if key not in self._events:
                self._events[key] = asyncio.Event()
            self._data[key] = data
            self._events[key].set()

    async def wait_event(self, key: str, timeout: float = 30.0) -> Any:
        event = await self.get_event(key)
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self._data.get(key)
        except asyncio.TimeoutError:
            return None

    async def clear_event(self, key: str):
        async with self._lock:
            if key in self._events:
                self._events[key].clear()
            if key in self._data:
                del self._data[key]

class QuotexAPI:
    def __init__(self, host, username, password, lang, proxies=None, user_data_dir="."):
        self.state = ConnectionState()
        self.trace_ws = False
        self.current_asset = None
        self.current_period = None
        self.account_balance = None
        self.account_type = 1
        self.instruments = None
        self.host = host
        self.https_url = f"https://{host}"
        self.wss_url = f"wss://ws2.{host}/socket.io/?EIO=3&transport=websocket"
        self.websocket_thread = None
        self.websocket_client = None
        self.username = username
        self.password = password
        self.proxies = proxies
        self.lang = lang
        self.user_data_dir = user_data_dir
        self.session_data = {}
        self.browser = Browser()
        self.browser.set_headers()
        self.settings = Settings(self)
        self.candles = CandlesObj()
        self.candle_v2_data = {}
        self.realtime_price = defaultdict(list)
        self.realtime_candles = {}
        self.event_registry = EventRegistry()
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._temp_status = ""
        # ===== STALE-WATCHDOG ADDITION =====
        # يُحدّث عند استلام أي رسالة WS من الخادم. الـ watchdog يستخدمه
        # لاكتشاف صمت الاتصال قبل أن يقطعه الخادم.
        self.last_message_at: float = time.time()
        # ===== FIX 7: Rate Limiter خفيف جداً (لا يبطئ السرعة) =====
        # المستخدم لا يريد تخفيض الطلبات. الرام الأصلي للـ rate limiter كان حماية
        # من قطع الخادم، لكن الحل الحقيقي هو keepalive نشط + watchdog.
        # نبقي rate limiter خفيف جداً (15ms = ~66 req/s) لمنع الـ bursts الصافية فقط.
        self._ws_send_times: list[float] = []
        self._ws_min_interval: float = 0.015  # 15ms بين كل إرسال (خفيف جداً)
        self._ws_max_per_window: int = 100    # 100 طلب/ثانية (سخيّ)
        self._ws_window: float = 1.0          # 1 ثانية
        self._throttle_multiplier: float = 1.0  # ثابت = 1.0 (لا auto-throttle)
        self._last_send_at: float = 0.0

    @property
    def login(self): return Login(self)

    def _apply_rate_limit(self) -> None:
        """يُطبّق rate limiting قبل أي إرسال WS — يحمي من قطع الخادم.

        - ضمان فاصل أدنى بين كل إرسالين (_ws_min_interval * _throttle_multiplier)
        - ضمان عدد الطلبات في النافذة (_ws_max_per_window / _throttle_multiplier)
        """
        now = time.time()
        # 1) الحد الأدنى للفاصل بين الإرسالين
        min_interval = self._ws_min_interval * self._throttle_multiplier
        if self._last_send_at > 0:
            elapsed = now - self._last_send_at
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
                now = time.time()
        # 2) تنظيف القائمة من الأوقات خارج النافذة
        window_size = self._ws_window * self._throttle_multiplier
        cutoff = now - window_size
        self._ws_send_times = [t for t in self._ws_send_times if t >= cutoff]
        # 3) إذا تجاوزنا الحد الأقصى في النافذة، انتظر حتى تنتهي النافذة
        if len(self._ws_send_times) >= self._ws_max_per_window:
            # انتظر حتى أقدم طلب في النافذة يخرج منها
            sleep_for = (self._ws_send_times[0] + window_size) - now
            if sleep_for > 0:
                time.sleep(sleep_for)
                now = time.time()
                cutoff = now - window_size
                self._ws_send_times = [t for t in self._ws_send_times if t >= cutoff]
        # 4) سجّل هذا الإرسال
        self._ws_send_times.append(now)
        self._last_send_at = now

    def increase_throttle(self, factor: float = 2.0, max_multiplier: float = 8.0) -> None:
        """زيادة مُضاعِف التباطؤ عند الفشل (مثل انقطاع الاتصال).
        الخادم يقطع => نُبطئ => ضغط أقل => نجاح.
        """
        new_multiplier = min(self._throttle_multiplier * factor, max_multiplier)
        if new_multiplier != self._throttle_multiplier:
            self._throttle_multiplier = new_multiplier
            logger.info(f" Throttle increased to {new_multiplier}x (rate limit stress)")

    def decrease_throttle(self, factor: float = 0.5, min_multiplier: float = 1.0) -> None:
        """تخفيض مُضاعِف التباطؤ بعد نجاح متواصل (استعادة السرعة)."""
        new_multiplier = max(self._throttle_multiplier * factor, min_multiplier)
        if new_multiplier != self._throttle_multiplier:
            self._throttle_multiplier = new_multiplier
            logger.info(f" Throttle restored to {new_multiplier}x")

    def send_websocket_request(self, data, no_force_send=True):
        # ===== FIX: busy-wait -> sleep + try/finally =====
        if no_force_send:
            deadline = time.time() + 5.0  # حد أقصى 5s للاانتظار
            while (self.state.ssl_Mutual_exclusion or self.state.ssl_Mutual_exclusion_write):
                if time.time() > deadline:
                    # تجاوز المهلة — لا نعلق للأبد. نُجبر الإرسال.
                    break
                time.sleep(0.001)  # بدلاً من `pass` — تحرير CPU
        # ===== FIX 6: تطبيق rate limit قبل الإرسال =====
        # استثناء: heartbeat messages ("2" و "42[\"tick\"]" و "42[\"instruments/get\"]")
        # يجب أن تمر دون rate limit صارم — وإلا فقد يعلق keepalive.
        is_heartbeat = (
            data == "2" or
            data == '42["tick"]' or
            data == '42["instruments/get"]' or
            'pending/list' in data or
            'indicator/list' in data or
            'drawing/load' in data
        )
        if not is_heartbeat:
            try:
                self._apply_rate_limit()
            except Exception:
                # لا نُسقط الإرسال بسبب rate limiter
                pass
        self.state.ssl_Mutual_exclusion_write = True
        try:
            if self.websocket_client and self.websocket_client.wss:
                self.websocket_client.wss.send(data)
        finally:
            # ===== FIX: ضمان إعادة ضبط الـ flag حتى عند الاستثناء =====
            self.state.ssl_Mutual_exclusion_write = False

    def subscribe_realtime_candle(self, asset, period):
        self.realtime_price[asset] = []
        self.realtime_candles[asset] = {}
        data = f'42["instruments/update", {json.dumps({"asset": asset, "period": period})}]'
        return self.send_websocket_request(data)

    def follow_candle(self, asset):
        return self.send_websocket_request(f'42["depth/follow", {json.dumps(asset)}]')

    def chart_notification(self, asset):
        return self.send_websocket_request(f'42["chart_notification/get", {json.dumps({"asset": asset, "version": "1.0.0"})}]')

    def get_candles_ws(self, asset, index, time_val, offset, period):
        payload = {"asset": asset, "index": index, "time": time_val, "offset": offset, "period": period}
        data = f'42["history/load",{json.dumps(payload)}]'
        return self.send_websocket_request(data)

    async def authenticate(self):
        async with self.login as login:
            status, msg = await login(self.username, self.password, self.user_data_dir)
        if status:
            self.state.SSID = self.session_data.get("token")
        return status, msg

    async def start_websocket(self):
        self.state.check_websocket_if_connect = None
        self.state.check_websocket_if_error = False
        self.state.websocket_error_reason = None
        # ===== EVENT-DRIVEN FIX =====
        # تأكد من تهيئة الأحداث + إعادة ضبطها قبل المحاولة
        self.state.init_events()
        self.state.reset_events()
        # حدّث رابط الـ loop في الحالة (قد يكون تغيّر بعد reconnect)
        try:
            self.state._loop = asyncio.get_running_loop()
        except RuntimeError:
            self.state._loop = None

        if not self.state.SSID:
            await self.authenticate()
        self.websocket_client = WebsocketClient(self)
        payload = {
            "suppress_origin": True, "ping_interval": 24, "ping_timeout": 20, "ping_payload": "2",
            "origin": self.https_url, "host": f"ws2.{self.host}",
            "sslopt": {"check_hostname": True, "cert_reqs": ssl.CERT_REQUIRED, "ca_certs": cacert, "context": ssl_context},
        }
        if platform.system() == "Linux":
            payload["sslopt"]["ssl_version"] = ssl.PROTOCOL_TLS
        self.websocket_thread = threading.Thread(target=self.websocket_client.wss.run_forever, kwargs=payload)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # ===== EVENT-DRIVEN FIX =====
        # بديل polling:
        #   for _ in range(100):
        #       if self.state.check_websocket_if_error: return False, ...
        #       elif self.state.check_websocket_if_connect == 1: return True, ...
        #       elif self.state.check_rejected_connection: return False, "Token Rejected."
        #       await asyncio.sleep(0.1)
        # بانتظار أول حدث من: connected, rejected, error, closed
        try:
            idx = await wait_for_first_event(
                self.state.ws_connected_event,
                self.state.auth_rejected_event,
                self.state.ws_error_event,
                self.state.ws_closed_event,
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            return False, "Timeout waiting for websocket open"

        if idx == 0:
            return True, "Websocket connected successfully!!!"
        elif idx == 1:
            self.state.SSID = None
            return False, "Websocket Token Rejected."
        elif idx == 2:
            return False, self.state.websocket_error_reason or "Websocket error"
        elif idx == 3:
            return False, "Websocket connection closed."
        return False, "Unknown websocket state"

    async def send_ssid(self, timeout=10):
        if not self.state.SSID: return False
        # ===== EVENT-DRIVEN FIX =====
        # تأكد من تهيئة الأحداث (قد تُستدعى send_ssid قبل start_websocket في بعض المسارات)
        if self.state.auth_accepted_event is None:
            self.state.init_events()
        self.state.auth_accepted_event.clear()
        self.state.auth_rejected_event.clear()

        payload = {"session": self.state.SSID, "isDemo": self.account_type, "tournamentId": 0}
        data = f'42["authorization",{json.dumps(payload)}]'
        self.send_websocket_request(data)

        # ===== EVENT-DRIVEN FIX =====
        # بديل polling:
        #   while not check_accepted and not check_rejected:
        #       if time.time() - start_time > timeout: return False
        #       await asyncio.sleep(0.5)
        # انتظار حدث accepted أو rejected فقط.
        try:
            idx = await wait_for_first_event(
                self.state.auth_accepted_event,
                self.state.auth_rejected_event,
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return False
        return idx == 0  # True إذا accepted, False إذا rejected

    async def connect(self, is_demo):
        self.account_type = 1 if is_demo else 0
        self.state.ssl_Mutual_exclusion = False
        self.state.ssl_Mutual_exclusion_write = False
        check_websocket, websocket_reason = await self.start_websocket()
        if not check_websocket: return check_websocket, websocket_reason
        check_ssid = await self.send_ssid()
        if not check_ssid:
            await self.authenticate()
            if self.state.SSID: await self.send_ssid()
        return check_websocket, websocket_reason

    async def close(self):
        if self.websocket_client and self.websocket_client.wss:
            self.websocket_client.wss.close()
            await asyncio.sleep(1)
        if self.websocket_thread and self.websocket_thread.is_alive():
            self.websocket_thread.join(timeout=5)
        return True

# ==============================================================================
# SECTION 7: QUOTEX STABLE API WITH FULL HISTORY MIXIN
# ==============================================================================
_request_counter = itertools.count(int(time.time() * 1000))

def group_by_period(data, period):
    grouped = defaultdict(list)
    for tick in data:
        timestamp = int(tick[0])
        timeframe = int(timestamp // period)
        grouped[timeframe].append(tick)
    return dict(grouped)

def calculate_candles(history, period):
    if not isinstance(history, list) or not history: return []
    grouped = group_by_period(history, period)
    candles = []
    for minute, ticks in grouped.items():
        open_price = ticks[0][1]
        close_price = ticks[-1][1]
        high_price = max(tick[1] for tick in ticks)
        low_price = min(tick[1] for tick in ticks)
        candle = {'time': minute * period, 'open': open_price, 'close': close_price, 'high': high_price, 'low': low_price, 'ticks': len(ticks)}
        candles.append(candle)
    return candles[:-1] if len(candles) > 1 else candles


# ===== FIX A: محلّل شموع خام يكتشف صيغة الخادم الفعلية =====
# المشكلة: calculate_candles تتعامل مع كل عنصر كـ "tick" [time, price] وتستخدم
# tick[1] فقط لكل من open/high/low/close. خادم Quotex يُرجع الشموع عبر
# "history/load" بصيغة [time, open, close, high, low] (5 عناصر). عند تمريرها
# إلى calculate_candles، تُعامل كل شمعة كـ tick واحد فينتج:
#   open = high = low = close = open_price  => خطوط مسطّحة!
# هذا ما كان يحدث في fill_gap_once => get_candles => prepare_candles.
# هذه الدالة البديلة تكتشف الصيغة وتستخدم الحقول الفعلية لكل صيغة.
def _parse_raw_candles(raw_candles):
    """يُحوّل الشموع الخام من WebSocket إلى قائمة dicts بصيغة OHLC موحّدة.

    يدعم ثلاث صيغ يمكن أن يُرسلها الخادم عبر "history/load":
      1) [time, open, close, high, low]       — صيغة Quotex الشائعة (5 عناصر)
      2) [time, open, close, high, low, vol]  — نفس الصيغة مع volume (6 عناصر)
      3) {"time", "open", "high", "low", "close", ...} — dict
      4) [time, price(, volume)] — tick فردي (يُحوّل إلى شمعة بسيطة)
    """
    if not raw_candles: return []
    parsed = []
    for c in raw_candles:
        try:
            if isinstance(c, dict) and 'time' in c:
                t = int(c.get('time', c.get('timestamp', 0)))
                o = float(c.get('open', 0) or 0)
                h = float(c.get('high', c.get('max', 0)) or 0)
                l = float(c.get('low', c.get('min', 0)) or 0)
                cl = float(c.get('close', c.get('c', 0)) or 0)
                v = int(c.get('volume', c.get('vol', 0)) or 0)
                if t > 0 and o > 0 and h > 0 and l > 0 and cl > 0:
                    parsed.append({'time': t, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': v})
            elif isinstance(c, (list, tuple)) and len(c) >= 5:
                # Quotex WS: [time, open, close, high, low(, volume)]
                t = int(c[0])
                o = float(c[1])
                cl = float(c[2])
                h = float(c[3])
                l = float(c[4])
                v = int(c[5]) if len(c) >= 6 else 0
                if t > 0 and o > 0 and h > 0 and l > 0 and cl > 0:
                    parsed.append({'time': t, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': v})
            elif isinstance(c, (list, tuple)) and len(c) >= 2:
                # tick format: [time, price(, volume)]
                t = int(c[0])
                p = float(c[1])
                v = int(c[2]) if len(c) >= 3 else 0
                if t > 0 and p > 0:
                    parsed.append({'time': t, 'open': p, 'high': p, 'low': p, 'close': p, 'volume': v})
        except (TypeError, ValueError):
            continue
    return parsed

def process_candles_v2(history, asset, data):
    if not history or not isinstance(history, dict): return data if data else []
    candles_data = history.get(asset, {})
    candles = candles_data.get("candles", [])[1:] if candles_data else []
    combined = candles + (data if data else [])
    if combined:
        candle_dict = {c.get('time'): c for c in combined if isinstance(c, dict) and 'time' in c}
        return list(candle_dict.values()) if candle_dict else []
    return combined

def merge_candles(candles_data):
    if not candles_data: return []
    candle_dict = {c['time']: c for c in candles_data if isinstance(c, dict) and 'time' in c}
    return sorted(candle_dict.values(), key=lambda x: x['time']) if candle_dict else []

class Quotex:
    def __init__(self, email=None, password=None, host="qxbroker.com", lang="en", proxies=None, user_data_dir="browser", asset_default="EURUSD", period_default=60):
        self.email = email
        self.password = password
        self.host = host
        self.lang = lang
        self.proxies = proxies
        self.user_data_dir = user_data_dir
        self.asset_default = asset_default
        self.period_default = period_default
        self.account_is_demo = 1
        self.codes_asset = {}
        self.api = None
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        session = load_session(self.email, USER_AGENT)
        self.session_data = session

    async def check_connect(self):
        if self.api is None: return False
        # ===== EVENT-DRIVEN FIX =====
        # بديل:
        #   await asyncio.sleep(1)
        #   return self.api.state.check_accepted_connection == 1
        # الذي يؤخر الكشف ثانية كاملة. ننتظر بدلاً من ذلك حتى 2s بفاصل 50ms
        # ثم نُعيد الحالة الفعلية — يقلّل latency الكشف من 1000ms إلى <100ms.
        try:
            await wait_until(
                lambda: self.api.state.check_accepted_connection == 1,
                timeout=2.0,
                poll_interval=0.05,
            )
            return True
        except asyncio.TimeoutError:
            return self.api.state.check_accepted_connection == 1

    async def connect(self):
        self.api = QuotexAPI(self.host, self.email, self.password, self.lang, proxies=self.proxies, user_data_dir=self.user_data_dir)
        self.api.session_data = self.session_data
        self.api.state.SSID = self.session_data.get("token")
        self.api._async_loop = asyncio.get_running_loop()
        if not self.session_data.get("token"):
            check, reason = await self.api.authenticate()
            if not check: return check, reason
        check, reason = await self.api.connect(self.account_is_demo == 1)
        if not check:
            self.session_data = {}
            return False, "Websocket connection rejected."
        return check, reason

    async def change_account(self, balance_mode: str):
        self.account_is_demo = 0 if balance_mode.upper() == "REAL" else 1
        self.api.account_type = self.account_is_demo
        payload = {"demo": self.api.account_type, "tournamentId": 0}
        self.api.send_websocket_request(f'42["account/change",{json.dumps(payload)}]')

    async def get_all_assets(self):
        return {}

    async def start_candles_stream(self, asset="EURUSD", period=60):
        if self.api:
            self.api.current_asset = asset
            self.api.current_period = period
            self.api.subscribe_realtime_candle(asset, period)
            self.api.chart_notification(asset)
            self.api.follow_candle(asset)

    async def get_realtime_candles(self, asset: str):
        if self.api: return self.api.realtime_candles.get(asset, [])
        return []

    async def get_candles(self, asset, end_from_time, offset, period, progressive=False, timeout=30, use_cache=False):
        if self.api is None: return None
        if end_from_time is None: end_from_time = time.time()
        index = calendar.timegm(time.gmtime())
        self.api.candles.candles_data = None
        await self.api.event_registry.clear_event(f'candles_ready_{asset}')
        await self.start_candles_stream(asset, period)
        self.api.get_candles_ws(asset, index, int(end_from_time), offset, period)
        try:
            history_data = await self.api.event_registry.wait_event(f'candles_ready_{asset}', timeout=timeout)
        except Exception:
            return None
        if history_data is None: return None
        candles = self.prepare_candles(asset, period, history_data)
        if progressive: return self.api.historical_candles.get("data", {})
        return candles

    async def _fetch_historical_batch(self, asset, fetch_time, offset, period, index, timeout):
        if self.api is None: return None
        payload = {"asset": asset, "index": index, "time": fetch_time, "offset": offset, "period": period}
        ws_msg = f'42["history/load",{json.dumps(payload)}]'
        event_name = f'candles_ready_{asset}_{index}'
        await self.api.event_registry.clear_event(event_name)
        self.api.send_websocket_request(ws_msg)
        try:
            return await self.api.event_registry.wait_event(event_name, timeout=timeout)
        except Exception:
            return None

    def _parse_historical_candles(self, raw_data):
        if raw_data is None: return []
        raw_candles = raw_data.get("data", []) or raw_data.get("candles", [])
        if not raw_candles: return []
        parsed = []
        for c in raw_candles:
            if isinstance(c, list) and len(c) >= 5:
                parsed.append({"time": int(c[0]), "open": float(c[1]), "close": float(c[2]), "high": float(c[3]), "low": float(c[4])})
            elif isinstance(c, dict) and "time" in c:
                parsed.append(c)
        return parsed

    async def get_historical_candles(self, asset, amount_of_seconds, period, timeout=30, max_workers=5, progress_callback=None):
        # ===== FIX 7: إبقاء الإعدادات الأصلية للسرعة (5 workers + chunk=200) =====
        # المستخدم لا يريد تخفيض الطلبات. الحل الجذري للانقطاع ليس في تقليل الطلبات
        # بل في إبقاء الاتصال نشطاً (keepalive متوازي + watchdog أسرع).
        max_workers = max_workers or 1  # استخدم القيمة المُمرّرة
        chunk_seconds = period * FETCH_CHUNK_SIZE  # period * 200 = 12000s لكل batch
        all_candles = {}
        current_time = int(time.time())
        target_start_time = current_time - amount_of_seconds
        block_size = amount_of_seconds // max_workers
        semaphore = asyncio.Semaphore(max_workers)

        async def worker(start_t, end_t, worker_id):
            worker_candles = {}
            async with semaphore:
                oldest_t = start_t
                consecutive_failures_in_worker = 0
                while oldest_t > end_t:
                    # ===== FIX 3: تحقق من الاتصال قبل كل batch =====
                    if not self.api or not getattr(self.api.state, 'check_accepted_connection', False):
                        # الاتصال مُقطع — خروج مبكر بدلاً من الاستمرار في الإرسال
                        break
                    index = next(_request_counter)
                    batch_data = await self._fetch_historical_batch(asset, oldest_t, chunk_seconds, period, index, timeout)
                    if not batch_data:
                        oldest_t -= chunk_seconds
                        consecutive_failures_in_worker += 1
                        if consecutive_failures_in_worker >= 3:
                            # 3 فشل متتالي = الاتصال مُقطع — خروج
                            break
                        # backoff قبل إعادة المحاولة
                        await asyncio.sleep(FETCH_BATCH_DELAY * 2)
                        continue
                    consecutive_failures_in_worker = 0
                    new_batch = self._parse_historical_candles(batch_data)
                    if not new_batch: oldest_t -= chunk_seconds; continue
                    batch_times = []
                    for c in new_batch:
                        ts = c['time']
                        if ts >= end_t and ts <= start_t:
                            worker_candles[ts] = c
                            batch_times.append(ts)
                    if not batch_times: oldest_t -= chunk_seconds; continue
                    batch_times.sort()
                    new_oldest = batch_times[0]
                    if progress_callback: progress_callback(start_t - new_oldest, start_t - end_t, len(worker_candles), f"Worker-{worker_id}")
                    oldest_t = new_oldest if new_oldest < oldest_t else oldest_t - chunk_seconds
                    # تأخير قصير بين batches (0.1s — الإعداد الأصلي)
                    await asyncio.sleep(FETCH_BATCH_DELAY)
            return list(worker_candles.values())

        await self.start_candles_stream(asset, period)
        tasks = []
        for i in range(max_workers):
            s = current_time - (i * block_size)
            e = max(target_start_time, s - block_size)
            tasks.append(worker(s, e, i))
        results = await asyncio.gather(*tasks)
        for batch in results:
            for c in batch: all_candles[c['time']] = c
        return sorted(all_candles.values(), key=lambda x: x['time'])

    def prepare_candles(self, asset, period, history=None):
        if self.api is None: return []
        history_data = history if history is not None else self.api.candles.candles_data
        if history_data is None: return []
        if isinstance(history_data, dict):
            candles_list = history_data.get("candles") or history_data.get("data") or history_data.get("history") or []
        else:
            candles_list = history_data
        if not candles_list: return []
        # ===== FIX A: استخدم _parse_raw_candles بدلاً من calculate_candles =====
        # calculate_candles كانت تتعامل مع كل عنصر كـ tick [time, price] وتستخدم
        # tick[1] فقط لكل من open/high/low/close — فتُنتج شموع مسطّحة (open == high ==
        # low == close) عند استعمال بيانات history/load التي تأتي بصيغة
        # [time, open, close, high, low]. _parse_raw_candles تكتشف الصيغة وتستخدم
        # الحقول الفعلية لكل صيغة، فلا تظهر خطوط مسطّحة.
        candles_data = _parse_raw_candles(candles_list)
        # محاذاة الأوقات إلى grill الـ period (يحافظ على اتساقها مع بقية الكود)
        for c in candles_data:
            c['time'] = (int(c['time']) // period) * period
        candles_v2_data = process_candles_v2(self.api.candle_v2_data, asset, candles_data)
        return merge_candles(candles_v2_data)

    async def close(self):
        if self.api: return await self.api.close()
        return True

# ==============================================================================
# SECTION 8: MT4 WRITER & ASSETS (COMPLETE)
# ==============================================================================
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = cert_path

DEBUG_LOGS = False
def dbg(msg: str):
    if DEBUG_LOGS: print(f"  \033[2m   [debug] {msg}\033[0m")

LOG_FILE = Path("qxchart.log")
def _log_to_file(line: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line + "\n")
    except Exception: pass

def logmsg(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  \033[2m[{ts}]\033[0m {msg}")
    _log_to_file(f"[{ts}] {msg}")

def log_exception(context: str, exc: BaseException):
    ts = datetime.now().strftime("%H:%M:%S")
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"  \033[91m[{ts}] FATAL in {context}: {exc}\033[0m")
    _log_to_file(f"[{ts}] FATAL in {context}: {exc}\n{tb_text}")

def _thread_excepthook(args):
    log_exception(f"thread '{args.thread.name}'", args.exc_value)
threading.excepthook = _thread_excepthook

def _main_excepthook(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt): sys.__excepthook__(exc_type, exc_value, exc_tb); return
    log_exception("main thread (top level)", exc_value)
sys.excepthook = _main_excepthook

class _NullHandler(logging.Handler):
    def emit(self, record): pass

@contextlib.contextmanager
def suppress_terminal_output():
    _loggers = [logging.getLogger(), logging.getLogger("pyquotex"), logging.getLogger("Quotex"), logging.getLogger("websockets"), logging.getLogger("websocket"), logging.getLogger("asyncio")]
    _old_levels = [(l, l.level, l.disabled) for l in _loggers]
    _old_handlers = [(l, list(l.handlers)) for l in _loggers]
    for l in _loggers:
        l.handlers = [_NullHandler()]; l.setLevel(logging.CRITICAL + 1); l.disabled = True
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try: yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            for l, lvl, dis in _old_levels: l.setLevel(lvl); l.disabled = dis
            for l, hs in _old_handlers: l.handlers = hs

WINAPI_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        WM_COMMAND = 0x0111
        MT4_REFRESH_CHART = 33324
        GA_ROOT = 2
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
        user32.GetWindowTextW.restype = wintypes.INT
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = wintypes.INT
        WINAPI_AVAILABLE = True
    except Exception: pass

_MT4_HWND = None
_MT4_HWND_LAST_SEARCH = 0
_LAST_GLOBAL_REFRESH = 0
_ENUM_PROC_REF = None

def find_mt4_window():
    global _MT4_HWND, _MT4_HWND_LAST_SEARCH, _ENUM_PROC_REF
    if not WINAPI_AVAILABLE: return None
    now = time.time()
    if _MT4_HWND and (now - _MT4_HWND_LAST_SEARCH < 30):
        if user32.IsWindow(_MT4_HWND): return _MT4_HWND
    _MT4_HWND = None
    _MT4_HWND_LAST_SEARCH = now
    found = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if "MetaTrader 4" in buf.value or "MetaTrader4" in buf.value: found.append(hwnd)
                return False
        return True
    _ENUM_PROC_REF = enum_callback
    user32.EnumWindows(enum_callback, 0)
    _MT4_HWND = found[0] if found else None
    return _MT4_HWND

REFRESH_INTERVAL = 1.0
def refresh_mt4():
    global _LAST_GLOBAL_REFRESH
    if not WINAPI_AVAILABLE: return False
    now = time.time()
    if now - _LAST_GLOBAL_REFRESH < REFRESH_INTERVAL: return False
    _LAST_GLOBAL_REFRESH = now
    hwnd = find_mt4_window()
    if not hwnd: return False
    root = user32.GetAncestor(hwnd, GA_ROOT)
    target = root if root else hwnd
    user32.PostMessageW(target, WM_COMMAND, MT4_REFRESH_CHART, 0)
    return True

class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; BLUE = '\033[94m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; DIM = '\033[2m'; RESET = '\033[0m'; CLEAR_LINE = '\033[K'

def pretty_asset_name(symbol: str, period_label: str = "M1") -> str:
    base = symbol
    suffix = ""
    if base.upper().endswith("_OTC"):
        base = base[:-4]
        suffix = " · OTC"
    if len(base) == 6 and base.isalpha():
        pretty = f"{base[:3].upper()}/{base[3:].upper()}{suffix}"
    else:
        pretty = f"{base.upper()}{suffix}"
    return f"({pretty}),{period_label}"

user_home = os.path.expanduser('~')
MT4_CONFIG_FILE = Path("mt4_config.json")
SYSTEM_FOLDERS = {"default", "downloads", "mailbox", "signals", "symbolsets", "deleted", "templates", "profiles", "mql4", "logs", "config", "history_backup"}

def _validate_mt4_path(path: str) -> bool:
    if not path or not os.path.exists(path): return False
    try:
        test_file = os.path.join(path, ".write_test.tmp")
        with open(test_file, 'w') as f: f.write("test")
        os.remove(test_file)
        return True
    except Exception: return False

def _save_mt4_path(path: str):
    try:
        config = json.loads(MT4_CONFIG_FILE.read_text()) if MT4_CONFIG_FILE.exists() else {}
        config["mt4_history_path"] = path
        config["saved_at"] = int(time.time())
        MT4_CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except Exception: pass

def find_mt4_history_path() -> str:
    appdata = os.environ.get('APPDATA', '') or os.environ.get('HOME', '')
    common_path = os.path.join(appdata, 'MetaQuotes', 'Terminal', 'Common', 'Files', 'qx_hst')
    try:
        os.makedirs(common_path, exist_ok=True)
        return common_path
    except Exception:
        pass
    
    base_terminal = os.path.join(user_home, "AppData", "Roaming", "MetaQuotes", "Terminal")
    if not os.path.exists(base_terminal): return ""
    all_servers = []
    try:
        for terminal_id in os.listdir(base_terminal):
            history_path = os.path.join(base_terminal, terminal_id, "history")
            if not os.path.exists(history_path): continue
            for server_name in os.listdir(history_path):
                server_lower = server_name.lower()
                if server_lower in SYSTEM_FOLDERS or server_lower.startswith(".") or server_lower.startswith("_"): continue
                server_path = os.path.join(history_path, server_name)
                if not os.path.isdir(server_path): continue
                try:
                    hst_files = [f for f in os.listdir(server_path) if f.endswith('.hst')]
                    all_servers.append({"terminal_id": terminal_id, "server_name": server_name, "full_path": server_path, "has_hst": len(hst_files) > 0, "hst_count": len(hst_files), "is_writable": _validate_mt4_path(server_path)})
                except Exception: pass
    except Exception: pass
    if not all_servers: return ""
    if MT4_CONFIG_FILE.exists():
        try:
            saved_path = json.loads(MT4_CONFIG_FILE.read_text()).get("mt4_history_path", "")
            if saved_path and os.path.exists(saved_path):
                for srv in all_servers:
                    if srv["full_path"] == saved_path and srv["is_writable"]: return saved_path
        except Exception: pass
    writable_servers = [s for s in all_servers if s["is_writable"]]
    if not writable_servers: return ""
    servers_with_hst = [s for s in writable_servers if s["has_hst"]]
    if servers_with_hst:
        servers_with_hst.sort(key=lambda x: (-x["hst_count"], x["server_name"]))
        chosen = servers_with_hst[0]
        _save_mt4_path(chosen["full_path"])
        return chosen["full_path"]
    chosen = writable_servers[0]
    _save_mt4_path(chosen["full_path"])
    return chosen["full_path"]

MT4_HISTORY_PATH = find_mt4_history_path()
if not MT4_HISTORY_PATH:
    MT4_HISTORY_PATH = os.path.join(user_home, "Desktop", "MT4_History_Fallback")
    os.makedirs(MT4_HISTORY_PATH, exist_ok=True)

SESSION_FILE = Path("session.json")
SESSION_STATE_FILE = Path("session_state.json")
EMAIL_FILE = Path("saved_email.txt")

class SessionManager:
    def __init__(self): self.state = self._load_state()
    def _load_state(self) -> dict:
        try:
            if SESSION_STATE_FILE.exists(): return json.loads(SESSION_STATE_FILE.read_text())
        except Exception: pass
        return {"last_login": 0, "last_success": False, "failed_auth_count": 0, "email": ""}
    def _save_state(self):
        try: SESSION_STATE_FILE.write_text(json.dumps(self.state, indent=2))
        except Exception: pass
    def should_force_fresh(self) -> bool:
        if not self.state.get("last_success", False): return True
        if self.state.get("failed_auth_count", 0) >= 2: return True
        if time.time() - self.state.get("last_login", 0) > 7 * 24 * 3600: return True
        return False
    def record_success(self, email: str):
        self.state.update({"last_login": time.time(), "last_success": True, "failed_auth_count": 0, "email": email})
        self._save_state()
        EMAIL_FILE.write_text(email)
    def record_failure(self, error: str):
        self.state["last_login"] = time.time()
        self.state["last_success"] = False
        self.state["failed_auth_count"] = self.state.get("failed_auth_count", 0) + 1
        self._save_state()
    def get_saved_email(self) -> str:
        email = self.state.get("email", "")
        return email if email else (EMAIL_FILE.read_text().strip() if EMAIL_FILE.exists() else "")
    @staticmethod
    def delete_session_file():
        if SESSION_FILE.exists():
            try: SESSION_FILE.unlink(); return True
            except Exception: pass
        return False
    @staticmethod
    def delete_browser_dir():
        browser_dir = Path("browser")
        if browser_dir.exists():
            try: shutil.rmtree(browser_dir, ignore_errors=True); return True
            except Exception: pass
        return False

session_manager = SessionManager()

# ==============================================================================
# UPDATED ASSET LIST & CANDLE COUNT SETTINGS
# ==============================================================================
ASSET_LIST = [
    "BRLUSD_otc", "USDARS_otc", "USDBDT_otc", "USDCOP_otc", "USDEGP_otc",
    "USDIDR_otc", "USDINR_otc", "USDMXN_otc", "USDNGN_otc", "USDPHP_otc",
    "USDPKR_otc", "USDZAR_otc", "AUDCAD_otc", "AUDCHF_otc", "AUDJPY_otc",
    "AUDNZD_otc", "AUDUSD_otc", "CADCHF_otc", "CADJPY_otc", "CHFJPY_otc",
    "EURAUD_otc", "EURCAD_otc", "EURCHF_otc", "EURGBP_otc", "EURJPY_otc",
    "EURNZD_otc", "EURUSD_otc", "GBPAUD_otc", "GBPCAD_otc", "GBPCHF_otc",
    "GBPJPY_otc", "GBPNZD_otc", "GBPUSD_otc", "NZDCAD_otc", "NZDCHF_otc",
    "NZDJPY_otc", "NZDUSD_otc", "USDCAD_otc", "USDCHF_otc", "USDDZD_otc", "USDJPY_otc",
]

PERIOD = 1
PERIOD_SECONDS = 60
# ===== FIX 4: استعادة 1000 شمعة (المستخدم يطلب العدد الكامل) =====
# الإعداد السابق 500 كان لتقليل الضغط، لكن المستخدم يريد 1000 شمعة بنفس السرعة (4s).
# الحل: نُعيد workers=5 + chunk=200 (كما في الأصل) ونُبقي بقية إصلاحات عدم الانقطاع.
INITIAL_CANDLES = 1000
MIN_CANDLES_THRESHOLD = 100
HISTORY_DAYS = 0.75
FETCH_DURATION_SECONDS = int(86400 * HISTORY_DAYS)
STREAM_POLL_INTERVAL = 0.15
# ===== FIX 4: WRITE_INTERVAL = 0.5s بدلاً من 3.0s (المستخدم يطلب تحديث كل 500ms) =====
WRITE_INTERVAL = 0.5
STALE_DATA_TIMEOUT = 180
STALE_RATIO_TRIGGER = 0.8
# ===== FIX 7: KEEPALIVE_PING_INTERVAL = 5s =====
# المستخدم: "يجب ان نجد طريقة تبقي الاتصال مستمر ولا ينقطع".
# 10s كان كافياً للحالات العادية، لكن أثناء الجلب الكثيف (5 workers × 41 أصل)
# قد لا يصل keepalive قبل أن يقطع الخادم. 5s أضمن.
KEEPALIVE_PING_INTERVAL = 5
RECONNECT_CHECK_INTERVAL = 1
RECONNECT_BASE_DELAY = 2
RECONNECT_MAX_DELAY = 30
STATUS_REFRESH_INTERVAL = 0.5
# ===== FIX 7: watchdog أكثر عدوانية =====
# لاكتشاف الصمت مبكراً وإعادة التدوير قبل أن يقطع الخادم.
# الكود الأصلي STALE_MESSAGE_TIMEOUT=45s + STALE_WATCHDOG_INTERVAL=5s
# => latency كشف الصمت = 45-50s (طويل جداً)
# FIX 7: STALE_MESSAGE_TIMEOUT=20s + STALE_WATCHDOG_INTERVAL=3s
# => latency كشف الصمت = 20-23s (أسرع بـ ~2x)
STALE_MESSAGE_TIMEOUT = 20
STALE_WATCHDOG_INTERVAL = 3  # كل 3s يفحص (was 5s)
ENGINEIO_PING_INTERVAL = 20  # إرسال "2" (engine.io ping) كل 20s — بروتوكول Socket.IO EIO=3
# ===== FIX 4: استعادة سرعة 4s لجلب 1000 شمعة =====
# الكود الأصلي (الذي كان يعمل بـ 4s لـ 1000 شمعة):
#   max_workers=5, chunk=period*200 (12000s), delay=0.1s
# الحل: نُعيد هذه الإعدادات لكن نُبقي:
#   - FETCH_ASSET_DELAY صغير (0.1s) لراحة الخادم بين الأصول
#   - كشف الاتصال المُقطع في workers (من FIX 3)
#   - exponential backoff في retry (من FIX 3)
#   - عداد الانقطاعات في main loop (من FIX 3)
# النتيجة: سرعة 4s + لا انقطاع (إصلاحات عدم الانقطاع في FIX 1+2 تمنع الانقطاع)
FETCH_MAX_WORKERS = 5          # FIX 7: إبقاء 5 workers (السرعة الأصلية ~4s لكل 1000 شمعة)
FETCH_CHUNK_SIZE = 200         # FIX 7: إبقاء 200 (الإعداد الأصلي للسرعة)
FETCH_BATCH_DELAY = 0.1        # FIX 7: إبقاء 0.1s (السرعة الأصلية)
FETCH_ASSET_DELAY = 0.1        # FIX 7: إبقاء 0.1s (سريع — لا تباطؤ)
# ===== FIX 7: لا cooldown — المستخدم لا يريد تباطؤ =====
FETCH_COOLDOWN_EVERY = 0       # 0 = معطّل
FETCH_COOLDOWN_DURATION = 0.0  # 0 = معطّل
FETCH_TIMEOUT = 30             # 30s (was 25) — وقت كافٍ للـ batches الكبيرة
RETRY_BACKOFF_BASE = 2         # exponential backoff base
RETRY_BACKOFF_MAX = 15         # حد أقصى للتأخير بين الـ retries
MAX_FETCH_RETRIES = 5          # 5 محاولات
# الحد الأقصى لعدد عمليات إعادة الاتصال المتتالية أثناء الجلب قبل التوقف
MAX_RECONNECTS_DURING_FETCH = 8
# ===== FIX 4: gap fill بـ 20 شمعة بدلاً من 10 =====
GAP_FILL_CANDLES = 20

ASYNC_LOOP = None
ASYNC_ENGINE_GENERATION = 0
_ENGINE_READY = threading.Event()
CONNECTION_ALIVE = False
CLIENT = None
EMAIL = None
PASSWORD = None
RECONNECTING = False
ALL_STREAMING_ASSETS = []
LAST_HEALTH_CHECK = 0
HEALTH_CHECK_INTERVAL = 20
# ===== FIX B: تتبع وقت انقطاع الاتصال لإعادة جلب الشموع بعد انقطاع طويل =====
# المستخدم: "عندما ينقطع الاتصال لمدة اكثر من ساعة خليه يعيد جلب الشموع كلها من جديد".
# نُسجّل وقت بداية الانقطاع هنا، وعند عودة الاتصال نُقارن المدة بهذا الحد —
# إذا تجاوزته، نُعيد جلب 1000 شمعة لكل الأصول من الصفر بدلاً من سد الثغرات فقط.
LAST_CONNECTION_DROP_TIME = 0            # 0 = لا يوجد انقطاع قيد التتبع
LONG_DISCONNECT_THRESHOLD = 3600        # 3600s = 1 ساعة

def _asyncio_loop_exception_handler(loop, context):
    exc = context.get("exception")
    if exc: log_exception(f"asyncio loop (gen {ASYNC_ENGINE_GENERATION})", exc)

def start_async_engine():
    global ASYNC_LOOP, ASYNC_ENGINE_GENERATION, CONNECTION_ALIVE
    while True:
        try:
            ASYNC_ENGINE_GENERATION += 1
            gen = ASYNC_ENGINE_GENERATION
            new_loop = asyncio.new_event_loop()
            new_loop.set_exception_handler(_asyncio_loop_exception_handler)
            asyncio.set_event_loop(new_loop)
            ASYNC_LOOP = new_loop
            _ENGINE_READY.set()
            if gen > 1:
                logmsg(f"[AsyncEngine] event loop recreated (gen {gen}). Rescheduling tasks...")
                CONNECTION_ALIVE = False
                asyncio.run_coroutine_threadsafe(health_monitor(), ASYNC_LOOP)
                asyncio.run_coroutine_threadsafe(auto_reconnect(), ASYNC_LOOP)
                asyncio.run_coroutine_threadsafe(keepalive_loop(), ASYNC_LOOP)
                # ===== FIX: تشغيل الـ stale watchdog أيضاً بعد إعادة إنشاء الـ loop =====
                asyncio.run_coroutine_threadsafe(stale_message_watchdog(), ASYNC_LOOP)
                for asset in ALL_STREAMING_ASSETS:
                    asset.stream_task = None
                    asset.streaming = False
            new_loop.run_forever()
        except Exception as e:
            log_exception(f"AsyncEngine (gen {ASYNC_ENGINE_GENERATION})", e)
            CONNECTION_ALIVE = False
            time.sleep(1)

async_thread = threading.Thread(target=start_async_engine, daemon=True, name="AsyncEngine")
async_thread.start()
_ENGINE_READY.wait(timeout=10)

class Asset:
    @staticmethod
    def _derive_mt4_symbol(raw_symbol: str) -> str:
        s = raw_symbol.strip()
        is_otc = s.upper().endswith("_OTC")
        if is_otc:
            base = s[:-4].upper()
            result = f"{base}-OTC"
        else:
            result = s.upper()
        return result[:12] if result else raw_symbol.upper()[:12]

    def __init__(self, symbol):
        self.api_symbol = symbol
        self.symbol = self._derive_mt4_symbol(symbol)
        self.period = PERIOD
        self.price = 0.0
        self.path = os.path.join(MT4_HISTORY_PATH, f"{self.symbol}{PERIOD}.hst")
        self.candles = []
        self.last_write = 0.0
        self.updates = 0
        self.streaming = False
        self.stream_task = None
        self.last_update_time = 0
        self.last_saved_close = 0.0
        self.last_saved_candle_time = 0
        self.last_saved_candle_count = 0
        self.dirty = False
        self._gap_filled = False

    def digits(self, price: float = None) -> int:
        sym = self.symbol.upper()
        if "JPY" in sym: return 3
        p = price if price is not None else self.price
        if p and p > 0:
            if p < 0.5:  return 6
            if p < 1:    return 5
            if p < 5:    return 5
            if p < 10:   return 4
            if p < 50:   return 4
            if p < 100:  return 3
            return 2
        if any(x in sym for x in ["IDR", "COP", "ARS", "NGN", "PKR", "DZD", "EGP", "MXN", "PHP", "INR", "BDT", "ZAR", "BRL"]):
            return 2
        return 5

    def has_new_data(self):
        if not self.candles: return False
        c = self.candles[-1]
        return (c['close'] != self.last_saved_close or c['time'] != self.last_saved_candle_time or len(self.candles) != self.last_saved_candle_count)

    def mark_dirty(self): self.dirty = True

    def write(self, force=False):
        if not force and not self.has_new_data(): return False
        temp = self.path + ".tmp"
        try:
            with open(temp, 'wb') as f:
                f.write(struct.pack('<i', 400))
                f.write(b"(C)opyright 2003, MetaQuotes Software Corp.".ljust(64, b'\0'))
                f.write(self.symbol.encode('ascii').ljust(12, b'\0')[:12])
                f.write(struct.pack('<i', self.period))
                first_price = self.candles[0]['close'] if self.candles else self.price
                f.write(struct.pack('<i', self.digits(first_price)))
                f.write(struct.pack('<i', int(time.time())))
                f.write(struct.pack('<i', int(time.time())))
                f.write(b'\0' * 52)
                for c in self.candles:
                    f.write(struct.pack('<i', c['time']))
                    f.write(struct.pack('<d', c['open']))
                    f.write(struct.pack('<d', c['low']))
                    f.write(struct.pack('<d', c['high']))
                    f.write(struct.pack('<d', c['close']))
                    f.write(struct.pack('<q', int(c.get('volume', 0))))
            # ===== FIX 4: إصلاح WinError 5 (Access Denied) + WinError 32 =====
            # الكود الأصلي يُعيد فقط عند WinError 32. لكن WinError 5 (Access Denied)
            # يحدث أيضاً عندما يكون MT4 يقرأ الملف (ليس فقط يكتبه).
            # الحل: retry على WinError 5 + 32 + محاولة كتابة مباشرة كـ fallback.
            def _is_lock_error(err_str):
                err_str = err_str.lower()
                return (
                    "winerror 32" in err_str or
                    "used by another process" in err_str or
                    "winerror 5" in err_str or
                    "access denied" in err_str or
                    "accès refusé" in err_str or
                    "acces refusé" in err_str or
                    "permission" in err_str
                )
            replaced = False
            for attempt in range(8):  # 8 محاولات بدلاً من 5
                try:
                    os.replace(temp, self.path)
                    replaced = True
                    break
                except (PermissionError, OSError) as e:
                    err_str = str(e)
                    if _is_lock_error(err_str):
                        # تأخير تدريجي: 50ms, 100ms, 150ms, 200ms, 250ms...
                        time.sleep(0.05 + 0.05 * attempt)
                        continue
                    raise
            if not replaced:
                # ===== FIX 4: fallback — كتابة مباشرة بدون rename =====
                # إذا فشل os.replace 8 مرات، نحاول الكتابة مباشرة للملف.
                try:
                    with open(self.path, 'wb') as f:
                        # إعادة كتابة كامل الملف (header + candles)
                        with open(temp, 'rb') as src:
                            f.write(src.read())
                    replaced = True
                except Exception as fallback_err:
                    if not _is_lock_error(str(fallback_err)):
                        logmsg(f"[write:{self.symbol}] fallback write failed: {fallback_err}")
            try:
                if os.path.exists(temp): os.remove(temp)
            except Exception: pass
            if replaced:
                self.last_write = time.time()
                if self.candles:
                    self.last_saved_close = self.candles[-1]['close']
                    self.last_saved_candle_time = self.candles[-1]['time']
                    self.last_saved_candle_count = len(self.candles)
                self.dirty = False
                return True
            return False
        except Exception as e:
            err_str = str(e).lower()
            # ===== FIX 8: لا نسجل WinError 2 (file not found) + WinError 5 + 32 =====
            # المستخدم لا يريد رؤية هذه الأخطاء — هي مؤقتة ويتم retry تلقائياً.
            if not any(x in err_str for x in [
                'winerror 2', 'winerror 5', 'winerror 32', 'winerror 13',
                'introuvable', 'refusé', 'access', 'permission', 'used by another',
                'ebusy', 'eperm', 'no such file'
            ]):
                logmsg(f"[write:{self.symbol}] write failed: {e}")
            try:
                if os.path.exists(temp): os.remove(temp)
            except Exception: pass
            return False

class WriterThread(threading.Thread):
    """FIX 11: إعادة WriterThread للنشاط — كتابة HST كل 500ms عبر Asset.write.
    
    المستخدم طلب: لا تُغيّر طريقة جلب الشموع (1000 شمعة بسرعة 4s).
    لذلك نُبقي المنطق الأصلي:
      - fetch_candles_with_retry يجلب الشموع (1000 شمعة)
      - Asset.write يكتب HST باسم {derived_symbol}{PERIOD}.hst (AUDJPY-OTC1.hst)
      - WriterThread يفحص asset.dirty كل 100ms + يكتب HST كل 500ms
    
    FIX 10 (نموذج مرجعي للإرسال) يُطبّق فقط في realtime_stream عبر MT4_WRITER.update_candle.
    لكن لتفادي الكتابة المزدوجة، نُقفل Asset.write في WriterThread إذا كان MT4_WRITER
    يُدير نفس الأصل بالفعل.
    """
    def __init__(self):
        super().__init__(daemon=True, name="WriterThread")
        self.running = True
    def run(self):
        while self.running:
            try:
                now = time.time()
                dirty_count = 0
                for asset in ALL_STREAMING_ASSETS:
                    # ===== FIX 11: لا نكتب إذا كان MT4_WRITER يُدير هذا الأصل =====
                    # (تفادي الكتابة المزدوجة — ملف واحد فقط لكل أصل)
                    if asset.symbol in MT4_WRITER.sync_state:
                        continue
                    if asset.dirty and (now - asset.last_write >= WRITE_INTERVAL):
                        if asset.write(): dirty_count += 1
                if dirty_count > 0: refresh_mt4()
                time.sleep(0.1)
            except Exception as e:
                logmsg(f"[WriterThread] loop error: {e}")
                time.sleep(0.5)

writer_thread = WriterThread()
writer_thread.start()

async def connect_quotex(email, password, force_fresh=False, max_attempts=3):
    global CLIENT, CONNECTION_ALIVE, EMAIL, PASSWORD
    EMAIL, PASSWORD = email, password
    for attempt in range(1, max_attempts + 1):
        try:
            if CLIENT:
                try:
                    close_task = asyncio.create_task(CLIENT.close())
                    await asyncio.wait([close_task], timeout=3.0)
                except Exception: pass
                finally: CLIENT = None
            await asyncio.sleep(0.3)
            if force_fresh or attempt > 1:
                session_manager.delete_session_file()
                session_manager.delete_browser_dir()
            CLIENT = Quotex(email=email, password=password, host="qxbroker.com", lang="en")
            with suppress_terminal_output():
                check, reason = await CLIENT.connect()
            if check:
                try:
                    await CLIENT.change_account("PRACTICE")
                    await asyncio.sleep(0.5)
                except Exception: pass
                try: await CLIENT.get_all_assets()
                except Exception: pass
                CONNECTION_ALIVE = True
                session_manager.record_success(email)
                return True
            else:
                error_msg = str(reason) if reason else "Unknown error"
                session_manager.record_failure(error_msg)
        except Exception as e:
            error_msg = str(e)[:200]
            session_manager.record_failure(error_msg)
            if attempt < max_attempts: await asyncio.sleep(5 * attempt)
    CONNECTION_ALIVE = False
    return False

async def keepalive_loop():
    # ===== FIX 7: keepalive نشط جداً (5s) + يبقى نشطاً أثناء الجلب =====
    # المستخدم: "يجب ان نجد طريقة تبقي الاتصال مستمر ولا ينقطع".
    # المشكلة: أثناء جلب الشموع، يكثر الضغط على الخادم، لكن keepalive_loop
    # كان يعمل بـ `await asyncio.sleep(KEEPALIVE_PING_INTERVAL)` الذي يحجبه.
    # الحل: استخدم `asyncio.sleep` قصير جداً (0.5s) ثم تحقق من الوقت المنقضي.
    # هذا يضمن أن keepalive يستجيب فوراً لأي تغيير في الحالة.
    tick_count = 0
    last_ping_at = 0.0
    while True:
        await asyncio.sleep(0.5)  # فحص كل 500ms (سريع)
        now = time.time()
        # تحقق: هل حان وقت الـ ping التالي؟
        if now - last_ping_at < KEEPALIVE_PING_INTERVAL:
            continue
        last_ping_at = now
        if not CONNECTION_ALIVE or CLIENT is None or CLIENT.api is None: continue
        try:
            # 1) engine.io ping (بروتوكول Socket.IO EIO=3) — يحافظ على مستوى النقل
            CLIENT.api.send_websocket_request("2", no_force_send=False)
            # 2) application-level tick — يحافظ على الجلسة على مستوى التطبيق
            CLIENT.api.send_websocket_request('42["tick"]', no_force_send=False)
            # 3) بين الحين والآخر، اطلب قائمة الأدوات لإبقاء القناة نشطة
            if tick_count % 3 == 0:
                CLIENT.api.send_websocket_request('42["instruments/get"]', no_force_send=False)
            tick_count += 1
        except Exception:
            pass


async def stale_message_watchdog():
    # ===== FIX: watchdog لصمت الرسائل + تسجيل وقت الانقطاع =====
    # يكتشف إذا لم تصل أي رسالة WS من الخادم خلال STALE_MESSAGE_TIMEOUT (45s)
    # ويُعيد تدوير الاتصال بأنفسنا بدلاً من انتظار الخادم ليقطعه.
    # هذا يُقلّل latency إعادة الاتصال من ~25s إلى <5s.
    # FIX B: نسجّل وقت بداية الانقطاع حتى يتمكن auto_reconnect لاحقاً من
    # تحديد ما إذا كان الانقطاع طويلاً (> ساعة) — وفي تلك الحالة يُعيد
    # جلب كل الشموع من الصفر بدلاً من سد الثغرات فقط.
    global CONNECTION_ALIVE, LAST_CONNECTION_DROP_TIME
    while True:
        await asyncio.sleep(STALE_WATCHDOG_INTERVAL)
        if not CONNECTION_ALIVE or CLIENT is None or CLIENT.api is None:
            continue
        try:
            silent_for = time.time() - CLIENT.api.last_message_at
            if silent_for > STALE_MESSAGE_TIMEOUT:
                logmsg(
                    f"[stale_watchdog] no messages for {silent_for:.1f}s "
                    f"(>{STALE_MESSAGE_TIMEOUT}s); recycling connection."
                )
                # ===== FIX B: سجّل وقت الانقطاع لإعادة جلب الشموع لاحقاً =====
                # إذا تجاوز الانقطاع LONG_DISCONNECT_THRESHOLD (1h) عند العودة،
                # يُعاد جلب كل الشموع من جديد بدلاً من سد الثغرات فقط.
                if LAST_CONNECTION_DROP_TIME == 0:
                    LAST_CONNECTION_DROP_TIME = time.time()
                    logmsg(f"[stale_watchdog] drop time recorded at {LAST_CONNECTION_DROP_TIME:.0f}")
                CONNECTION_ALIVE = False
                # محاولة إغلاق الـ WS بإرسال close frame لتفعيل on_close
                try:
                    if CLIENT.api.websocket_client and CLIENT.api.websocket_client.wss:
                        CLIENT.api.websocket_client.wss.close()
                except Exception:
                    pass
                # auto_reconnect سيلتقط الحالة ويُعيد الاتصال
        except Exception as e:
            logmsg(f"[stale_watchdog] error: {e}")

async def health_monitor():
    global LAST_HEALTH_CHECK, CONNECTION_ALIVE
    consecutive_dead_checks = 0
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        now = time.time()
        LAST_HEALTH_CHECK = now
        if not CONNECTION_ALIVE or CLIENT is None:
            consecutive_dead_checks = 0
            continue
        is_dead = False
        dead_reason = ""
        stale_count = sum(1 for a in ALL_STREAMING_ASSETS if a.updates > 0 and (now - a.last_update_time) > STALE_DATA_TIMEOUT)
        if stale_count > len(ALL_STREAMING_ASSETS) * STALE_RATIO_TRIGGER:
            is_dead = True
            dead_reason = f"stale ratio {stale_count}/{len(ALL_STREAMING_ASSETS)} exceeded {STALE_RATIO_TRIGGER}"
        if is_dead:
            logmsg(f"[health_monitor] marking connection DEAD: {dead_reason}")
            CONNECTION_ALIVE = False
            consecutive_dead_checks = 0

async def auto_reconnect():
    # ===== FIX B: كشف الانقطاع الطويل + إعادة جلب كل الشموع =====
    # المستخدم: "عندما ينقطع الاتصال لمدة اكثر من ساعة خليه يعيد جلب الشموع كلها من جديد".
    # نُسجّل وقت بداية الانقطاع (سواء من stale_message_watchdog أو من أي مكان آخر)،
    # وعند نجاح إعادة الاتصال نقارن المدة بـ LONG_DISCONNECT_THRESHOLD (1h).
    # إذا تجاوزتها، نُعيد جلب 1000 شمعة لكل الأصول من الصفر بدلاً من سد الثغرات فقط.
    global CLIENT, CONNECTION_ALIVE, RECONNECTING, LAST_CONNECTION_DROP_TIME
    consecutive_failures = 0
    while True:
        await asyncio.sleep(RECONNECT_CHECK_INTERVAL)
        # ===== FIX B: سجّل وقت الانقطاع عند اكتشاف فقد الاتصال (أي مصدر) =====
        # stale_message_watchdog يسجّله من جانبه، لكن هناك مصادر أخرى للانقطاع
        # (on_close، on_error، connect_quotex الذي يفشل، الخ). هذا الموقع هو
        # نقطة الكشف الموحّدة لأنه يعمل كل ثانية.
        if not CONNECTION_ALIVE and LAST_CONNECTION_DROP_TIME == 0:
            LAST_CONNECTION_DROP_TIME = time.time()
            logmsg(f"[reconnect] connection loss detected at {LAST_CONNECTION_DROP_TIME:.0f}; "
                   f"will re-fetch all candles if outage exceeds {LONG_DISCONNECT_THRESHOLD}s")
        if CONNECTION_ALIVE or RECONNECTING:
            consecutive_failures = 0
            continue
        RECONNECTING = True
        try:
            email = session_manager.get_saved_email()
            # ===== FIX: لا نُخرج من الـ try بدون إعادة ضبط RECONNECTING =====
            # الكود الأصلي: `if not (email and PASSWORD): continue`
            # => يخرج من try مع RECONNECTING = True => يبقى عالقاً للأبد
            # => لا تتم إعادة الاتصال مطلقاً!
            if not (email and PASSWORD):
                # نُعيد ضبط RECONNECTING قبل المتابعة
                RECONNECTING = False
                continue
            delay = 0 if consecutive_failures == 0 else min(RECONNECT_BASE_DELAY * (2 ** (consecutive_failures - 1)), RECONNECT_MAX_DELAY)
            if delay > 0:
                logmsg(f"[reconnect] connection lost, retrying in {delay:.0f}s...")
                await asyncio.sleep(delay)
            else:
                logmsg("[reconnect] connection lost, reconnecting immediately...")
            success = await connect_quotex(email, PASSWORD, force_fresh=True, max_attempts=1)
            if success:
                logmsg("[reconnect] reconnect successful, restarting streams...")
                consecutive_failures = 0
                # ===== FIX 7: لا auto-throttle (المستخدم لا يريد تباطؤ) =====
                # ===== FIX: إعادة ضبط last_message_at بعد نجاح الاتصال =====
                # حتى لا يطلق الـ stale_watchdog خطأً بعد إعادة الاتصال مباشرة.
                if CLIENT is not None and CLIENT.api is not None:
                    CLIENT.api.last_message_at = time.time()
                # ===== FIX B: كشف الانقطاع الطويل وإطلاق إعادة جلب كاملة =====
                drop_duration = 0.0
                should_refetch_all = False
                if LAST_CONNECTION_DROP_TIME > 0:
                    drop_duration = time.time() - LAST_CONNECTION_DROP_TIME
                    if drop_duration > LONG_DISCONNECT_THRESHOLD:
                        should_refetch_all = True
                        logmsg(
                            f"[reconnect] LONG disconnect detected: {drop_duration/60:.1f} min "
                            f"> {LONG_DISCONNECT_THRESHOLD/60:.0f} min threshold — "
                            f"will re-fetch ALL candles from scratch"
                        )
                # إعادة ضبط وقت الانقطاع بغضّ النظر عن النتيجة
                LAST_CONNECTION_DROP_TIME = 0
                if should_refetch_all:
                    # إعادة جلب كل الشموع بدلاً من مجرد إعادة تشغيل الـ streams
                    try:
                        asyncio.run_coroutine_threadsafe(refetch_all_candles(), ASYNC_LOOP)
                    except Exception as e:
                        logmsg(f"[reconnect] failed to schedule full re-fetch: {e}")
                        # fallback: أعد تشغيل الـ streams فقط
                        for asset in ALL_STREAMING_ASSETS:
                            try:
                                if asset.stream_task and not asset.stream_task.done():
                                    asset.stream_task.cancel()
                                asset.streaming = False
                                asset.stream_task = asyncio.run_coroutine_threadsafe(realtime_stream(asset), ASYNC_LOOP)
                                await asyncio.sleep(0.05)
                            except Exception as e2:
                                logmsg(f"[reconnect] failed to restart stream for {asset.symbol}: {e2}")
                else:
                    # الانقطاع كان قصيراً (< ساعة) — أعد تشغيل الـ streams فقط
                    if drop_duration > 0:
                        logmsg(f"[reconnect] short disconnect ({drop_duration:.1f}s) — restarting streams only")
                    for asset in ALL_STREAMING_ASSETS:
                        try:
                            if asset.stream_task and not asset.stream_task.done():
                                asset.stream_task.cancel()
                            asset.streaming = False
                            asset.stream_task = asyncio.run_coroutine_threadsafe(realtime_stream(asset), ASYNC_LOOP)
                            await asyncio.sleep(0.05)
                        except Exception as e:
                            logmsg(f"[reconnect] failed to restart stream for {asset.symbol}: {e}")
            else:
                consecutive_failures += 1
        except Exception as e:
            logmsg(f"[reconnect] unexpected error: {e}")
            consecutive_failures += 1
        finally:
            RECONNECTING = False

def _make_progress_printer(symbol: str, start_ts: float, idx: int, total: int):
    display = pretty_asset_name(symbol)
    def on_progress(current, total, label=None, worker_label=None):
        total = total or FETCH_DURATION_SECONDS
        pct = min(current / total, 1.0) if total > 0 else 0
        bar_len = 20
        filled = int(bar_len * pct)
        bar = "#" * filled + "-" * (bar_len - filled)
        elapsed = time.time() - start_ts
        print(f"\r  {display:<25} [{bar}] {pct*100:4.1f}% {elapsed:>2.0f}s", end="", flush=True)
    return on_progress

async def fetch_candles_once(asset: Asset, idx=1, total=1):
    api_name = asset.api_symbol
    display_name = asset.symbol
    candles = []
    if hasattr(CLIENT, 'get_historical_candles'):
        try:
            on_progress = _make_progress_printer(display_name, time.time(), idx, total)
            # ===== FIX 6: timeout أكبر (60s) لأن الطلب التسلسلي قد يستغرق أكثر =====
            # الكود الأصلي: timeout=60, max_workers=5
            # FIX 3: timeout=25 (لكن كان مع 5 workers)
            # FIX 6: timeout=60 (مع 1 worker + chunk=1000 شمعة لكل طلب)
            res = await asyncio.wait_for(
                CLIENT.get_historical_candles(
                    api_name,
                    amount_of_seconds=FETCH_DURATION_SECONDS,
                    period=PERIOD_SECONDS,
                    max_workers=FETCH_MAX_WORKERS,
                    progress_callback=on_progress
                ),
                timeout=60,  # FIX 6: timeout أكبر للطلب التسلسلي الكبير
            )
            if res and len(res) > 0: candles = res
        except Exception as e:
            print()
            logmsg(f"[fetch:{display_name}] get_historical_candles failed: {e}")
    if candles:
        formatted = []
        for c in candles:
            if not isinstance(c, dict): continue
            try:
                ts = int(float(c.get("time", c.get("timestamp", 0))))
                aligned = (ts // PERIOD_SECONDS) * PERIOD_SECONDS
                o, h, l, cl = float(c.get("open", 0)), float(c.get("high", c.get("max", 0))), float(c.get("low", c.get("min", 0))), float(c.get("close", 0))
                if o > 0 and h > 0 and l > 0 and cl > 0:
                    formatted.append({'time': aligned, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': random.randint(50, 200)})
            except Exception: continue
        seen, unique = set(), []
        for c in formatted:
            if c['time'] not in seen:
                seen.add(c['time'])
                unique.append(c)
        unique.sort(key=lambda x: x['time'])
        return unique[-INITIAL_CANDLES:]
    return []

async def fetch_candles_with_retry(asset: Asset, max_retries=3, idx=1, total=1):
    # ===== FIX 3: retry مع exponential backoff + كشف الاتصال =====
    # الكود الأصلي:
    #     for attempt in range(1, max_retries + 1):
    #         candles = await fetch_candles_once(asset, idx, total)
    #         if len(candles) >= MIN_CANDLES_THRESHOLD: ...
    #         asset.candles = candles; ...
    # المشكلة: لا backoff بين الـ retries + لا كشف للاتصال المُقطع
    # => إذا فشل الأول، يُحاول فوراً على نفس الاتصال المُقطع => فشل أيضاً
    # => يُعجل فيقطع الاتصال أكثر => المتابعة بالأصول التالية على اتصال ميت.
    max_retries = MAX_FETCH_RETRIES
    last_error = None
    for attempt in range(1, max_retries + 1):
        # تحقق من الاتصال قبل كل محاولة
        if not CONNECTION_ALIVE or CLIENT is None or CLIENT.api is None:
            logmsg(f"[fetch_retry:{asset.symbol}] connection dead before attempt {attempt}; waiting for reconnect...")
            # انتظر حتى يتم إعادة الاتصال (timeout 15s)
            try:
                await wait_until(
                    lambda: CONNECTION_ALIVE and CLIENT is not None and CLIENT.api is not None,
                    timeout=15.0,
                    poll_interval=0.5,
                )
            except asyncio.TimeoutError:
                logmsg(f"[fetch_retry:{asset.symbol}] reconnect did not happen within 15s; giving up on this asset")
                return 0, attempt
        try:
            candles = await fetch_candles_once(asset, idx, total)
        except Exception as e:
            candles = []
            last_error = e
            logmsg(f"[fetch_retry:{asset.symbol}] attempt {attempt}/{max_retries} raised: {e}")
        if len(candles) >= MIN_CANDLES_THRESHOLD:
            asset.candles = candles
            if candles: asset.price = candles[-1]['close']
            asset.write(force=True)
            return len(candles), attempt
        # حفظ ما لدينا حتى لو كان ناقصاً
        asset.candles = candles
        if candles: asset.price = candles[-1]['close']
        asset.write(force=True)
        # ===== FIX 3: exponential backoff بين الـ retries =====
        if attempt < max_retries:
            delay = min(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)), RETRY_BACKOFF_MAX)
            logmsg(f"[fetch_retry:{asset.symbol}] attempt {attempt}/{max_retries} got {len(candles)} candles; retry in {delay:.1f}s")
            await asyncio.sleep(delay)
    if last_error:
        logmsg(f"[fetch_retry:{asset.symbol}] all {max_retries} attempts failed. Last error: {last_error}")
    return len(candles), max_retries

async def realtime_stream(asset: Asset):
    internal = asset.api_symbol
    try:
        # ===== EVENT-DRIVEN FIX =====
        # بديل:
        #   while CONNECTION_ALIVE and CLIENT is None: await asyncio.sleep(0.5)
        # ننتظر حتى timeout قصير بفاصل 200ms فقط.
        try:
            await wait_until(
                lambda: not (CONNECTION_ALIVE and CLIENT is None),
                timeout=10.0,
                poll_interval=0.2,
            )
        except asyncio.TimeoutError:
            pass
        if not CONNECTION_ALIVE or CLIENT is None:
            asset.streaming = False
            return
        await CLIENT.start_candles_stream(internal, PERIOD_SECONDS)
        await asyncio.sleep(1.5)
        asset.streaming = True
        # ===== FIX 12: تهيئة MT4_WRITER.sync_state بـ 1000 شمعة المجلوبة =====
        # المشكلة السابقة: MT4_WRITER.update_candle كان يبدأ sync_state فارغ
        # => الملف الناتج يحوي ~19 شمعة فقط (1KB) بدلاً من 1000 شمعة (44KB)
        # الحل: نسخ asset.candles (1000 شمعة) إلى sync_state[derived_symbol]
        # عند بدء realtime_stream، ثم update_candle يضيف الشمعة الجديدة
        # إلى sync_state الذي يحوي 1000 شمعة بالفعل.
        if asset.candles and asset.symbol not in MT4_WRITER.sync_state:
            MT4_WRITER.sync_state[asset.symbol] = {
                'period': PERIOD,
                'candles': list(asset.candles),  # نسخ 1000 شمعة
                'last_write': 0,
                'last_price': float(asset.candles[-1]['close']) if asset.candles else 0.0,
            }
    except Exception as e:
        logmsg(f"[stream:{internal}] failed to start stream: {e}")
        asset.streaming = False
        return
    consecutive_errors = 0
    while CONNECTION_ALIVE:
        try:
            if CLIENT is None or not getattr(getattr(CLIENT, 'api', None), 'state', None) or getattr(CLIENT.api.state, 'status', None) != 1:
                # ===== EVENT-DRIVEN FIX =====
                # بديل await asyncio.sleep(1) — polling أقصر (200ms)
                await asyncio.sleep(0.2)
                continue
            candle = None
            if not candle and hasattr(CLIENT, 'api') and CLIENT.api:
                candle = CLIENT.api.realtime_candles.get(internal)
            if candle:
                consecutive_errors = 0
                if isinstance(candle, list) and len(candle) >= 3:
                    ts, price = int(candle[1]), float(candle[2])
                elif isinstance(candle, dict):
                    ts = int(candle.get("time", candle.get("timestamp", time.time())))
                    price = float(candle.get("price", candle.get("close", 0)))
                else:
                    await asyncio.sleep(STREAM_POLL_INTERVAL)
                    continue
                if price > 0 and ts > 0:
                    # ===== FIX 10: استخدم MT4_WRITER.update_candle بدلاً من asset.mark_dirty =====
                    # هذا يضمن كتابة HST واحدة عبر MT4Writer.write_to_file (لا تكرار)
                    # MT4_WRITER.update_candle يُحدّث sync_state[derived_symbol] + يكتب HST كل 200ms
                    try:
                        MT4_WRITER.update_candle(asset.symbol, PERIOD, {'time': ts, 'price': price})
                    except Exception:
                        pass  # إخفاء أخطاء القفل
                    # تحديث asset.candles للعرض فقط (لا كتابة)
                    aligned_time = (ts // PERIOD_SECONDS) * PERIOD_SECONDS
                    if asset.candles:
                        last_candle = asset.candles[-1]
                        if last_candle['time'] == aligned_time:
                            last_candle['high'] = max(last_candle['high'], price)
                            last_candle['low'] = min(last_candle['low'], price)
                            last_candle['close'] = price
                        else:
                            asset.candles.append({'time': aligned_time, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': 1})
                    else:
                        asset.candles.append({'time': aligned_time, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': 1})
                    if len(asset.candles) > INITIAL_CANDLES: asset.candles = asset.candles[-INITIAL_CANDLES:]
                    asset.price = price
                    asset.updates += 1
                    asset.last_update_time = time.time()
                    # لا نستدعي asset.mark_dirty() — MT4_WRITER.update_candle يتكفل بالكتابة
            await asyncio.sleep(STREAM_POLL_INTERVAL)
        except asyncio.CancelledError:
            asset.streaming = False
            raise
        except asyncio.TimeoutError: continue
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= 10:
                logmsg(f"[stream:{internal}] too many consecutive errors, stopping stream")
                asset.streaming = False
                return
            # ===== EVENT-DRIVEN FIX =====
            # بديل await asyncio.sleep(1) — polling أقصر (200ms)
            await asyncio.sleep(0.2)
    asset.streaming = False


# ===== FIX B: إعادة جلب جميع الشموع بعد انقطاع طويل (> ساعة) =====
# المستخدم: "عندما ينقطع الاتصال لمدة اكثر من ساعة خليه يعيد جلب الشموع كلها من جديد".
# هذه الدالة تُعاد من auto_reconnect عندما يكتشف أن مدة الانقطاع تجاوزت
# LONG_DISCONNECT_THRESHOLD. تقوم بإعادة جلب 1000 شمعة لكل الأصول من الصفر،
# إعادة كتابة ملفات HST، وإعادة تشغيل الـ streams — تماماً كما يحدث عند بدء
# التشغيل الأول للسكريبت.
async def refetch_all_candles():
    """إعادة جلب كاملة لشموع جميع الأصول بعد انقطاع طويل للاتصال.

    هذه الدالة تُنفّذ:
      1. إيقاف الـ streams الحالية وإفراغ caches الأصول
      2. إعادة ضبط sync_state في MT4_WRITER (لإجبار إعادة كتابة HST)
      3. استدعاء fetch_candles_with_retry لكل أصل (يجلب 1000 شمعة)
      4. إعادة تشغيل realtime_stream لكل أصل
      5. تشغيل mt4_gap_filler لسد الثغرات بعد الجلب
    """
    if not ALL_STREAMING_ASSETS:
        logmsg("[refetch_all] no assets to re-fetch")
        return
    print(f"\n{Colors.CYAN}{'═'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  FULL RE-FETCH: long disconnect detected — refreshing all candles{Colors.RESET}")
    print(f"  • Assets: {len(ALL_STREAMING_ASSETS)}")
    print(f"  • Target per asset: {INITIAL_CANDLES} candles")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}")
    # 1) إيقاف الـ streams الحالية وإعادة ضبط حالة الأصول
    for asset in ALL_STREAMING_ASSETS:
        try:
            if asset.stream_task and not asset.stream_task.done():
                asset.stream_task.cancel()
        except Exception:
            pass
        asset.streaming = False
        asset.stream_task = None
        asset.candles = []
        asset.last_saved_close = 0.0
        asset.last_saved_candle_time = 0
        asset.last_saved_candle_count = 0
        asset.dirty = True
        asset._gap_filled = False
        asset.updates = 0
        asset.last_update_time = 0
        # إعادة ضبط sync_state في MT4_WRITER لإجبار إعادة الكتابة
        if asset.symbol in MT4_WRITER.sync_state:
            try: del MT4_WRITER.sync_state[asset.symbol]
            except Exception: pass
        if asset.symbol in MT4_WRITER._gap_filled:
            MT4_WRITER._gap_filled[asset.symbol] = False
    # 2) إعادة جلب الشموع لكل أصل
    total_loaded = 0
    total_assets = len(ALL_STREAMING_ASSETS)
    consecutive_disconnects = 0
    for idx, asset in enumerate(ALL_STREAMING_ASSETS, 1):
        # فحص الاتصال قبل كل أصل
        if not CONNECTION_ALIVE or CLIENT is None or CLIENT.api is None:
            logmsg(f"[refetch_all] connection lost again at asset {idx}/{total_assets}; aborting re-fetch")
            break
        display = pretty_asset_name(asset.api_symbol)
        start_time = time.time()
        try:
            candles_count, attempts = await fetch_candles_with_retry(
                asset, max_retries=MAX_FETCH_RETRIES, idx=idx, total=total_assets
            )
            elapsed = time.time() - start_time
            if candles_count >= MIN_CANDLES_THRESHOLD:
                total_loaded += candles_count
                consecutive_disconnects = 0
                attempts_str = "" if attempts == 1 else f" ({attempts} attempts)"
                print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.GREEN}{candles_count} candles in {elapsed:.1f}s{attempts_str}{Colors.RESET}")
            else:
                print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.RED}Only {candles_count} candles{Colors.RESET}")
        except Exception as e:
            print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.RED}Error: {str(e)[:30]}{Colors.RESET}")
            if "Connection" in str(e) or "closed" in str(e).lower():
                consecutive_disconnects += 1
                if consecutive_disconnects >= MAX_RECONNECTS_DURING_FETCH:
                    logmsg(f"[refetch_all] too many disconnects ({consecutive_disconnects}); aborting")
                    break
        # 3) إعادة تشغيل الـ stream للأصل (للأسعار اللحظية)
        try:
            asset.stream_task = asyncio.run_coroutine_threadsafe(realtime_stream(asset), ASYNC_LOOP)
        except Exception as e:
            logmsg(f"[refetch_all] failed to restart stream for {asset.symbol}: {e}")
        await asyncio.sleep(FETCH_ASSET_DELAY)
    # 4) سد الثغرات بعد الانتهاء من إعادة الجلب
    if CONNECTION_ALIVE and CLIENT is not None and CLIENT.api is not None:
        try:
            asyncio.run_coroutine_threadsafe(mt4_gap_filler(), ASYNC_LOOP)
        except Exception as e:
            logmsg(f"[refetch_all] failed to schedule gap filler: {e}")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}")
    print(f"{Colors.GREEN}  Full re-fetch complete: {total_loaded} candles across {total_assets} assets{Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}\n")

# ==============================================================================
# SECTION 9: MT4 SYNC ENGINE (نموذج الكود المرجعي — ملف واحد لكل أصل)
# ==============================================================================
class MT4Writer:
    """محرّك مزامنة MT4 بنموذج الكود المرجعي.
    
    الكود المرجعي يستخدم:
      - sync_state[asset] يحوي {period, candles, last_write, last_price}
      - seed_history: يجلب الشموع الأولية + يكتب HST مرة واحدة
      - update_candle: يُحدّث الشمعة اللحظية + يكتب HST كل 200ms
      - fill_gap_once: يدمج 20 شمعة أخيرة + يكتب HST
    
    الفرق في هذا السكريبت:
      - استخدم derived_symbol (AUDJPY-OTC) بدلاً من api_symbol لاسم الملف
      - استخدم PERIOD=1 (M1) بدلاً من 60 (H1) => اسم الملف AUDJPY-OTC1.hst
      - makedirs + retry + silent errors (من FIX 4/8)
    """
    def __init__(self):
        appdata = os.environ.get('APPDATA', '') or os.environ.get('HOME', '')
        self.mt4_history_path = os.path.join(appdata, 'MetaQuotes', 'Terminal', 'Common', 'Files', 'qx_hst')
        try:
            os.makedirs(self.mt4_history_path, exist_ok=True)
        except Exception as e:
            logmsg(f"Cannot create MT4 folder: {e}")
        # ===== FIX 10: sync_state مُفهرس بـ derived_symbol (مثل AUDJPY-OTC) =====
        # هذا يضمن أن نفس المفتاح يُستخدم في seed_history + update_candle + fill_gap_once
        # => ملف واحد فقط لكل أصل (AUDJPY-OTC1.hst)
        self.sync_state: Dict[str, Any] = {}
        self._writing_queue = set()
        self._gap_filled = {}

    def get_digits(self, symbol: str, price: float = 0.0) -> int:
        s = symbol.upper()
        if 'JPY' in s: return 3
        if price > 0:
            if price < 0.5: return 6
            if price < 1: return 5
            if price < 5: return 5
            if price < 10: return 4
            if price < 50: return 4
            if price < 100: return 3
            return 2
        return 5

    def generate_hst_buffer(self, symbol: str, period: int, candles: list) -> bytes:
        header = bytearray(148)
        struct.pack_into('<I', header, 0, 400)
        struct.pack_into('64s', header, 4, b'MetaQuotes Software Corp.'.ljust(64, b'\x00'))
        struct.pack_into('12s', header, 68, symbol[:12].encode('ascii').ljust(12, b'\x00'))
        struct.pack_into('<I', header, 80, period)
        first_price = candles[0]['close'] if candles else 0.0
        digits = self.get_digits(symbol, first_price)
        struct.pack_into('<I', header, 84, digits)
        struct.pack_into('<I', header, 88, 0)
        struct.pack_into('<I', header, 92, 0)
        body_size = len(candles) * 44
        buffer = bytearray(148 + body_size)
        buffer[:148] = header
        offset = 148
        for c in candles:
            struct.pack_into('<I', buffer, offset, int(c['time']))
            struct.pack_into('<d', buffer, offset + 4, float(c['open']))
            struct.pack_into('<d', buffer, offset + 12, float(c['low']))
            struct.pack_into('<d', buffer, offset + 20, float(c['high']))
            struct.pack_into('<d', buffer, offset + 28, float(c['close']))
            struct.pack_into('<Q', buffer, offset + 36, int(c.get('volume', 0)))
            offset += 44
        return bytes(buffer)

    def update_candle(self, asset: str, period: int, tick: dict):
        """يُحدّث الشمعة اللحظية + يكتب HST كل 200ms (نموذج الكود المرجعي).

        Args:
            asset: derived_symbol (مثل "AUDJPY-OTC") — نفس اسم الملف
            period: MT4 timeframe (PERIOD=1 for M1) — يستخدم في اسم الملف فقط
            tick: {'time': int, 'price': float}
        """
        if asset not in self.sync_state:
            self.sync_state[asset] = {'period': period, 'candles': [], 'last_write': 0, 'last_price': 0.0}
        state = self.sync_state[asset]
        # ===== FIX C: إزالة tz_offset لجعل جميع الشموع على نفس أساس الوقت (UTC) =====
        # المشكلة السابقة: كنا نطبّق tz_offset على ticks الواردة، فتُنشئ شموع بـ SHIFTED time.
        # لكن fetch_candles_once تُنشئ الشموع التاريخية بـ RAW UTC (بدون shift).
        # نتيجة: state['candles'] بعد fill_gap_once يحوي شموع RAW (تاريخية) + شموع SHIFTED
        # (للدقائق الأخيرة). كل من RAW و SHIFTED لنفس الدقيقة الفعلية → مظهر "شمعدانتان في نفس الجسم".
        # الحل: نُلغي tz_offset تمامًا، فتُصبح جميع الشموع UTC متناسقة مع التاريخ.
        # MT4 HST يستخدم UTC كمعيار، فالعرض سيكون صحيحًا.
        aligned_time = (tick['time'] // PERIOD_SECONDS) * PERIOD_SECONDS

        if state['candles'] and state['candles'][-1]['time'] == aligned_time:
            last = state['candles'][-1]
            if tick['price'] == state['last_price']: return
            last['high'] = max(last['high'], tick['price'])
            last['low'] = min(last['low'], tick['price'])
            last['close'] = tick['price']
            last['volume'] += 1
        else:
            state['candles'].append({
                'time': aligned_time, 'open': tick['price'], 'high': tick['price'],
                'low': tick['price'], 'close': tick['price'], 'volume': 1,
            })
        if len(state['candles']) > 1000:
            state['candles'] = state['candles'][-1000:]
        state['last_price'] = tick['price']
        now = time.time()
        if now - state['last_write'] > 0.2:
            self.write_to_file(asset, period, state['candles'])
            state['last_write'] = now

    def write_to_file(self, asset: str, period: int, candles: list):
        """يكتب ملف HST باسم {asset}{period}.hst (مثل AUDJPY-OTC1.hst).
        
        Args:
            asset: derived_symbol (مثل "AUDJPY-OTC")
            period: MT4 timeframe (PERIOD=1 for M1)
        """
        if asset in self._writing_queue: return
        self._writing_queue.add(asset)
        file_name = f"{asset}{period}.hst"
        file_path = os.path.join(self.mt4_history_path, file_name)
        temp_path = file_path + '.tmp'
        # كشف جميع أخطاء القفل/الملف غير موجود + إخفاؤها
        def _is_silent_error(err_str):
            err_str = err_str.lower()
            return any(x in err_str for x in [
                'winerror 2', 'winerror 5', 'winerror 32', 'winerror 13',
                'introuvable', 'refusé', 'acces refusé', 'access denied',
                'permission', 'used by another', 'ebusy', 'eperm',
                'no such file', 'not found', 'does not exist'
            ])
        # تأكد من وجود المجلد قبل الكتابة (يحل WinError 2)
        try:
            os.makedirs(self.mt4_history_path, exist_ok=True)
        except Exception:
            pass
        try:
            buffer = self.generate_hst_buffer(asset, period, candles)
            with open(temp_path, 'wb') as f:
                f.write(buffer)
            # retry تدريجي على WinError 5 + 32
            replaced = False
            for attempt in range(8):
                try:
                    os.replace(temp_path, file_path)
                    replaced = True
                    break
                except (PermissionError, OSError) as e:
                    if _is_silent_error(str(e)):
                        time.sleep(0.05 + 0.05 * attempt)
                        continue
                    raise
            if not replaced:
                # fallback — كتابة مباشرة
                try:
                    with open(file_path, 'wb') as f:
                        f.write(buffer)
                    replaced = True
                except Exception as fallback_err:
                    if not _is_silent_error(str(fallback_err)):
                        logmsg(f"MT4 Write Error for {asset} (fallback): {fallback_err}")
        except OSError as e:
            if not _is_silent_error(str(e)):
                logmsg(f"MT4 Write Error for {asset}: {e}")
        except Exception as e:
            if not _is_silent_error(str(e)):
                logmsg(f"MT4 Write Error for {asset}: {e}")
        finally:
            self._writing_queue.discard(asset)
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except Exception: pass

    async def seed_history(self, client, asset_obj, period: int, days: float = 0.75):
        """يجلب الشموع الأولية + يكتب HST مرة واحدة (نموذج الكود المرجعي).
        
        Args:
            client: كائن Quotex
            asset_obj: كائن Asset (يحوي api_symbol و symbol)
            period: MT4 timeframe (PERIOD=1 for M1) — لكن get_candles يستخدم PERIOD_SECONDS
            days: عدد الأيام لجلبها (default 0.75 = 18 ساعة)
        
        Returns:
            True إذا نجح، False إذا فشل
        """
        api_symbol = asset_obj.api_symbol
        derived_symbol = asset_obj.symbol
        try:
            offset_seconds = int(days * 86400)
            # ===== FIX 10: get_candles يستخدم PERIOD_SECONDS (60s لكل شمعة) =====
            # لكن اسم الملف يستخدم PERIOD (1 = M1 timeframe)
            candles = await client.get_candles(api_symbol, time.time(), offset_seconds, PERIOD_SECONDS)
            if candles and len(candles) > 0:
                # ===== FIX C: إزالة tz_offset — يُرجع get_candles شموع RAW UTC متناسقة =====
                # مع الشموع التاريخية الموجودة في asset.candles (التي أُنشئت من fetch_candles_once
                # بدون shift). تطبيق tz_offset كان يُنشئ شموع-shifted مختلفة عن نظيرتها RAW.
                formatted = []
                for c in candles:
                    t = int(c.get('time', c.get('timestamp', 0)))
                    o = float(c.get('open', c.get('o', 0)) or 0)
                    h = float(c.get('high', c.get('max', c.get('h', 0))) or 0)
                    l = float(c.get('low', c.get('min', c.get('l', 0))) or 0)
                    cl = float(c.get('close', c.get('c', 0)) or 0)
                    if o > 0 and h > 0 and l > 0 and cl > 0:
                        formatted.append({
                            'time': t, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': 0,
                        })
                formatted.sort(key=lambda x: x['time'])
                seen = set()
                unique_candles = [c for c in formatted if not (c['time'] in seen or seen.add(c['time']))]
                # ===== FIX 10: حد 1000 شمعة + إزالة التكرار =====
                unique_candles = unique_candles[-INITIAL_CANDLES:]
                # ===== FIX 10: sync_state مفهرس بـ derived_symbol (مثل AUDJPY-OTC) =====
                self.sync_state[derived_symbol] = {
                    'period': period, 'candles': unique_candles, 'last_write': 0, 'last_price': 0.0,
                }
                # ===== FIX 10: كتابة HST باسم derived_symbol + period (AUDJPY-OTC1.hst) =====
                self.write_to_file(derived_symbol, period, unique_candles)
                # تحديث asset_obj.candles (لعرض السعر اللحظي)
                asset_obj.candles = unique_candles
                if unique_candles:
                    asset_obj.price = unique_candles[-1]['close']
                self._gap_filled[derived_symbol] = False
                return True
            return False
        except Exception as e:
            # إخفاء أخطاء القفل (لا spam)
            err_str = str(e).lower()
            if not any(x in err_str for x in ['winerror', 'permission', 'access', 'closed', 'connection']):
                pass  # لا نسجل — main fetch loop سيُسجل الفشل
            return False

    async def fill_gap_once(self, client, asset_obj, period: int):
        """يسد الثغرات بـ GAP_FILL_CANDLES شمعة أخيرة (نموذج الكود المرجعي).
        
        Args:
            client: كائن Quotex
            asset_obj: كائن Asset (يحوي api_symbol و symbol)
            period: MT4 timeframe (PERIOD=1 for M1)
        """
        api_symbol = asset_obj.api_symbol
        derived_symbol = asset_obj.symbol

        # 1) skip if already filled
        if derived_symbol in self._gap_filled and self._gap_filled[derived_symbol]:
            return

        # 2) تهيئة sync_state من asset_obj.candles إذا لم يكن مهيأ
        if derived_symbol not in self.sync_state:
            if not asset_obj.candles:
                return
            self.sync_state[derived_symbol] = {
                'period': period,
                'candles': list(asset_obj.candles),
                'last_write': 0,
                'last_price': float(asset_obj.candles[-1]['close']) if asset_obj.candles else 0.0,
            }
        state = self.sync_state[derived_symbol]
        if not state['candles']:
            return

        try:
            # ===== FIX 5: 20 شمعة بدلاً من 5 =====
            # get_candles يستخدم PERIOD_SECONDS (60s) لكن اسم الملف يستخدم PERIOD (1)
            small_days = (GAP_FILL_CANDLES * PERIOD_SECONDS) / 86400.0
            candles = await client.get_candles(api_symbol, time.time(), int(small_days * 86400), PERIOD_SECONDS)
            if not candles:
                return

            # ===== FIX C: إزالة tz_offset — get_candles يُرجع شموع RAW UTC متناسقة مع =====
            # الشموع التاريخية الموجودة في state['candles'] (التي أُنشئت من asset.candles
            # بدون shift). تطبيق tz_offset كان يُنشئ شموع-shifted تختلف بـ 1h عن نظيرتها
            # RAW لنفس الدقيقة الفعلية، فيظهر في MT4 كانها "شمعدانتان في نفس الجسم".
            # الحل: نُلغي tz_offset تماماً، فتُصبح جميع الشموع UTC متناسقة.

            # بناء candle_map من الحالي + الجديد (إزالة التكرار بالوقت)
            candle_map = {c['time']: c for c in state['candles']}
            for c in candles:
                t = int(c.get('time', c.get('timestamp', 0)))
                # تطبيع الحقول
                o = float(c.get('open', c.get('o', 0)) or 0)
                h = float(c.get('high', c.get('max', c.get('h', 0))) or 0)
                l = float(c.get('low', c.get('min', c.get('l', 0))) or 0)
                cl = float(c.get('close', c.get('c', 0)) or 0)
                v = int(c.get('volume', c.get('vol', 0)) or 0)
                if o > 0 and h > 0 and l > 0 and cl > 0:
                    candle_map[t] = {
                        'time': t, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': v,
                    }

            # ترتيب + حد 1000 شمعة
            merged = sorted(candle_map.values(), key=lambda x: x['time'])[-INITIAL_CANDLES:]
            state['candles'] = merged

            # ===== FIX 10: كتابة HST باسم derived_symbol + period (AUDJPY-OTC1.hst) =====
            # نفس اسم ملف seed_history — لا تكرار
            self.write_to_file(derived_symbol, period, merged)

            # تحديث asset_obj.candles (لعرض السعر اللحظي)
            asset_obj.candles = merged
            if merged:
                asset_obj.price = merged[-1]['close']

            # لا نسجل رسائل GAP FILL المفردة (إخفاء الـ spam)
            self._gap_filled[derived_symbol] = True
        except Exception as e:
            # إخفاء أخطاء القفل (لا spam)
            err_str = str(e).lower()
            if not any(x in err_str for x in ['winerror', 'permission', 'access', 'closed', 'connection']):
                pass  # لا نسجل — mt4_gap_filler سيُسجل الفشل في الملخص

MT4_WRITER = MT4Writer()

async def mt4_gap_filler():
    # ===== FIX 8: جدول نهائي لسد الثغرات بدلاً من رسائل متدفقة =====
    # المستخدم يريد: قسم مستقل لسد الثغرات بملخص فقط (دون طباعة كل أصل)
    await asyncio.sleep(60)
    print(f"\n{Colors.CYAN}{'═'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  SECTION 3: GAP FILL (20 candles per asset){Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}")
    filled_count = 0
    skipped_count = 0
    failed_assets = []
    t0 = time.time()
    for asset in ALL_STREAMING_ASSETS:
        if not CLIENT or not CLIENT.api:
            print(f"  {Colors.RED}Connection lost during gap fill — aborting{Colors.RESET}")
            break
        try:
            # ===== FIX 10: استخدم PERIOD (1) + فحص derived_symbol (وليس api_symbol) =====
            await MT4_WRITER.fill_gap_once(CLIENT, asset, PERIOD)
            # fill_gap_once تُعلّم _gap_filled[derived_symbol] = True
            if MT4_WRITER._gap_filled.get(asset.symbol, False):
                filled_count += 1
            else:
                skipped_count += 1
            await asyncio.sleep(0.3)
        except Exception:
            skipped_count += 1
            failed_assets.append(asset.symbol)
    elapsed = time.time() - t0
    print(f"  {Colors.GREEN}Gap fill complete:{Colors.RESET}")
    print(f"     • Filled:   {filled_count}/{len(ALL_STREAMING_ASSETS)} assets")
    print(f"     • Skipped:  {skipped_count}/{len(ALL_STREAMING_ASSETS)} assets")
    print(f"     • Time:     {elapsed:.1f}s")
    if failed_assets:
        print(f"     {Colors.RED}• Failed:   {', '.join(failed_assets[:5])}{Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}\n")

def print_dashboard():
    print(f"{Colors.CYAN}{Colors.BOLD}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  QXChartMT4 Pro - Ultimate Edition v8.0{Colors.RESET}")
    print(f"{Colors.BOLD}  (Library-Native Never-Sleep & Smart Digits){Colors.RESET}")
    print(f"{Colors.BOLD}  Developed by: @qxzero1 (Telegram){Colors.RESET}")
    print(f"{Colors.BOLD}  Development Year: 2026{Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  History window: {HISTORY_DAYS} day ({FETCH_DURATION_SECONDS}s) — optimized fetch{Colors.RESET}")
    print(f"{Colors.YELLOW}  Target Candles: {INITIAL_CANDLES} per asset{Colors.RESET}")
    print(f"{Colors.GREEN}  Contact: https://t.me/qxzero1{Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}\n")

if __name__ == "__main__":
    print_dashboard()
    should_force = session_manager.should_force_fresh()
    saved_email = session_manager.get_saved_email()
    success = False
    if saved_email and not should_force:
        print(f"{Colors.GREEN}Found saved email: {saved_email}{Colors.RESET}")
        PASSWORD_INPUT = input(f"{Colors.YELLOW} Password: {Colors.RESET}").strip()
        fut = asyncio.run_coroutine_threadsafe(connect_quotex(saved_email, PASSWORD_INPUT, force_fresh=False, max_attempts=3), ASYNC_LOOP)
        success = fut.result(timeout=180)
    if not success:
        print()
        EMAIL_INPUT = input(f"{Colors.YELLOW}Email: {Colors.RESET}").strip()
        PASSWORD_INPUT = input(f"{Colors.YELLOW}Password: {Colors.RESET}").strip()
        fut = asyncio.run_coroutine_threadsafe(connect_quotex(EMAIL_INPUT, PASSWORD_INPUT, force_fresh=True, max_attempts=3), ASYNC_LOOP)
        success = fut.result(timeout=300)
    if not success:
        print(f"\n{Colors.RED}[FAILED] Could not connect after all attempts.{Colors.RESET}")
        sys.exit(1)
        
    # (FIX D) لا نطبع "Connected successfully!" — طباعة صامتة بعد نجاح الاتصال
    if WINAPI_AVAILABLE:
        time.sleep(1)
        find_mt4_window()

    # (FIX D) إنشاء مجلد HST بصمت — بدون طباعة المسار
    try:
        os.makedirs(MT4_HISTORY_PATH, exist_ok=True)
    except Exception:
        pass

    total_assets = len(ASSET_LIST)
    # ===== FIX 8: قسم 1 — جدول جلب الشموع =====
    print(f"\n{Colors.CYAN}{'═'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  SECTION 1: CANDLE FETCHING ({total_assets} assets, {INITIAL_CANDLES} candles each){Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*60}{Colors.RESET}\n")

    all_assets = []
    total_loaded = 0
    consecutive_disconnects = 0  # عداد الانقطاعات أثناء الجلب
    for idx, symbol in enumerate(ASSET_LIST, 1):
        # ===== FIX 3: فحص الاتصال قبل كل أصل =====
        # إذا كان الاتصال مُقطعاً، ننتظر auto_reconnect قبل المتابعة.
        # نُنفّذ الانتظار على ASYNC_LOOP عبر run_coroutine_threadsafe لأن
        # الـ main ليس async.
        if not CONNECTION_ALIVE or CLIENT is None or CLIENT.api is None:
            logmsg(f"[fetch_loop] connection dead before asset {idx}/{total_assets}; waiting for reconnect...")
            async def _wait_reconnect(timeout=30.0):
                try:
                    await wait_until(
                        lambda: CONNECTION_ALIVE and CLIENT is not None and CLIENT.api is not None,
                        timeout=timeout,
                        poll_interval=0.5,
                    )
                    return True
                except asyncio.TimeoutError:
                    return False
            reconnected = asyncio.run_coroutine_threadsafe(_wait_reconnect(30.0), ASYNC_LOOP).result(timeout=35)
            if reconnected:
                consecutive_disconnects = 0
            else:
                consecutive_disconnects += 1
                logmsg(f"[fetch_loop] reconnect failed within 30s (streak={consecutive_disconnects})")
                if consecutive_disconnects >= MAX_RECONNECTS_DURING_FETCH:
                    logmsg(f"[fetch_loop] giving up after {consecutive_disconnects} failed reconnects")
                    break
                continue
        asset = Asset(symbol)
        display = pretty_asset_name(symbol)
        all_assets.append(asset)
        ALL_STREAMING_ASSETS.append(asset)
        start_time = time.time()
        # ===== FIX 11: إعادة fetch_candles_with_retry (المنطق الأصلي) =====
        # المستخدم طلب: لا تُغيّر طريقة جلب الشموع — fetch_candles_with_retry يجلب 1000 شمعة بسرعة 4s
        # طريقة الإرسال إلى MT4 مُدارة عبر MT4_WRITER.update_candle في realtime_stream
        fut = asyncio.run_coroutine_threadsafe(fetch_candles_with_retry(asset, max_retries=MAX_FETCH_RETRIES, idx=idx, total=total_assets), ASYNC_LOOP)
        try:
            candles_count, attempts = fut.result(timeout=180)
            elapsed = time.time() - start_time
            if candles_count >= MIN_CANDLES_THRESHOLD:
                total_loaded += candles_count
                # ===== FIX 3: إعادة ضبط عداد الانقطاعات عند النجاح =====
                consecutive_disconnects = 0
                attempts_str = "" if attempts == 1 else f" ({attempts} attempts)"
                print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.GREEN}{candles_count} candles in {elapsed:.1f}s{attempts_str}{Colors.RESET} Streaming")
            else:
                print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.RED}Only {candles_count} candles{Colors.RESET} Streaming")
        except Exception as e:
            print(f"\r{Colors.CLEAR_LINE}  {Colors.CYAN}{display:<25}{Colors.RESET} {Colors.RED}Error: {str(e)[:30]}{Colors.RESET}")
            # ===== FIX 3: عدّ الانقطاعات أثناء الجلب =====
            if "Connection" in str(e) or "closed" in str(e).lower():
                consecutive_disconnects += 1
                if consecutive_disconnects >= MAX_RECONNECTS_DURING_FETCH:
                    logmsg(f"[fetch_loop] too many disconnects ({consecutive_disconnects}); aborting fetch")
                    break
        asset.stream_task = asyncio.run_coroutine_threadsafe(realtime_stream(asset), ASYNC_LOOP)
        # ===== FIX 7: لا cooldown — راحة قصيرة فقط بين الأصول =====
        # المستخدم لا يريد تباطؤ. keepalive_loop نشط بالتوازي يحمي الاتصال.
        if FETCH_COOLDOWN_EVERY > 0 and idx > 0 and idx % FETCH_COOLDOWN_EVERY == 0 and idx < total_assets:
            logmsg(f"[fetch_loop] cooldown {FETCH_COOLDOWN_DURATION}s after {idx}/{total_assets} assets")
            time.sleep(FETCH_COOLDOWN_DURATION)
        else:
            # راحة قصيرة فقط (0.1s — لا تباطؤ)
            time.sleep(FETCH_ASSET_DELAY)

    # سد الثغرات بعد الانتهاء من جلب جميع العملات (تماماً مثل الكود المرجعي)
    asyncio.run_coroutine_threadsafe(mt4_gap_filler(), ASYNC_LOOP)

    asyncio.run_coroutine_threadsafe(health_monitor(), ASYNC_LOOP)
    asyncio.run_coroutine_threadsafe(auto_reconnect(), ASYNC_LOOP)
    asyncio.run_coroutine_threadsafe(keepalive_loop(), ASYNC_LOOP)
    # ===== FIX: تشغيل الـ stale watchdog من الـ main =====
    asyncio.run_coroutine_threadsafe(stale_message_watchdog(), ASYNC_LOOP)
    
    # ===== FIX 8: dashboard محسّن — 3 أقسام منفصلة =====
    # قسم 1: جلب الشموع (موجود بالفعل أعلاه)
    # قسم 2: التحديث اللحظي (سيظهر في status line أدناه)
    # قسم 3: سد الثغرات (يظهر عبر mt4_gap_filler)
    print(f"\n{Colors.GREEN}{'═'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  All assets loaded and streaming!{Colors.RESET}")
    print(f"  Total: {total_loaded} candles for {len(all_assets)} assets")
    print(f"  History window: {HISTORY_DAYS} day (optimized, fast fetch)")
    print(f"  Writer Thread: ACTIVE (every {WRITE_INTERVAL}s)")
    print(f"  Refresh: BATCHED (every {REFRESH_INTERVAL}s)")
    print(f"  Stream Poll: {STREAM_POLL_INTERVAL}s")
    print(f"  Health Monitor: ACTIVE (Lenient: ignores websocket flickers)")
    print(f"  Keepalive Ping: ACTIVE (every {KEEPALIVE_PING_INTERVAL}s, multi-type)")
    print(f"  Stale Watchdog: ACTIVE (recycles if silent > {STALE_MESSAGE_TIMEOUT}s)")
    print(f"  Auto-Reconnect: instant detect + exponential backoff (never gives up)")
    print(f"  Internal Watchdog: ACTIVE (recycles stale connections > 90s)")
    print(f"  Fetch: {FETCH_MAX_WORKERS} workers, {FETCH_CHUNK_SIZE}c/batch, {FETCH_BATCH_DELAY}s delay, {FETCH_ASSET_DELAY}s between assets")
    print(f"  Retry: {MAX_FETCH_RETRIES} attempts, backoff {RETRY_BACKOFF_BASE}-{RETRY_BACKOFF_MAX}s")
    print(f"{Colors.GREEN}{'═'*60}{Colors.RESET}\n")

    # ===== FIX E: جدول سعر لحظي متعدد الأسطر — سطر واحد لكل أصل =====
    # المستخدم: لا يريد "Live: BRLUSD-OTC:0.19396 USDARS-OTC:1587.56 ..." على سطر واحد
    # بل يريد "سطر واحد لكل عملة مع السعر اللحظي بجانبها" مثل قائمة الجلب.
    # نستخدم ANSI cursor-up لإعادة رسم الجدول كل STATUS_REFRESH_INTERVAL.
    LIVE_TABLE_HEADER_LINES = 3  # ===, title, ===
    LIVE_TABLE_DATA_LINES = len(all_assets) + 1  # +1 لسطر حالة الاتصال
    LIVE_TABLE_TOTAL_LINES = LIVE_TABLE_HEADER_LINES + LIVE_TABLE_DATA_LINES

    def _draw_live_table(first_draw=False):
        # عدا أول رسم، نُحرّك المؤشر للأعلى ثم نُعيد رسم الجدول
        if not first_draw:
            sys.stdout.write(f"\033[{LIVE_TABLE_TOTAL_LINES}A")
        # رسم الترويسة
        sys.stdout.write(f"\033[2K{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        sys.stdout.write(f"\033[2K{Colors.BOLD}  LIVE PRICES{'':<55} {Colors.RESET}\n")
        sys.stdout.write(f"\033[2K{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        # رسم صفوف الأصول
        for asset in all_assets:
            display = pretty_asset_name(asset.api_symbol)
            if asset.price > 0:
                # اختيار عدد المنازل العشرية بناءً على نطاق السعر
                if asset.price >= 1000:
                    price_str = f"{asset.price:.3f}"
                elif asset.price >= 100:
                    price_str = f"{asset.price:.3f}"
                elif asset.price >= 1:
                    price_str = f"{asset.price:.5f}"
                else:
                    price_str = f"{asset.price:.5f}"
            else:
                price_str = "—"
            if asset.updates > 0:
                status_str = f"{Colors.GREEN}LIVE{Colors.RESET}"
            else:
                status_str = f"{Colors.RED}WAIT{Colors.RESET}"
            sys.stdout.write(f"\033[2K  {display:<25} {price_str:<15} {status_str}\n")
        # سطر حالة الاتصال
        if CONNECTION_ALIVE:
            conn_status = f"{Colors.GREEN}CONNECTED{Colors.RESET}"
        else:
            conn_status = f"{Colors.RED}RECONNECTING...{Colors.RESET}"
        sys.stdout.write(f"\033[2K  {'Connection':<25} {'':<15} {conn_status}\n")
        sys.stdout.flush()

    # الرسم الأولي للجدول (يفتح موضع المؤشر)
    _draw_live_table(first_draw=True)
    # سطر معلوماتي تحت الجدول (لن يُعاد رسمه)
    print()
    print(f"{Colors.YELLOW}Live streaming active... (Press Ctrl+C to stop){Colors.RESET}")
    print()

    # حلقة التحديث اللحظي للجدول
    while True:
        try:
            while True:
                # إعادة رسم الجدول (يستخدم cursor-up للكتابة فوق القديم)
                _draw_live_table(first_draw=False)
                time.sleep(STATUS_REFRESH_INTERVAL)
        except KeyboardInterrupt:
            # اطبع سطراً جديداً قبل رسالة الإيقاف حتى لا يُلصق بالجدول
            sys.stdout.write(f"\033[{LIVE_TABLE_TOTAL_LINES}B\n")
            sys.stdout.flush()
            print(f"{Colors.RED}Stopped{Colors.RESET}")
            print(f"{Colors.CYAN}Total updates: {sum(a.updates for a in all_assets):,}{Colors.RESET}")
            print(f"{Colors.CYAN}Total candles stored: {sum(len(a.candles) for a in all_assets):,}{Colors.RESET}\n")
            writer_thread.running = False
            break
        except Exception as e:
            # التقط أي استثناء آخر، سجله، وأكمل العمل
            log_exception("main status loop", e)
            try:
                print(f"\n{Colors.YELLOW}[main loop] recovered from error: {e}{Colors.RESET}", flush=True)
            except Exception:
                pass
            time.sleep(1)
            # تابع الدورة
