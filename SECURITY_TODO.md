# Security Fixes TODO

## Fixed ✓

- [x] **Remove hardcoded fallback secret key** — `core/core/settings.py:26`
  Removed `default="fallback-secret-key"`. The env var is now required.

- [x] **Set DEBUG to False by default** — `core/core/settings.py:29`
  Changed `default=True` to `default=False`.

- [x] **Add object-level permissions to PatientProfileViewSet** — `core/accounts/api/v1/views.py`
  Now filters by `user=request.user`; admin users can see all.

- [x] **Restrict UserViewSet to admin-only** — `core/accounts/api/v1/views.py`
  Changed to `ReadOnlyModelViewSet` with `IsAdminUser` permission.

- [x] **Add ownership check to payment verification** — `core/payments/api/v1/views.py`
  Verified payment belongs to requesting user; rejects already-processed payments; generates secure `gateway_ref` with token.

- [x] **Add rate limiting to auth endpoints** — `core/website/views.py` and `core/website/admin_views.py`
  Login: 10 req/min/IP. Register: 5 req/min/IP. Admin login: 10 req/min/IP.

- [x] **Configure secure cookies and HSTS** — `core/core/settings.py`
  Added `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY`, `SESSION_COOKIE_HTTPONLY`, `SECURE_SSL_REDIRECT`. All toggle based on `DEBUG`.

- [x] **Use Django password validators for change-password flow** — `core/website/views.py`
  Replaced manual length check with `validate_password()`.

- [x] **Use Django password validators on registration** — `core/website/views.py`
  Added `validate_password()` call during user registration.

- [x] **Lock down CORS with explicit origins** — `core/core/settings.py`
  Added `CORS_ALLOWED_ORIGINS` parsed from env var with sensible defaults.

- [x] **Remove duplicate UserSerializer** — `core/accounts/api/v1/serializers.py`
  Removed duplicate class definition.

- [x] **Pin CDN version and add crossorigin attribute** — `core/website/templates/website/base.html` and `dashboard/doctor.html`
  Chart.js pinned to v4.4.7; both scripts use `crossorigin="anonymous"`.

## Remaining (requires manual review / real gateway integration)

- [ ] **Replace `googletrans` dependency** — `core/accounts/signals.py`
  Uses unofficial Google Translate API. Replace with official Cloud Translation or remove auto-translation.

- [ ] **Remove placeholder PII on registration** — `core/website/views.py`
  `national_id='0000000000'` and `birth_date='2000-01-01'` planted on profile creation. Require or allow null.

- [ ] **Implement real payment gateway signature verification** — `core/payments/api/v1/views.py`
  Mock gateway must be replaced with a real provider (Zibal/IDPay/Mellat) and verify HMAC signatures server-side.
