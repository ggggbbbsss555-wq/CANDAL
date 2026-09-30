# CANDAL — Quotex Candle Fetcher

أداة لجلب الشموع التاريخية (Candles) من منصة **Quotex** وحفظها كملفات JSON.

## المميزات

- **جلب تفاعلي**: المستخدم يُدخل اسم العملة + عدد الأيام + الفريم الزمني.
- **حفظ آلي لبيانات الدخول**: الإيميل وكلمة المرور يُحفظان في `credentials.json` لإعادة الاستخدام.
- **حفظ JSON ذكي**: كل جلب يُحفظ في ملف باسم فريد `{asset}_{timeframe}m_{days}d_{random}.json` حتى لا يُكتب فوق الجلب السابق.
- **متوازي وسريع**: 5 workers بالتوازي لجلب البيانات بسرعة.
- **بدون MT4**: نسخة مبسّطة بدون الاعتماد على MetaTrader 4 أو كتابة ملفات `.hst`.
- **حلقة مستمرة**: بعد كل جلب ينتظر Enter للجلب التالي، أو الخروج.

## الاستخدام

```bash
python BOT.py
```

عند أول تشغيل:
1. أدخل Email + Password الخاص بـ Quotex.
2. سيتم حفظها تلقائياً في `credentials.json`.
3. في كل تشغيل لاحق، سيستخدم البرنامج البيانات المحفوظة (يمكنك رفضها).

في الحلقة التفاعلية:
1. أدخل اسم العملة (مثل `EURUSD` — يُضاف `_otc` تلقائياً).
2. أدخل عدد الأيام (مثل `7` أو `30` أو `100`).
3. أدخل الفريم بالدقائق (`1`, `5`, `15`, `30`, `60`).
4. سيتم جلب الشموع وحفظها في `candles_data/`.
5. اضغط Enter لجلب عملة أخرى، أو `exit` للخروج.

## صيغة الملفات

### ملف JSON للشموع
```json
{
  "metadata": {
    "asset": "EURUSD_otc",
    "timeframe_minutes": 1,
    "days_requested": 7,
    "candle_count": 10080,
    "fetch_time": "2026-09-29T12:34:56",
    "fetch_timestamp": 1234567890,
    "first_candle_time": 1234500000,
    "last_candle_time": 1234567890
  },
  "candles": [
    {"time": 1234567890, "open": 1.05, "high": 1.06, "low": 1.04, "close": 1.05, "volume": 100}
  ]
}
```

### اسم الملف
`{asset}_{timeframe}m_{days}d_{random8hex}.json`

مثال: `EURUSD_otc_5m_7d_9485d7af.json`

## المتطلبات

```bash
pip install certifi requests websocket-client beautifulsoup4 fake-useragent orjson
```

## الإعدادات القابلة للتعديل (داخل BOT.py)

| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|--------|
| `FETCH_MAX_WORKERS` | 5 | عدد العمال المتوازين للجلب |
| `FETCH_CHUNK_SIZE` | 200 | عدد الشموع لكل batch |
| `MAX_FETCH_RETRIES` | 5 | عدد محاولات إعادة الجلب |
| `KEEPALIVE_INTERVAL` | 5 | فترة الـ ping للحفاظ على الاتصال |

## هيكل المشروع

```
CANDAL/
├── BOT.py                  # الكود الرئيسي
├── README.md               # هذا الملف
├── credentials.json        # بيانات الدخول (تُحفظ تلقائياً)
├── session.json            # جلسة Quotex (تُحفظ تلقائياً)
├── candal.log              # ملف السجل
└── candles_data/           # مجلد حفظ الشموع
    ├── EURUSD_otc_5m_7d_9485d7af.json
    ├── GBPJPY_otc_15m_30d_a3f9b2c1.json
    └── ...
```
