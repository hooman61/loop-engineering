# راه‌اندازی محصول Loop Engineering

## هدف

این راهنما یک پروژهٔ محلی را به یک پروفایل بررسی فقط‌خواندنی متصل می‌کند.
پروفایل در خود پروژه نگهداری می‌شود، اما گزارش‌ها به‌طور پیش‌فرض بیرون از آن
قرار می‌گیرند.

## نصب

از ریشهٔ مخزن:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
```

برای ساخت بستهٔ قابل‌انتقال:

```powershell
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --wheel-dir dist
```

## اتصال یک پروژه

```powershell
loop-engineering init C:\path\to\project
```

خروجی در مسیر زیر ساخته می‌شود:

```text
C:\path\to\project\.loop-engineering\inspection.yaml
```

قبل از نخستین اجرا، فرمان‌های شناسایی‌شده را در پروفایل بازبینی کنید. تشخیص
خودکار محافظه‌کارانه است و فقط اسکریپت‌ها و فایل‌های متعارف اعلام‌شده را
استفاده می‌کند.

## بررسی آمادگی و اجرا

```powershell
loop-engineering doctor C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering run C:\path\to\project\.loop-engineering\inspection.yaml
```

کد خروجی صفر یعنی اجرای قابل‌اعتماد. کد یک فقط با گزینهٔ
`--fail-on-findings` برای یافته‌ها برگردانده می‌شود. کد دو یعنی پیکربندی،
ابزار یا تضمین فقط‌خواندنی قابل‌اعتماد نبوده است.

## مشاهدهٔ گزارش‌ها

```powershell
loop-engineering reports C:\path\to\project\.loop-engineering\inspection.yaml --open
```

در ویندوز، مسیر پیش‌فرض گزارش‌ها زیر این ریشه است:

```text
%LOCALAPPDATA%\loop-engineering\runs\<project-id>
```

در لینوکس و macOS از `XDG_STATE_HOME` یا مسیر استاندارد وضعیت کاربر استفاده
می‌شود.

## GitHub Actions

```powershell
loop-engineering github C:\path\to\project\.loop-engineering\inspection.yaml
```

گردش‌کار تولیدشده:

- دسترسی مخزن را فقط خواندنی نگه می‌دارد؛
- اکشن‌های شخص ثالث را با شناسهٔ کامل commit قفل می‌کند؛
- هر حسگر را در job مستقل اجرا می‌کند؛
- لاگ هر حسگر را به‌عنوان artifact نگه می‌دارد؛
- نتیجه‌ها را در یک گیت نهایی جمع می‌کند.

فایل تولیدشده را پیش از commit با نیازهای محیطی پروژه، مانند متغیرهای
غیرمحرمانه یا سرویس پایگاه‌دادهٔ تست، تطبیق دهید. هیچ راز یا اعتبارنامه‌ای
نباید در پروفایل یا گردش‌کار نوشته شود.

## بازنویسی صریح

فرمان‌های تولید فایل، فایل موجود را به‌طور پیش‌فرض حفظ می‌کنند. فقط پس از
بازبینی مقصد از گزینهٔ زیر استفاده کنید:

```powershell
--force
```
