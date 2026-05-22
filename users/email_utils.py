import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


def _send_brevo(to_email, subject, html, text):
    api_key = getattr(settings, 'BREVO_API_KEY', '') or ''
    if not api_key:
        logger.error('[EMAIL] BREVO_API_KEY not set.')
        return False
    try:
        resp = requests.post(
            BREVO_API_URL,
            headers={
                'api-key': api_key,
                'Content-Type': 'application/json',
            },
            json={
                'sender':      {'name': 'UniGroups', 'email': settings.DEFAULT_FROM_EMAIL},
                'to':          [{'email': to_email}],
                'subject':     subject,
                'htmlContent': html,
                'textContent': text,
            },
            timeout=10,
        )
        if resp.status_code == 201:
            logger.info(f'[EMAIL] Sent to {to_email}')
            return True
        else:
            logger.error(f'[EMAIL] Brevo error {resp.status_code}: {resp.text}')
            return False
    except Exception as e:
        logger.error(f'[EMAIL] Request failed: {e}')
        return False


def send_verification_email(user, otp_code):
    subject = 'UniGroups — Email Verification Code'
    text = (
        f'Your verification code: {otp_code}\n'
        f'Roll Number: {user.roll_number}\n'
        f'Expires in 10 minutes.'
    )
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>body{{font-family:Arial,sans-serif;background:#f4f5f7;margin:0;padding:0}}
.wrap{{max-width:500px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)}}
.header{{background:linear-gradient(135deg,#6366f1,#4f46e5);padding:30px;text-align:center}}
.header h1{{color:#fff;margin:0;font-size:22px}}.header p{{color:rgba(255,255,255,0.8);margin:4px 0 0;font-size:12px}}
.body{{padding:32px}}.hi{{font-size:15px;color:#334155;margin-bottom:20px}}
.otp-box{{background:#f0f4ff;border:2px solid #c7d2fe;border-radius:14px;padding:24px;text-align:center;margin:20px 0}}
.lbl{{font-size:11px;color:#6b7280;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px}}
.code{{font-size:44px;font-weight:900;color:#4f46e5;letter-spacing:14px;font-family:monospace}}
.exp{{font-size:11px;color:#9ca3af;margin-top:8px}}
.roll{{background:#f8faff;border:1px solid #e0e7ff;border-radius:10px;padding:14px 18px;margin:16px 0}}
.roll-lbl{{font-size:10px;color:#6b7280;font-weight:700;text-transform:uppercase;letter-spacing:0.8px}}
.roll-num{{font-size:15px;font-weight:800;color:#1e293b;letter-spacing:1.5px;margin-top:2px;font-family:monospace}}
.note{{font-size:12px;color:#94a3b8;margin-top:20px;line-height:1.7}}
.footer{{background:#f8faff;padding:16px;text-align:center;border-top:1px solid #e2e8f0}}
.footer p{{font-size:11px;color:#94a3b8;margin:0}}</style></head>
<body><div class="wrap">
<div class="header"><h1>UniGroups</h1><p>Superior University · Group Management System</p></div>
<div class="body">
<p class="hi">Assalam o Alaikum <strong>{user.name}</strong>,</p>
<p style="color:#475569;font-size:14px;">Your email verification code:</p>
<div class="otp-box">
<div class="lbl">Verification Code</div>
<div class="code">{otp_code}</div>
<div class="exp">⏱ Expires in 10 minutes</div>
</div>
<div class="roll">
<div class="roll-lbl">Your Roll Number</div>
<div class="roll-num">{user.roll_number}</div>
</div>
<p class="note">Do not share this code with anyone.<br>If you did not register, ignore this email.</p>
</div>
<div class="footer"><p>Superior University · UniGroups</p></div>
</div></body></html>'''
    return _send_brevo(user.email, subject, html, text)


def send_welcome_email(user):
    dept = user.get_department_display() if user.department else 'Not set'
    subject = 'Welcome to UniGroups! 🎓'
    text = f'Marhaba {user.name}! Your UniGroups account is verified. Roll Number: {user.roll_number}'
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>body{{font-family:Arial,sans-serif;background:#f4f5f7;margin:0}}
.wrap{{max-width:500px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)}}
.header{{background:linear-gradient(135deg,#6366f1,#4f46e5);padding:30px;text-align:center}}
.header h1{{color:#fff;margin:0;font-size:22px}}.body{{padding:32px;text-align:center}}
.check{{font-size:48px;margin-bottom:12px}}.title{{font-size:20px;font-weight:800;color:#1e293b;margin-bottom:6px}}
.sub{{font-size:14px;color:#64748b;margin-bottom:20px}}
.info{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;text-align:left}}
.row{{display:flex;justify-content:space-between;padding:5px 0;font-size:13px}}
.lbl{{color:#6b7280}}.val{{font-weight:700;color:#1e293b}}
.footer{{background:#f8faff;padding:16px;text-align:center;border-top:1px solid #e2e8f0}}
.footer p{{font-size:11px;color:#94a3b8;margin:0}}</style></head>
<body><div class="wrap">
<div class="header"><h1>UniGroups ✓</h1></div>
<div class="body">
<div class="check">🎉</div>
<div class="title">Account Verified!</div>
<div class="sub">Marhaba {user.name}, your account is active!</div>
<div class="info">
<div class="row"><span class="lbl">Roll Number</span><span class="val" style="font-family:monospace">{user.roll_number}</span></div>
<div class="row"><span class="lbl">Name</span><span class="val">{user.name}</span></div>
<div class="row"><span class="lbl">Department</span><span class="val">{dept}</span></div>
<div class="row"><span class="lbl">Login with</span><span class="val">Roll Number + Password</span></div>
</div></div>
<div class="footer"><p>Superior University · UniGroups</p></div>
</div></body></html>'''
    _send_brevo(user.email, subject, html, text)
