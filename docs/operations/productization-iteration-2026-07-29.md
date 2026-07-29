# Iteration report

## Run metadata

```text
loop_id: reusable-loop-engineering-product
run_id: productization-20260729
definition_version_or_hash: architecture/reusable-product-cli.md
skill_version_or_hash: not-applicable
started_at: 2026-07-29T19:30:00+03:30
finished_at: 2026-07-29T20:12:00+03:30
status: accepted
```

## Selected target

- Target: تبدیل موتور مشاهده‌ای به محصول نصب‌پذیر و قابل‌حمل
- Sensor evidence: رابط قبلی فقط `validate` و `run` داشت و خروجی پیش‌فرض محلی بود
- Selection reason: استفاده روی پروژه‌های متفاوت بدون ویرایش دستی کد ممکن نبود
- Applicable limits: فقط‌خواندنی، بدون تغییر محصول، بدون deploy و بدون secret

## Change summary

یک رابط محصولی منسجم برای تشخیص پروژه، تولید پروفایل، بررسی آمادگی، اجرای
LangGraph، گزارش HTML، داشبورد و تولید GitHub Actions افزوده شد. تغییر در
منطق حسگرهای موجود ایجاد نشد و build خودکار به‌دلیل احتمال نوشتن فایل در
محصول فعال نشد.

## Files changed

| File | Reason | In allowed paths |
|---|---|---|
| `src/loop_engineering/cli.py` | رابط شش‌فرمانی محصول | yes |
| `src/loop_engineering/onboarding.py` | تشخیص و پروفایل قابل‌حمل | yes |
| `src/loop_engineering/health.py` | پیش‌بررسی محیط | yes |
| `src/loop_engineering/paths.py` | مسیر وضعیت کاربر | yes |
| `src/loop_engineering/github_actions.py` | مولد CI فقط‌خواندنی | yes |
| `src/loop_engineering/reporting.py` | HTML و داشبورد | yes |
| `src/loop_engineering/command_runner.py` | توکن Python قابل‌حمل | yes |
| `src/loop_engineering/config.py` | یافتن شِما پس از نصب | yes |
| `pyproject.toml` | نسخه، فرمان و بسته‌بندی شِما | yes |
| `tests/test_product_cli.py` | آزمون قابلیت‌های محصول | yes |
| `tests/test_engine.py` | الزام گزارش HTML | yes |
| `README.md` و اسناد محصول | راهنمای نصب و بهره‌برداری | yes |

## Before and after evidence

| Measure | Before | After | Expected direction |
|---|---:|---:|---|
| فرمان‌های عمومی | 2 | 6 | increase |
| قالب‌های گزارش هر اجرا | 3 | 4 | increase |
| آزمون‌های خودکار | 17 | 23 | increase |
| خطای `doctor` روی Sana | not available | 0 | decrease |
| اکشن‌های CI بدون SHA کامل | not measured | 0 of 12 | zero |

## Verification results

| Check or command | Result | Evidence location |
|---|---|---|
| `python -m unittest discover -s tests -t . -v` | 23 passed | terminal evidence |
| `python scripts/validate_loop.py --all` | 5 valid | terminal evidence |
| `python -m compileall -q src` | passed | terminal evidence |
| `loop-engineering doctor` روی کپی Sana | ready, 0 errors | terminal evidence |
| `loop-engineering run` با LangGraph | completed, reports written | `artifacts/product-smoke/` |
| parse گردش‌کار تولیدشده | 5 jobs, valid YAML | `artifacts/generated-quality-gates.yml` |
| سیاست اکشن‌ها | 12 of 12 pinned; no secrets | terminal evidence |
| ساخت wheel | passed | `dist/loop_engineering-0.2.0-py3-none-any.whl` |

## Risks and assumptions

- Risks: تشخیص خودکار همهٔ ساختارهای سفارشی monorepo را پوشش نمی‌دهد.
- Assumptions: پروژهٔ Python یا محیط مجازی نزدیک فرمان دارد یا وابستگی‌ها در
  مفسر جاری نصب شده‌اند.
- Items intentionally outside scope: اصلاح خودکار کد، merge، deploy،
  زمان‌بندی و دسترسی به پایگاه‌دادهٔ تولید.

## Stop-condition status

هیچ شرط توقفی فعال نشد. اجرای پذیرش Sana دو یافتهٔ واقعی/محیطی گزارش کرد، اما
مخزن هدف تغییر نکرد و موتور به‌صورت قابل‌اعتماد خاتمه یافت.

## Durable-feedback proposal

پیشنهاد: مولدهای پروفایل هرگز build نوشتنی را به‌طور خودکار فعال نکنند، مگر
اینکه مقصد خروجی ایزوله و خط‌مشی فقط‌خواندنی آن به‌طور قطعی اثبات شده باشد.

## Suggested next target

افزودن adapterهای اختیاری برای monorepo و سرویس‌های پایگاه‌دادهٔ تست پس از
جمع‌آوری نمونه‌های واقعی از پروژه‌های بعدی.
