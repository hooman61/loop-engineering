# Loop Engineering

[![PyPI](https://img.shields.io/pypi/v/loop-engineering.svg)](https://pypi.org/project/loop-engineering/)
[![Python](https://img.shields.io/pypi/pyversions/loop-engineering.svg)](https://pypi.org/project/loop-engineering/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

نصب نسخهٔ منتشرشده:

```powershell
python -m pip install loop-engineering
```

این مخزن چارچوب مهندسی لوپ‌های عامل‌محور و چندعاملی برای افزایش کیفیت محصولات ساخته‌شده با وایب‌کدینگ است.

هدف، تولید بیشترین حجم کد یا بیشترین تعداد اجرای عامل نیست. هدف، ساخت سامانه‌هایی است که تغییرات کوچک، قابل‌اندازه‌گیری، قابل‌بازبینی و قابل بازگردانی ایجاد کنند و مالکیت انسانی محصول را حفظ کنند.

## استفاده به‌عنوان محصول

نسخهٔ محصولی می‌تواند یک پروژهٔ دیگر را بدون انتقال کد آن پروژه و در حالت
فقط‌خواندنی بررسی کند. نصب توسعه‌ای در این مخزن:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

راه‌اندازی روی هر پروژهٔ محلی:

```powershell
loop-engineering init C:\path\to\project
loop-engineering doctor C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering run C:\path\to\project\.loop-engineering\inspection.yaml
loop-engineering reports C:\path\to\project\.loop-engineering\inspection.yaml --open
```

فرمان `init` فناوری‌های اعلام‌شدهٔ پروژه را بدون اجرای کد آن تشخیص می‌دهد و
پروفایلی قابل‌حمل با مسیر نسبی می‌سازد. فرمان `doctor` پیش‌نیازها را کنترل
می‌کند. فرمان `run` شواهد JSON، Markdown و HTML را بیرون از مخزن هدف در پوشهٔ
وضعیت کاربر ذخیره می‌کند. فرمان `reports` نمای فهرست اجراها را می‌سازد.

برای تولید گیت‌های مستقل GitHub Actions:

```powershell
loop-engineering github C:\path\to\project\.loop-engineering\inspection.yaml
```

فایل موجود بدون گزینهٔ صریح زیر بازنویسی نمی‌شود:

```powershell
--force
```

شرح معماری محصول:

[رابط خط فرمان قابل‌استفادهٔ مجدد](docs/architecture/reusable-product-cli.md)

راهنمای عملیاتی:

[راه‌اندازی محصول Loop Engineering](docs/operations/reusable-product-quickstart.md)

## از کجا شروع کنیم

برای آشنایی و طراحی یک لوپ جدید، اسناد را به این ترتیب بخوانید:

1. مبنای فکری استخراج‌شده از ویدیو:

   [مهندسی لوپ از اصول پایه](docs/foundations/loop-engineering-from-first-principles.md)

2. تصمیم معماری پذیرفته‌شده:

   [تصمیم ۰۰۰۱: معماری کنترل‌لوپ‌محور](docs/decisions/0001-control-loop-first.md)

3. اجزا و مرزهای معماری:

   [معماری مرجع لوپ‌های چندعاملی](docs/architecture/reference-loop-architecture.md)

4. قرارداد الزامی هر لوپ:

   [قرارداد تعریف و اجرای لوپ](docs/standards/loop-contract.md)

5. کنترل کیفیت، ریسک و توقف:

   [گیت‌های کیفیت و سیاست ریسک](docs/standards/quality-gates.md)

6. راه‌اندازی و بهره‌برداری:

   [چرخهٔ عمر عملیاتی لوپ](docs/operations/loop-lifecycle.md)

7. پیاده‌سازی مرحلهٔ اول مشاهدهٔ وب‌اپ:

   [معماری مشاهدهٔ فقط‌خواندنی](docs/architecture/stage-1-read-only-inspection.md)

8. مرجع ماژول‌های پایتون:

   [مرجع صفحهٔ کنترل پایتونی](docs/api/python-control-plane.md)

## ساختار مخزن

```text
.
├── AGENTS.md
├── README.md
├── config/
│   └── portfolio.yaml
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── decisions/
│   ├── foundations/
│   ├── operations/
│   └── standards/
├── loops/
│   ├── README.md
│   └── webapp-quality-observer/
├── pyproject.toml
├── requirements-dev.txt
├── schemas/
│   ├── inspection-profile.schema.json
│   ├── inspection-report.schema.json
│   ├── loop-definition.schema.json
│   └── portfolio.schema.json
├── scripts/
│   ├── run_inspection.py
│   └── validate_loop.py
├── src/
│   └── loop_engineering/
├── tests/
└── templates/
    └── loop/
        ├── feedback.md
        ├── golden-patterns.md
        ├── iteration-report.md
        ├── loop.yaml
        ├── runbook.md
        └── skill.md
```

هر لوپ واقعی در مسیر زیر قرار می‌گیرد:

```text
loops/<loop-id>/
```

## ساخت یک لوپ جدید

1. بستهٔ زیر را کپی کنید:

   `templates/loop/`

2. مقصد را با شناسهٔ یکتای لوپ بسازید:

   `loops/<loop-id>/`

3. فایل تعریف را تکمیل و با شِما اعتبارسنجی کنید:

   `schemas/loop-definition.schema.json`

   پس از آماده‌سازی وابستگی‌های توسعه، فرمان مرجع اعتبارسنجی چنین است:

   ```powershell
   python -m pip install -r requirements-dev.txt
   python scripts/validate_loop.py loops/<loop-id>/loop.yaml
   ```

   برای بررسی قالب پایه و همهٔ لوپ‌ها:

   ```powershell
   python scripts/validate_loop.py --all
   ```

4. حسگر و خط پایه را پیش از فعال‌کردن عامل اثبات کنید.
5. لوپ را ابتدا در حالت مشاهده‌ای اجرا کنید.
6. پس از تأیید خروجی‌های محدود، آن را به‌تدریج فعال کنید.

شرح کامل این فرایند در سند چرخهٔ عمر آمده است.

## ترتیب اعتبار اسناد

اگر میان اسناد تعارضی وجود داشت، این ترتیب حاکم است:

1. تصمیم‌های معماری پذیرفته‌شده؛
2. استانداردهای پروژه؛
3. تعریف نسخه‌بندی‌شدهٔ همان لوپ؛
4. ران‌بوک و مهارت همان لوپ؛
5. اسناد مبنا و یادداشت‌های منبع.

فایل بازخورد می‌تواند رفتار آیندهٔ یک لوپ را دقیق‌تر کند، اما حق نقض استانداردها، گیت‌های ریسک یا تصمیم‌های معماری را ندارد.

## اصول غیرقابل چشم‌پوشی

- ابزار قطعی بر عامل زبانی مقدم است.
- هر تکرار باید محدود و قابل‌اندازه‌گیری باشد.
- ارزیابی نباید فقط در اختیار عامل اعمال‌کنندهٔ تغییر باشد.
- خروجی بازبینی‌نشده نباید بدون حد انباشته شود.
- خودکارسازی با شواهد پایداری افزایش می‌یابد، نه با اعتماد اولیه.
- انسان برای ادغام تغییرات محصول، مالک نهایی باقی می‌ماند مگر اینکه یک تصمیم معماری دامنهٔ کم‌ریسک مشخصی را صریحاً مستثنا کند.

## وضعیت فعلی

این مخزن اکنون افزون بر بستهٔ پایه، موتور مشاهدهٔ فقط‌خواندنی و پروفایل اثبات‌شدهٔ
محصول Sana را دارد. بازرسی‌های Django، پایگاه‌داده، TypeScript، ساخت Vite و
یکپارچگی Django/React روی کپی آزمایشی اجرا شده‌اند. حسگر React Doctor نیز با
نسخهٔ دقیق، دامنهٔ منبع محدود و خروجی قطعی به بازرس فرانت‌اند متصل است.

لوپ `webapp-quality-observer` همچنان در وضعیت پیش‌نویس باقی می‌ماند، زیرا مالک
و تأییدکنندهٔ انسانی هنوز از مقادیر نمونه جایگزین نشده‌اند و هیچ عملگر اصلاح
خودکار یا زمان‌بندی فعال نشده است.

آزمون هسته بدون نصب وابستگی خارجی:

```powershell
python -m unittest discover -s tests -t . -v
```

پس از ساخت محیط مجازی و نصب وابستگی‌ها، پروفایل محصول را اعتبارسنجی و با موتور
اصلی اجرا کنید:

```powershell
python scripts/run_inspection.py validate config/inspection.local.yaml
python scripts/run_inspection.py run config/inspection.local.yaml --runtime langgraph
```
