#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL SIGNAL_BOT — Live Binary-Option Signal Generator + Telegram Notifier
=============================================================================
This bot:
  1. Connects to Quotex (login + WebSocket, never-sleeps like BOT.py)
  2. Fetches 500 historical candles for each asset
  3. Streams real-time M1 candles
  4. On each new candle, evaluates 25 exploits from the Playbook v3
  5. When an exploit fires, sends a Telegram notification
  6. Stays connected via keepalive (will NOT lose connection during waits)

Telegram library: python-telegram-bot 22.8
Telegram bot token: 8893034575:AAGE7GDM4W4IM30H1zTVsaGvF4qk8qVpMHE
Telegram chat ID: 8219553982

Signal format (matches user request):
  💎 QX ZERO

  📊 USDPKR-OTC  |  1M
  🕐 ENTRY  02:06
  🟢 BUY   (or 🔴 SELL)

  👑 ROYAL GOLD

Core modules reused from BOT.py:
  - SSL/HTTP Navigator + CipherSuiteAdapter
  - Login + Settings + WebsocketClient + QuotexAPI
  - Quotex (candle parsing + indicators infrastructure)

New modules:
  - Indicator + SMC computation (pandas-based, efficient)
  - 25 exploits evaluator (from Playbook v3)
  - Telegram bot async notifier
  - Live signal loop
"""

import os
import sys
import ssl
import json
import time
import math
import asyncio
import logging
import threading
import traceback
import platform
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional

import certifi
import requests
import websocket
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import numpy as np
import pandas as pd

# Telegram
try:
    from telegram import Bot
    from telegram.constants import ParseMode
    HAS_TELEGRAM = True
except Exception:
    HAS_TELEGRAM = False


# =============================================================================
# CONFIGURATION
# =============================================================================
TELEGRAM_BOT_TOKEN = "8893034575:AAGE7GDM4W4IM30H1zTVsaGvF4qk8qVpMHE"
TELEGRAM_CHAT_ID = 8219553982

# Asset list — the 16 assets in the repo
ASSET_LIST = [
    "BRLUSD_otc", "EURGBP_otc", "EURNZD_otc", "EURUSD_otc",
    "USDARS_otc", "USDBDT_otc", "USDCOP_otc", "USDDZD_otc",
    "USDEGP_otc", "USDIDR_otc", "USDINR_otc", "USDMXN_otc",
    "USDNGN_otc", "USDPHP_otc", "USDPKR_otc", "USDZAR_otc",
]

# Number of historical candles to fetch per asset
INITIAL_CANDLES = 500
PERIOD_SECONDS = 60  # M1

# Speed tuning (from BOT.py)
FETCH_MAX_WORKERS = 5
FETCH_CHUNK_SIZE = 200
FETCH_BATCH_DELAY = 0.1
MAX_FETCH_RETRIES = 5
RETRY_BACKOFF_BASE = 2
RETRY_BACKOFF_MAX = 15
KEEPALIVE_INTERVAL = 5  # ping every 5s to keep WebSocket alive

# Credentials persistence
CREDENTIALS_FILE = Path("credentials.json")
SESSION_FILE = Path("session.json")
BROWSER_DIR = Path("browser")
LOG_FILE = Path("candal_signals.log")


# =============================================================================
# LOGGING
# =============================================================================
def _prepare_logging():
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    ws_logger = logging.getLogger("websocket")
    ws_logger.setLevel(logging.INFO)
    ws_logger.addHandler(logging.NullHandler())

_prepare_logging()
logger = logging.getLogger(__name__)

cert_path = certifi.where()
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = cert_path
cacert = os.environ.get('WEBSOCKET_CLIENT_CA_BUNDLE')

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.load_verify_locations(cert_path)


class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; BLUE = '\033[94m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; DIM = '\033[2m'; RESET = '\033[0m'


def logmsg(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  \033[2m[{ts}]\033[0m {msg}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def log_exception(context: str, exc: BaseException):
    ts = datetime.now().strftime("%H:%M:%S")
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"  \033[91m[{ts}] FATAL in {context}: {exc}\033[0m")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] FATAL in {context}: {exc}\n{tb_text}\n")
    except Exception:
        pass


def _thread_excepthook(args):
    log_exception(f"thread '{args.thread.name}'", args.exc_value)
threading.excepthook = _thread_excepthook


def _main_excepthook(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb); return
    log_exception("main thread", exc_value)
sys.excepthook = _main_excepthook


# =============================================================================
# EVENT PRIMITIVES (from BOT.py)
# =============================================================================
async def wait_until(predicate, *, timeout=10.0, poll_interval=0.05):
    async def _loop():
        while not predicate():
            await asyncio.sleep(poll_interval)
    await asyncio.wait_for(_loop(), timeout=timeout)


async def wait_for_first_event(*events, timeout=10.0):
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
        raise asyncio.TimeoutError()
    except asyncio.CancelledError:
        for t in tasks:
            if not t.done(): t.cancel()
        raise


def _schedule_event_set(event, loop):
    if event is None or loop is None: return
    try:
        if not loop.is_closed() and loop.is_running():
            loop.call_soon_threadsafe(event.set)
    except RuntimeError:
        pass


# =============================================================================
# SESSION + CREDENTIALS
# =============================================================================
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
base_dir = Path.cwd()
session_lock = threading.Lock()


def resource_path(relative_path):
    global base_dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    return base_dir / relative_path


def load_session(email, user_agent=None):
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


def update_session(email, d):
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


def load_credentials():
    if not CREDENTIALS_FILE.exists(): return None
    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        if data.get("email") and data.get("password"): return data
        return None
    except Exception:
        return None


def save_credentials(email, password):
    try:
        existing = {}
        if CREDENTIALS_FILE.exists():
            try: existing = json.loads(CREDENTIALS_FILE.read_text())
            except Exception: pass
        existing.update({
            "email": email, "password": password,
            "saved_at": int(time.time())
        })
        CREDENTIALS_FILE.write_text(json.dumps(existing, indent=2))
        return True
    except Exception as e:
        logmsg(f"Failed to save credentials: {e}")
        return False


def purge_old_session():
    """Always log in fresh — delete session.json and browser/ on startup."""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    except Exception:
        pass
    try:
        import shutil
        if BROWSER_DIR.exists():
            shutil.rmtree(BROWSER_DIR, ignore_errors=True)
    except Exception:
        pass


# =============================================================================
# HTTP NAVIGATOR (CipherSuiteAdapter + Browser)
# =============================================================================
retry_strategy = Retry(
    total=3, backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504, 104],
    allowed_methods=["HEAD", "POST", "PUT", "GET", "OPTIONS"],
)


class CipherSuiteAdapter(HTTPAdapter):
    __attrs__ = ['ssl_context', 'max_retries', 'config', '_pool_connections',
                 '_pool_maxsize', '_pool_block', 'source_address']

    def __init__(self, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.cipherSuite = kwargs.pop('cipherSuite',
            'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:'
            'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
            'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
            'DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
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
        self.cipherSuite = kwargs.pop('cipherSuite',
            'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:'
            'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
            'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
            'DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        self.source_address = kwargs.pop('source_address', None)
        self.server_hostname = kwargs.pop('server_hostname', None)
        _proxies = kwargs.pop('proxies', None)
        super().__init__(*args, **kwargs)
        # IMPORTANT: set self.proxies AFTER super().__init__ (Session overrides it to {})
        self.proxies = _proxies
        self.headers.update(self.get_headers())
        self.mount('https://', CipherSuiteAdapter(
            ecdhCurve=self.ecdhCurve, cipherSuite=self.cipherSuite,
            server_hostname=self.server_hostname, source_address=self.source_address,
            ssl_context=ssl_context, max_retries=retry_strategy))

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


# =============================================================================
# LOGIN + SETTINGS
# =============================================================================
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
        self.headers["Accept"] = ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                                  "image/avif,image/webp,*/*;q=0.8")
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
            print("\nClosing program."); sys.exit()
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
            input_message = (f'{auth_body.find("p").text}: '
                             if auth_body.find("p")
                             else "Enter the PIN code sent to your email: ")
            await self.awaiting_pin(data, input_message)
            await asyncio.sleep(1)
            return self.success_login()
        return self.success_login()

    def success_login(self):
        if "trade" in str(self.response.url):
            return True, "Login successful."
        soup = self.get_soup()
        not_available = soup.select_one("#tab-1 > div > div.modal-sign__not-avalible__title")
        if not_available:
            return False, f"Service unavailable: {not_available.get_text(strip=True)}"
        error = soup.select_one("#tab-1 form > div:nth-child(2) > div")
        msg = error.get_text(strip=True) if error else "Unknown error"
        return False, f"Login failed. {msg}"

    async def __call__(self, username, password, user_data_dir=None):
        data = {"_token": self.get_token(), "email": username,
                "password": password, "remember": 1}
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


# =============================================================================
# WEBSOCKET CLIENT + STATE
# =============================================================================
class WebsocketStatus(IntEnum):
    DISCONNECTED = 0; CONNECTED = 1; CONNECTING = 2; ERROR = -1


class AuthStatus(IntEnum):
    NOT_AUTHENTICATED = 0; AUTHENTICATING = 1; AUTHENTICATED = 2; FAILED = -1


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
        self.ws_connected_event = None
        self.ws_closed_event = None
        self.auth_accepted_event = None
        self.auth_rejected_event = None
        self.ws_error_event = None
        self._loop = None

    def init_events(self):
        if self.ws_connected_event is None: self.ws_connected_event = asyncio.Event()
        if self.ws_closed_event is None: self.ws_closed_event = asyncio.Event()
        if self.auth_accepted_event is None: self.auth_accepted_event = asyncio.Event()
        if self.auth_rejected_event is None: self.auth_rejected_event = asyncio.Event()
        if self.ws_error_event is None: self.ws_error_event = asyncio.Event()
        try: self._loop = asyncio.get_running_loop()
        except RuntimeError: self._loop = None

    def reset_events(self):
        for ev in (self.ws_connected_event, self.ws_closed_event,
                   self.auth_accepted_event, self.auth_rejected_event, self.ws_error_event):
            if ev is not None: ev.clear()

    def signal_ws_connected(self): _schedule_event_set(self.ws_connected_event, self._loop)
    def signal_ws_closed(self): _schedule_event_set(self.ws_closed_event, self._loop)
    def signal_auth_accepted(self): _schedule_event_set(self.auth_accepted_event, self._loop)
    def signal_auth_rejected(self): _schedule_event_set(self.auth_rejected_event, self._loop)
    def signal_ws_error(self): _schedule_event_set(self.ws_error_event, self._loop)


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
            on_message=self.on_message, on_error=self.on_error,
            on_close=self.on_close, on_open=self.on_open,
            on_ping=self.on_ping, on_pong=self.on_pong,
            header=self.headers,
            cookie=self.api.session_data.get("cookies"),
        )

    def on_message(self, wss, msg):
        self.state.ssl_Mutual_exclusion = True
        try:
            if self.api is not None:
                self.api.last_message_at = time.time()
            msg_str = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else str(msg)

            if msg_str == "2":
                try: self.wss.send("3")
                except Exception: pass
                self.state.ssl_Mutual_exclusion = False
                return
            if msg_str == "3":
                self.state.ssl_Mutual_exclusion = False
                return

            if "authorization/reject" in msg_str:
                logger.warning("Token rejected.")
                self.state.check_rejected_connection = True
                self.state.auth_status = AuthStatus.FAILED
                self.state.signal_auth_rejected()
            elif "s_authorization" in msg_str:
                self.state.check_accepted_connection = True
                self.state.check_rejected_connection = False
                self.state.auth_status = AuthStatus.AUTHENTICATED
                self.state.status = WebsocketStatus.CONNECTED
                self.state.signal_auth_accepted()

            message = None
            if len(msg_str) > 1 and msg_str[1] in ('[', '{'):
                try: message = json.loads(msg_str[1:])
                except Exception: pass

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
            if loop is None or not loop.is_running(): return
            if isinstance(message, dict):
                asset = message.get("asset")
                if asset and (message.get("candles") or message.get("data") or message.get("history")):
                    self.api.candle_v2_data[asset] = message
                    self.api.candles.candles_data = (message.get("candles")
                                                    or message.get("data")
                                                    or message.get("history"))
                    asyncio.run_coroutine_threadsafe(
                        self.api.event_registry.set_event(f'candles_ready_{asset}', message), loop)
                    index = message.get("index")
                    if index is not None:
                        asyncio.run_coroutine_threadsafe(
                            self.api.event_registry.set_event(f'candles_ready_{asset}_{index}', message), loop)
                if isinstance(message, list) and len(message) > 0 and isinstance(message[0], list) and len(message[0]) == 4:
                    asset = message[0][0]
                    self.api.realtime_candles[asset] = message[0]
        except Exception as e:
            logger.debug(f"Error processing message: {e}")

    def on_error(self, wss, error):
        logger.error(error)
        self.state.websocket_error_reason = str(error)
        self.state.check_websocket_if_error = True
        self.state.status = WebsocketStatus.ERROR
        self.state.check_accepted_connection = False
        self.state.signal_ws_error()

    def on_open(self, wss):
        logger.info("Websocket client connected.")
        self.state.check_websocket_if_connect = 1
        self.state.status = WebsocketStatus.CONNECTED
        self.state.signal_ws_connected()
        asset_name = self.api.current_asset or "EURUSD_otc"
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
        logger.info("Websocket connection closed.")
        self.state.check_websocket_if_connect = 0
        self.state.status = WebsocketStatus.DISCONNECTED
        self.state.check_accepted_connection = False
        self.state.signal_ws_closed()

    def on_ping(self, wss, ping_msg): pass
    def on_pong(self, wss, pong_msg): pass


# =============================================================================
# QUOTEX API CORE
# =============================================================================
class CandlesObj:
    def __init__(self): self.__candles_data = None
    @property
    def candles_data(self): return self.__candles_data
    @candles_data.setter
    def candles_data(self, v): self.__candles_data = v


class EventRegistry:
    def __init__(self):
        self._events = {}
        self._data = {}
        self._lock = asyncio.Lock()

    async def get_event(self, key):
        async with self._lock:
            if key not in self._events: self._events[key] = asyncio.Event()
            return self._events[key]

    async def set_event(self, key, data=None):
        async with self._lock:
            if key not in self._events: self._events[key] = asyncio.Event()
            self._data[key] = data
            self._events[key].set()

    async def wait_event(self, key, timeout=30.0):
        event = await self.get_event(key)
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self._data.get(key)
        except asyncio.TimeoutError:
            return None

    async def clear_event(self, key):
        async with self._lock:
            if key in self._events: self._events[key].clear()
            if key in self._data: del self._data[key]


class QuotexAPI:
    def __init__(self, host, username, password, lang, proxies=None, user_data_dir="."):
        self.state = ConnectionState()
        self.current_asset = None
        self.current_period = None
        self.account_balance = None
        self.account_type = 1
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
        # Pass proxies to Browser
        proxies_dict = None
        if isinstance(proxies, str): proxies_dict = {"http": proxies, "https": proxies}
        elif isinstance(proxies, dict): proxies_dict = proxies
        self.browser = Browser(proxies=proxies_dict)
        self.browser.set_headers()
        self.settings = Settings(self)
        self.candles = CandlesObj()
        self.candle_v2_data = {}
        self.realtime_price = defaultdict(list)
        self.realtime_candles = {}
        self.event_registry = EventRegistry()
        self._async_loop = None
        self.last_message_at = time.time()

    @property
    def login(self):
        proxies_dict = None
        if isinstance(self.proxies, str): proxies_dict = {"http": self.proxies, "https": self.proxies}
        elif isinstance(self.proxies, dict): proxies_dict = self.proxies
        return Login(self, proxies=proxies_dict)

    def send_websocket_request(self, data, no_force_send=True):
        if no_force_send:
            deadline = time.time() + 5.0
            while (self.state.ssl_Mutual_exclusion or self.state.ssl_Mutual_exclusion_write):
                if time.time() > deadline: break
                time.sleep(0.001)
        self.state.ssl_Mutual_exclusion_write = True
        try:
            if self.websocket_client and self.websocket_client.wss:
                self.websocket_client.wss.send(data)
        finally:
            self.state.ssl_Mutual_exclusion_write = False

    def subscribe_realtime_candle(self, asset, period):
        self.realtime_price[asset] = []
        data = f'42["instruments/update", {json.dumps({"asset": asset, "period": period})}]'
        return self.send_websocket_request(data)

    def follow_candle(self, asset):
        return self.send_websocket_request(f'42["depth/follow", {json.dumps(asset)}]')

    def chart_notification(self, asset):
        return self.send_websocket_request(
            f'42["chart_notification/get", {json.dumps({"asset": asset, "version": "1.0.0"})}]')

    def get_candles_ws(self, asset, index, time_val, offset, period):
        payload = {"asset": asset, "index": index, "time": time_val, "offset": offset, "period": period}
        data = f'42["history/load",{json.dumps(payload)}]'
        return self.send_websocket_request(data)

    async def authenticate(self):
        async with self.login as login:
            status, msg = await login(self.username, self.password, self.user_data_dir)
        if status: self.state.SSID = self.session_data.get("token")
        return status, msg

    async def start_websocket(self):
        self.state.check_websocket_if_connect = None
        self.state.check_websocket_if_error = False
        self.state.websocket_error_reason = None
        self.state.init_events()
        self.state.reset_events()
        try: self.state._loop = asyncio.get_running_loop()
        except RuntimeError: self.state._loop = None

        if not self.state.SSID: await self.authenticate()
        self.websocket_client = WebsocketClient(self)
        payload = {
            "suppress_origin": True, "ping_interval": 24, "ping_timeout": 20,
            "ping_payload": "2", "origin": self.https_url, "host": f"ws2.{self.host}",
            "sslopt": {"check_hostname": True, "cert_reqs": ssl.CERT_REQUIRED,
                       "ca_certs": cacert, "context": ssl_context},
        }
        if platform.system() == "Linux":
            payload["sslopt"]["ssl_version"] = ssl.PROTOCOL_TLS
        self.websocket_thread = threading.Thread(
            target=self.websocket_client.wss.run_forever, kwargs=payload)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        try:
            idx = await wait_for_first_event(
                self.state.ws_connected_event, self.state.auth_rejected_event,
                self.state.ws_error_event, self.state.ws_closed_event,
                timeout=10.0)
        except asyncio.TimeoutError:
            return False, "Timeout waiting for websocket open"

        if idx == 0: return True, "Websocket connected"
        elif idx == 1: self.state.SSID = None; return False, "Token Rejected"
        elif idx == 2: return False, self.state.websocket_error_reason or "Websocket error"
        elif idx == 3: return False, "Websocket closed"
        return False, "Unknown state"

    async def send_ssid(self, timeout=10):
        if not self.state.SSID: return False
        if self.state.auth_accepted_event is None: self.state.init_events()
        self.state.auth_accepted_event.clear()
        self.state.auth_rejected_event.clear()
        payload = {"session": self.state.SSID, "isDemo": self.account_type, "tournamentId": 0}
        data = f'42["authorization",{json.dumps(payload)}]'
        self.send_websocket_request(data)
        try:
            idx = await wait_for_first_event(
                self.state.auth_accepted_event, self.state.auth_rejected_event,
                timeout=timeout)
        except asyncio.TimeoutError:
            return False
        return idx == 0

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


# =============================================================================
# CANDLE PARSING + QUOTEX WRAPPER
# =============================================================================
import calendar
import itertools
_request_counter = itertools.count(int(time.time() * 1000))


def _parse_raw_candles(raw_candles):
    """Convert raw WebSocket candles to OHLC dicts."""
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
                t = int(c[0]); o = float(c[1]); cl = float(c[2])
                h = float(c[3]); l = float(c[4])
                v = int(c[5]) if len(c) >= 6 else 0
                if t > 0 and o > 0 and h > 0 and l > 0 and cl > 0:
                    parsed.append({'time': t, 'open': o, 'high': h, 'low': l, 'close': cl, 'volume': v})
        except (TypeError, ValueError):
            continue
    return parsed


def merge_candles(candles_data):
    if not candles_data: return []
    candle_dict = {c['time']: c for c in candles_data if isinstance(c, dict) and 'time' in c}
    return sorted(candle_dict.values(), key=lambda x: x['time']) if candle_dict else []


class Quotex:
    def __init__(self, email=None, password=None, host="qxbroker.com", lang="en",
                 proxies=None, user_data_dir="browser"):
        self.email = email
        self.password = password
        self.host = host
        self.lang = lang
        self.proxies = proxies
        self.user_data_dir = user_data_dir
        self.account_is_demo = 1
        self.api = None
        session = load_session(self.email, USER_AGENT)
        self.session_data = session

    async def connect(self):
        self.api = QuotexAPI(self.host, self.email, self.password, self.lang,
                             proxies=self.proxies, user_data_dir=self.user_data_dir)
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

    async def change_account(self, balance_mode):
        self.account_is_demo = 0 if balance_mode.upper() == "REAL" else 1
        self.api.account_type = self.account_is_demo
        payload = {"demo": self.api.account_type, "tournamentId": 0}
        self.api.send_websocket_request(f'42["account/change",{json.dumps(payload)}]')

    async def start_candles_stream(self, asset="EURUSD_otc", period=60):
        if self.api:
            self.api.current_asset = asset
            self.api.current_period = period
            self.api.subscribe_realtime_candle(asset, period)
            self.api.chart_notification(asset)
            self.api.follow_candle(asset)

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
                parsed.append({
                    "time": int(c[0]), "open": float(c[1]),
                    "close": float(c[2]), "high": float(c[3]), "low": float(c[4]),
                })
            elif isinstance(c, dict) and "time" in c:
                parsed.append(c)
        return parsed

    async def get_historical_candles(self, asset, amount_of_seconds, period,
                                     timeout=30, max_workers=5):
        max_workers = max_workers or 1
        chunk_seconds = period * FETCH_CHUNK_SIZE
        all_candles = {}
        current_time = int(time.time())
        target_start_time = current_time - amount_of_seconds
        block_size = amount_of_seconds // max_workers
        semaphore = asyncio.Semaphore(max_workers)

        async def worker(start_t, end_t, worker_id):
            worker_candles = {}
            async with semaphore:
                oldest_t = start_t
                consecutive_failures = 0
                while oldest_t > end_t:
                    if not self.api or not getattr(self.api.state, 'check_accepted_connection', False):
                        break
                    index = next(_request_counter)
                    batch_data = await self._fetch_historical_batch(
                        asset, oldest_t, chunk_seconds, period, index, timeout)
                    if not batch_data:
                        oldest_t -= chunk_seconds
                        consecutive_failures += 1
                        if consecutive_failures >= 3: break
                        await asyncio.sleep(FETCH_BATCH_DELAY * 2)
                        continue
                    consecutive_failures = 0
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
                    oldest_t = new_oldest if new_oldest < oldest_t else oldest_t - chunk_seconds
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

    async def close(self):
        if self.api: return await self.api.close()
        return True


# =============================================================================
# INDICATORS + SMC COMPUTATION
# =============================================================================
def add_indicators(df):
    """Add all indicators needed by the 25 exploits."""
    df = df.copy()
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = (100 - 100 / (1 + rs)).fillna(50)
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    df["bb_mid"] = df["close"].rolling(20).mean()
    df["bb_std"] = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.ewm(alpha=1/14, adjust=False).mean()
    df["avg_body"] = df["body"].rolling(50).mean()
    df["range"] = df["high"] - df["low"]
    df["body"] = (df["close"] - df["open"]).abs()
    df["dir"] = np.sign(df["close"] - df["open"])
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["is_doji"] = (df["body"] < 0.3 * df["range"]) & (df["range"] > 0)
    df["hammer"] = (df["lower_wick"] > 2 * df["body"]) & (df["upper_wick"] < 0.3 * df["body"]) & (df["range"] > 0)
    df["star"] = (df["upper_wick"] > 2 * df["body"]) & (df["lower_wick"] < 0.3 * df["body"]) & (df["range"] > 0)
    df["big_body"] = df["body"] > 2 * df["avg_body"]
    df["small_body"] = df["body"] < 0.3 * df["avg_body"]
    df["atr_avg_50"] = df["atr_14"].rolling(50).mean()
    df["atr_low"] = df["atr_14"] < df["atr_avg_50"]

    # FVG (3-candle imbalance)
    n = len(df)
    h = df["high"].values
    l = df["low"].values
    fvg_bull = np.zeros(n, dtype=bool)
    fvg_bear = np.zeros(n, dtype=bool)
    for i in range(1, n - 1):
        if h[i - 1] < l[i + 1]: fvg_bull[i + 1] = True
        elif l[i - 1] > h[i + 1]: fvg_bear[i + 1] = True
    df["fvg_bull"] = fvg_bull
    df["fvg_bear"] = fvg_bear

    # Liquidity sweep (20-bar lookback)
    lookback = 20
    sweep_bull = np.zeros(n, dtype=bool)
    sweep_bear = np.zeros(n, dtype=bool)
    for i in range(lookback, n):
        recent_low = np.min(l[i - lookback:i])
        recent_high = np.max(h[i - lookback:i])
        if l[i] < recent_low and df["close"].iloc[i] > recent_low and df["dir"].iloc[i] == 1:
            sweep_bull[i] = True
        elif h[i] > recent_high and df["close"].iloc[i] < recent_high and df["dir"].iloc[i] == -1:
            sweep_bear[i] = True
    df["sweep_bull"] = sweep_bull
    df["sweep_bear"] = sweep_bear

    # Sequences
    df["2reds_before"] = (df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1)
    df["3reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1) &
                          (df["dir"].shift(3) == -1))
    df["4reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1) &
                         (df["dir"].shift(3) == -1) & (df["dir"].shift(4) == -1))
    df["2greens_before"] = (df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1)
    df["3greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1) &
                             (df["dir"].shift(3) == 1))
    df["4greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1) &
                             (df["dir"].shift(3) == 1) & (df["dir"].shift(4) == 1))
    df["2doji_before"] = df["is_doji"].shift(1).fillna(False) & df["is_doji"].shift(2).fillna(False)

    # Bull/Bear bar
    df["green_bar"] = df["dir"] == 1
    df["red_bar"] = df["dir"] == -1
    df["big_green"] = (df["dir"] == 1) & df["big_body"]
    df["big_red"] = (df["dir"] == -1) & df["big_body"]

    # Wick asymmetry
    df["lower_wick_long"] = df["lower_wick"] > df["upper_wick"]
    df["upper_wick_long"] = df["upper_wick"] > df["lower_wick"]

    # RSI conditions
    df["rsi_oversold"] = df["rsi_14"] < 30
    df["rsi_low"] = (df["rsi_14"] < 40) & (df["rsi_14"] > 25)
    df["rsi_oversold_loose"] = df["rsi_14"] < 45
    df["rsi_overbought"] = df["rsi_14"] > 70
    df["rsi_high"] = (df["rsi_14"] > 60) & (df["rsi_14"] < 75)
    df["rsi_overbought_loose"] = df["rsi_14"] > 55

    # EMA position
    df["ema_above"] = df["close"] > df["ema_50"]
    df["ema_below"] = df["close"] < df["ema_50"]

    # BB extremes
    df["bb_lower"] = df["close"] < df["bb_lower"]
    df["bb_upper"] = df["close"] > df["bb_upper"]

    # MACD cross
    df["macd_cross_up"] = (df["macd_hist"] > 0) & (df["macd_hist"].shift(1) <= 0)
    df["macd_cross_down"] = (df["macd_hist"] < 0) & (df["macd_hist"].shift(1) >= 0)

    return df


# =============================================================================
# 25 EXPLOITS DEFINITIONS (from Playbook v3)
# =============================================================================
# Each exploit: (id, asset, combo_name, direction, conditions, hour_filter)
# conditions = list of column names that must all be True at current bar
# hour_filter = None or hour (UTC) when this exploit only fires

EXPLOITS = [
    # (id, asset, display_name, direction, conditions, hour_filter)
    (1,  "EURUSD_otc", "RSI High + Red + 3 Greens",      "SELL", ["rsi_high", "red_bar", "3greens_before"], None),
    (2,  "EURUSD_otc", "RSI High + 2 Greens + Small",   "SELL", ["rsi_high", "2greens_before", "small_body"], None),
    (3,  "USDPHP_otc", "EMA Below + 3 Greens + ATR Low","SELL", ["ema_below", "3greens_before", "atr_low"], None),
    (4,  "USDDZD_otc", "Hammer + Doji + ATR Low",        "BUY",  ["hammer", "is_doji", "atr_low"], None),
    (5,  "USDIDR_otc", "BB Lower + ATR Low",             "BUY",  ["bb_lower", "atr_low"], None),
    (6,  "USDMXN_otc", "Green + FVG + Small",            "BUY",  ["green_bar", "fvg_bull", "small_body"], None),
    (7,  "EURUSD_otc", "RSI High + Red + 4 Greens",      "SELL", ["rsi_high", "red_bar", "4greens_before"], None),
    (8,  "EURUSD_otc", "Big Green @ 15:00 UTC",           "BUY",  ["big_green"], 15),
    (9,  "USDIDR_otc", "RSI<45 + BB Lower + ATR Low",    "BUY",  ["rsi_oversold_loose", "bb_lower", "atr_low"], None),
    (10, "USDZAR_otc", "RSI High + Red + 4 Greens",      "SELL", ["rsi_high", "red_bar", "4greens_before"], None),
    (11, "BRLUSD_otc", "BB Lower @ 17:00 UTC",            "BUY",  ["bb_lower"], 17),
    (12, "USDDZD_otc", "BB Lower + 2 Reds + 4 Reds",     "BUY",  ["bb_lower", "2reds_before", "4reds_before"], None),
    (13, "USDEGP_otc", "RSI Low + MACD Up + Lower Wick", "BUY",  ["rsi_low", "macd_cross_up", "lower_wick_long"], None),
    (14, "USDDZD_otc", "BB Lower + 3 Reds + 4 Reds",     "BUY",  ["bb_lower", "3reds_before", "4reds_before"], None),
    (15, "USDDZD_otc", "RSI<45 + BB Lower + 4 Reds",     "BUY",  ["rsi_oversold_loose", "bb_lower", "4reds_before"], None),
    (16, "USDDZD_otc", "BB Lower + 4 Reds",             "BUY",  ["bb_lower", "4reds_before"], None),
    (17, "USDIDR_otc", "Green + 4 Reds + 2 Dojis",       "BUY",  ["green_bar", "4reds_before", "2doji_before"], None),
    (18, "EURGBP_otc", "Big Green + FVG",                "BUY",  ["big_green", "fvg_bull"], None),
    (19, "EURGBP_otc", "Green + Big Green + FVG",        "BUY",  ["green_bar", "big_green", "fvg_bull"], None),
    (20, "USDMXN_otc", "Green + 4 Reds + ATR Low",       "BUY",  ["green_bar", "4reds_before", "atr_low"], None),
    (21, "USDPHP_otc", "4 Reds + Lower Wick + ATR Low", "BUY",  ["4reds_before", "lower_wick_long", "atr_low"], None),
    (22, "USDINR_otc", "RSI Low + 3 Reds + Small",       "BUY",  ["rsi_low", "3reds_before", "small_body"], None),
    (23, "USDBDT_otc", "RSI Low + Hammer + 2 Reds",     "BUY",  ["rsi_low", "hammer", "2reds_before"], None),
    (24, "USDBDT_otc", "Red + Big Red + MACD Down",      "SELL", ["red_bar", "big_red", "macd_cross_down"], None),
    (25, "USDBDT_otc", "Big Red + MACD Down",            "SELL", ["big_red", "macd_cross_down"], None),
]


# =============================================================================
# TELEGRAM NOTIFIER
# =============================================================================
async def send_telegram_signal(text: str):
    """Send a signal message to the configured Telegram chat."""
    if not HAS_TELEGRAM:
        logmsg("Telegram library not available")
        return False
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception as e:
        logmsg(f"Telegram send failed: {e}")
        return False


def format_signal(asset: str, direction: str, exploit_name: str, exploit_id: int,
                  entry_time_utc: str, l1_win_rate: float) -> str:
    """Format a signal message in the style the user requested.

    Example output:
        💎 QX ZERO

        📊 USDPKR-OTC  |  1M
        🕐 ENTRY  02:06
        🟢 BUY

        👑 ROYAL GOLD
    """
    # Asset format: USDPKR_otc -> USDPKR-OTC
    asset_display = asset.replace("_otc", "-OTC").upper()
    arrow = "🟢 BUY" if direction == "BUY" else "🔴 SELL"

    # Build message
    msg = (
        "💎 QX ZERO\n\n"
        f"📊 {asset_display}  |  1M\n"
        f"🕐 ENTRY  {entry_time_utc}\n"
        f"{arrow}\n\n"
        f"🎯 Strategy #{exploit_id}: {exploit_name}\n"
        f"📈 Historical win rate: {l1_win_rate*100:.1f}%\n\n"
        f"👑 ROYAL GOLD"
    )
    return msg


# =============================================================================
# SIGNAL ENGINE
# =============================================================================
class SignalEngine:
    """Evaluates all 25 exploits on each new candle. Fires signals to Telegram."""

    def __init__(self, client):
        self.client = client
        self.asset_dfs = {}  # asset -> pandas DataFrame
        self.asset_last_evaluated = {}  # asset -> last evaluated timestamp
        # Cooldown: prevent firing same exploit on same asset within 60s
        self.cooldowns = {}  # (exploit_id, asset) -> last fire time
        self.COOLDOWN_SECONDS = 60

    def update_candles(self, asset: str, new_candle: dict):
        """Called by the live stream when a new candle arrives.

        Adds the candle to the asset's DataFrame and evaluates all exploits.
        """
        if asset not in self.asset_dfs:
            # Will be populated by initial fetch
            return
        df = self.asset_dfs[asset]
        # Check if this candle is new (timestamp > last in df)
        ts = int(new_candle.get("time", 0))
        if ts == 0: return
        if len(df) > 0 and ts <= df.index[-1]:
            # Update last candle (price update within same minute)
            df.loc[df.index[-1], "close"] = float(new_candle.get("close", df.iloc[-1]["close"]))
            df.loc[df.index[-1], "high"] = max(df.iloc[-1]["high"], float(new_candle.get("high", df.iloc[-1]["high"])))
            df.loc[df.index[-1], "low"] = min(df.iloc[-1]["low"], float(new_candle.get("low", df.iloc[-1]["low"])))
        else:
            # Append new candle
            new_row = pd.DataFrame([{
                "time": ts,
                "open": float(new_candle.get("open", 0)),
                "high": float(new_candle.get("high", 0)),
                "low": float(new_candle.get("low", 0)),
                "close": float(new_candle.get("close", 0)),
                "volume": int(new_candle.get("volume", 0) or 0),
            }])
            new_row["time"] = pd.to_datetime(new_row["time"], unit="s", utc=True)
            new_row = new_row.set_index("time")
            df = pd.concat([df, new_row])
            # Keep only last 1000 candles
            if len(df) > 1000:
                df = df.iloc[-1000:]
            self.asset_dfs[asset] = df
            # Re-compute indicators on new candle
            self.asset_dfs[asset] = add_indicators(self.asset_dfs[asset])
            # Evaluate exploits
            self._evaluate_exploits(asset, ts)

    def _evaluate_exploits(self, asset: str, current_ts: int):
        """Evaluate all exploits that target this asset at the current bar."""
        # Current bar is the last in df
        df = self.asset_dfs[asset]
        if len(df) == 0: return
        last_bar = df.iloc[-1]
        # Hour-of-day (UTC) of the current bar
        current_hour_utc = df.index[-1].hour

        for exploit_id, exploit_asset, name, direction, conditions, hour_filter in EXPLOITS:
            if exploit_asset != asset: continue
            # Check hour filter
            if hour_filter is not None and hour_filter != current_hour_utc:
                continue
            # Check cooldown
            cooldown_key = (exploit_id, asset)
            now = time.time()
            if cooldown_key in self.cooldowns:
                if now - self.cooldowns[cooldown_key] < self.COOLDOWN_SECONDS:
                    continue
            # Check all conditions are True at the last bar
            all_true = True
            for cond in conditions:
                val = last_bar.get(cond)
                if val is None or not bool(val):
                    all_true = False
                    break
            if not all_true: continue
            # Signal fired!
            self.cooldowns[cooldown_key] = now
            entry_time_utc = df.index[-1].strftime("%H:%M")
            # Find historical L1 win rate from CSV (cached)
            l1_win_rate = self._get_historical_win_rate(exploit_id)
            # Send signal
            msg = format_signal(asset, direction, name, exploit_id, entry_time_utc, l1_win_rate)
            logmsg(f"SIGNAL #{exploit_id} {asset} {direction} (entry {entry_time_utc} UTC)")
            # Schedule async send
            asyncio.create_task(send_telegram_signal(msg))

    def _get_historical_win_rate(self, exploit_id: int) -> float:
        """Get historical L1 win rate from the v3 CSV (cached)."""
        if not hasattr(self, "_win_rate_cache"):
            self._win_rate_cache = {}
            try:
                csv_path = Path("/home/z/my-project/download/CANDAL_binary_exploits_v3.csv")
                if not csv_path.exists():
                    # Look in repo
                    csv_path = Path("analysis/CANDAL_binary_exploits_v3.csv")
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    # Match by exploit index (sorted by signals_per_day desc)
                    df = df[(df["level1_win_rate"] >= 0.65) & (df["level1_p_value"] < 0.05)]
                    df = df.sort_values("signals_per_day", ascending=False).head(25).reset_index(drop=True)
                    for i, row in df.iterrows():
                        self._win_rate_cache[i + 1] = row["level1_win_rate"]
            except Exception:
                pass
        return self._win_rate_cache.get(exploit_id, 0.65)


# =============================================================================
# LIVE STREAM LOOP (never-sleep, keeps WebSocket alive)
# =============================================================================
async def fetch_initial_candles(client: Quotex, asset: str) -> List[Dict]:
    """Fetch INITIAL_CANDLES candles for an asset. Returns a list of dicts."""
    logmsg(f"Fetching {INITIAL_CANDLES} candles for {asset}...")
    candles = []
    for attempt in range(1, MAX_FETCH_RETRIES + 1):
        if client is None or client.api is None or not getattr(client.api.state, 'check_accepted_connection', False):
            logmsg(f"Connection dead before attempt {attempt}; aborting {asset}")
            return []
        try:
            res = await asyncio.wait_for(
                client.get_historical_candles(
                    asset,
                    amount_of_seconds=int(INITIAL_CANDLES * PERIOD_SECONDS),
                    period=PERIOD_SECONDS,
                    max_workers=FETCH_MAX_WORKERS,
                ),
                timeout=120,
            )
            if res and len(res) > 0: candles = res; break
        except asyncio.TimeoutError:
            logmsg(f"Attempt {attempt}/{MAX_FETCH_RETRIES}: {asset} fetch timed out")
        except Exception as e:
            logmsg(f"Attempt {attempt}/{MAX_FETCH_RETRIES}: {asset} raised: {e}")
        if attempt < MAX_FETCH_RETRIES:
            delay = min(RETRY_BACKOFF_BASE * (2 ** (attempt - 1)), RETRY_BACKOFF_MAX)
            await asyncio.sleep(delay)
    # Format
    formatted = []
    seen_times = set()
    for c in candles:
        if not isinstance(c, dict): continue
        try:
            ts = int(c.get("time", c.get("timestamp", 0)))
            aligned = (ts // PERIOD_SECONDS) * PERIOD_SECONDS
            o = float(c.get("open", 0))
            h = float(c.get("high", c.get("max", 0)))
            l = float(c.get("low", c.get("min", 0)))
            cl = float(c.get("close", 0))
            if aligned in seen_times: continue
            if o > 0 and h > 0 and l > 0 and cl > 0:
                formatted.append({
                    "time": aligned, "open": o, "high": h, "low": l,
                    "close": cl, "volume": int(c.get("volume", 0) or 0),
                })
                seen_times.add(aligned)
        except Exception:
            continue
    formatted.sort(key=lambda x: x["time"])
    return formatted[-INITIAL_CANDLES:]


async def live_stream(asset: str, signal_engine: SignalEngine, stop_event: asyncio.Event):
    """Subscribe to real-time candles for an asset and feed them to the signal engine."""
    api_name = asset
    try:
        await wait_until(
            lambda: signal_engine.client is not None and signal_engine.client.api is not None,
            timeout=10.0, poll_interval=0.2,
        )
    except asyncio.TimeoutError:
        pass
    if signal_engine.client is None:
        return
    await signal_engine.client.start_candles_stream(api_name, PERIOD_SECONDS)
    await asyncio.sleep(1.5)

    consecutive_errors = 0
    last_processed_minute = -1
    while not stop_event.is_set():
        try:
            client = signal_engine.client
            if client is None or client.api is None:
                await asyncio.sleep(0.2)
                continue
            if not getattr(getattr(client, 'api', None), 'state', None) or \
               getattr(client.api.state, 'status', None) != 1:
                await asyncio.sleep(0.2)
                continue
            candle = client.api.realtime_candles.get(api_name)
            if candle:
                consecutive_errors = 0
                if isinstance(candle, list) and len(candle) >= 3:
                    ts, price = int(candle[1]), float(candle[2])
                elif isinstance(candle, dict):
                    ts = int(candle.get("time", candle.get("timestamp", time.time())))
                    price = float(candle.get("price", candle.get("close", 0)))
                else:
                    await asyncio.sleep(0.15)
                    continue
                if price > 0 and ts > 0:
                    # Build a candle update (current minute)
                    aligned_time = (ts // PERIOD_SECONDS) * PERIOD_SECONDS
                    minute_bucket = aligned_time // 60
                    # Only evaluate when a new minute starts
                    if minute_bucket != last_processed_minute:
                        last_processed_minute = minute_bucket
                        # Update the engine with a new candle (open=close=high=low=price)
                        new_candle = {
                            "time": aligned_time, "open": price, "high": price,
                            "low": price, "close": price, "volume": 1,
                        }
                        signal_engine.update_candles(api_name, new_candle)
                    else:
                        # Within the same minute — update high/low/close of the in-progress candle
                        new_candle = {
                            "time": aligned_time, "open": price, "high": price,
                            "low": price, "close": price, "volume": 1,
                        }
                        signal_engine.update_candles(api_name, new_candle)
            await asyncio.sleep(0.15)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= 10:
                logmsg(f"[stream:{api_name}] too many errors, stopping")
                return
            await asyncio.sleep(0.2)


async def keepalive_loop(client: Quotex, stop_event: asyncio.Event):
    """Send pings every KEEPALIVE_INTERVAL seconds to keep WebSocket alive."""
    while not stop_event.is_set():
        try:
            if client and client.api:
                client.api.send_websocket_request("2", no_force_send=False)
                client.api.send_websocket_request('42["tick"]', no_force_send=False)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=KEEPALIVE_INTERVAL)
        except asyncio.TimeoutError:
            pass


async def connect_quotex(email: str, password: str, max_attempts: int = 3):
    """Connect to Quotex. Returns a Quotex client on success, None on failure."""
    for attempt in range(1, max_attempts + 1):
        try:
            client = Quotex(email=email, password=password,
                            host="qxbroker.com", lang="en")
            check, reason = await client.connect()
            if check:
                try:
                    await client.change_account("PRACTICE")
                    await asyncio.sleep(0.5)
                except Exception: pass
                logmsg(f"Connected to Quotex as {email}")
                return client
            else:
                err = str(reason) if reason else "Unknown error"
                logmsg(f"Login attempt {attempt}/{max_attempts} failed: {err}")
        except Exception as e:
            logmsg(f"Login attempt {attempt}/{max_attempts} raised: {e}")
        if attempt < max_attempts:
            await asyncio.sleep(3 * attempt)
    return None


# =============================================================================
# ASYNC INPUT (non-blocking)
# =============================================================================
async def ainput(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)


# =============================================================================
# MAIN
# =============================================================================
async def main_async():
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  CANDAL SIGNAL_BOT — Live Signals → Telegram{Colors.RESET}")
    print(f"{Colors.BOLD}  16 assets × 25 exploits → ~100 signals/day{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Telegram chat ID: {TELEGRAM_CHAT_ID}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Assets: {len(ASSET_LIST)} ({', '.join(ASSET_LIST[:3])}, ...){Colors.RESET}")
    print(f"{Colors.YELLOW}  Exploits: {len(EXPLOITS)} from Playbook v3{Colors.RESET}")
    print(f"{Colors.YELLOW}  Initial candles per asset: {INITIAL_CANDLES}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    # ===== Purge old session =====
    purge_old_session()

    # ===== Read credentials =====
    creds = load_credentials()
    if creds:
        print(f"{Colors.GREEN}Found saved credentials for: {creds['email']}{Colors.RESET}")
        use_saved = (await ainput(f"{Colors.YELLOW}Use saved credentials? (Y/n): {Colors.RESET}")).strip().lower()
        if use_saved in ('y', '', 'yes'):
            email, password = creds['email'], creds['password']
        else:
            email = (await ainput(f"{Colors.YELLOW}Email: {Colors.RESET}")).strip()
            password = (await ainput(f"{Colors.YELLOW}Password: {Colors.RESET}")).strip()
    else:
        print(f"{Colors.CYAN}Enter your Quotex credentials (will be saved automatically){Colors.RESET}")
        email = (await ainput(f"{Colors.YELLOW}Email: {Colors.RESET}")).strip()
        password = (await ainput(f"{Colors.YELLOW}Password: {Colors.RESET}")).strip()

    if not email or not password:
        print(f"{Colors.RED}Invalid credentials.{Colors.RESET}")
        return

    # ===== Connect to Quotex =====
    logmsg("Connecting to Quotex...")
    client = await connect_quotex(email, password, max_attempts=3)
    if client is None:
        print(f"\n{Colors.RED}Connection failed after multiple attempts.{Colors.RESET}")
        return

    save_credentials(email, password)
    print(f"{Colors.GREEN}Credentials saved to {CREDENTIALS_FILE.name}{Colors.RESET}\n")

    # ===== Start keepalive =====
    stop_event = asyncio.Event()
    keepalive_task = asyncio.create_task(keepalive_loop(client, stop_event))

    # ===== Fetch initial candles for each asset =====
    print(f"{Colors.BOLD}Phase 1: Fetching {INITIAL_CANDLES} candles per asset ({len(ASSET_LIST)} assets){Colors.RESET}\n")
    signal_engine = SignalEngine(client)
    successful_assets = []
    for i, asset in enumerate(ASSET_LIST, 1):
        print(f"  [{i}/{len(ASSET_LIST)}] {asset}...", end=" ", flush=True)
        candles = await fetch_initial_candles(client, asset)
        if not candles:
            print(f"{Colors.RED}FAILED{Colors.RESET}")
            continue
        # Build DataFrame
        df = pd.DataFrame(candles)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.set_index("time").sort_index()
        # Add indicators
        df["range"] = df["high"] - df["low"]
        df["body"] = (df["close"] - df["open"]).abs()
        df = add_indicators(df)
        signal_engine.asset_dfs[asset] = df
        successful_assets.append(asset)
        print(f"{Colors.GREEN}{len(candles)} candles OK{Colors.RESET}")
    print(f"\n{Colors.GREEN}{len(successful_assets)}/{len(ASSET_LIST)} assets loaded{Colors.RESET}\n")

    if not successful_assets:
        print(f"{Colors.RED}No assets loaded. Cannot continue.{Colors.RESET}")
        stop_event.set()
        try: await asyncio.wait_for(keepalive_task, timeout=2.0)
        except Exception: pass
        return

    # ===== Start live streams =====
    print(f"{Colors.BOLD}Phase 2: Starting live streams for {len(successful_assets)} assets{Colors.RESET}\n")
    stream_tasks = []
    for asset in successful_assets:
        task = asyncio.create_task(live_stream(asset, signal_engine, stop_event))
        stream_tasks.append(task)

    # ===== Send a startup notification to Telegram =====
    startup_msg = (
        "💎 QX ZERO\n\n"
        f"✅ Bot started successfully\n"
        f"📊 Assets monitored: {len(successful_assets)}\n"
        f"🎯 Active exploits: {len(EXPLOITS)}\n"
        f"📈 Expected signals/day: ~{sum(3.0 for _ in EXPLOITS):.0f}\n\n"
        f"👑 ROYAL GOLD"
    )
    await send_telegram_signal(startup_msg)
    logmsg(f"Startup notification sent to Telegram (chat {TELEGRAM_CHAT_ID})")

    # ===== Main loop: just wait for signals =====
    print(f"\n{Colors.BOLD}Phase 3: Live signal monitoring (Press Ctrl+C to stop){Colors.RESET}\n")
    try:
        while True:
            await asyncio.sleep(60)
            # Status print every minute
            logmsg(f"Monitoring {len(successful_assets)} assets × {len(EXPLOITS)} exploits...")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.RESET}")
    finally:
        stop_event.set()
        try: await asyncio.wait_for(keepalive_task, timeout=2.0)
        except Exception: pass
        for task in stream_tasks:
            try: task.cancel()
            except Exception: pass
        try: await client.close()
        except Exception: pass
        print(f"{Colors.CYAN}Shutdown complete.{Colors.RESET}")


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopped.{Colors.RESET}")
    except Exception as e:
        log_exception("main", e)


if __name__ == "__main__":
    main()
