# app.py
"""
MyAgent Booking - Ultimate Premium Edition (Merged)
- Glass UI
- Guest Mode / Login Mode
- Budget tracking + alerts
- PDF/ICS export
- Monitoring hooks
- Virtual payment
- NEW: Per-flight/per-hotel detail info + deep-link open (Booking / Google Flights)
- NEW: Hotel check_in/check_out required (auto-fill) + nights + total/per-night price display
- NEW: Login/Signup moved to LEFT SIDEBAR under Guest Mode (right side no longer shows login page)
"""
import os
import re
import json
import time
import uuid
import sqlite3
import datetime
from io import BytesIO
from typing import Tuple, Optional, Dict, List, Any

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---- Imports from your app modules (keep core logic unchanged) ----
try:
    from agent import TravelAgent
except ImportError:
    from agent import TravelAgent

from database import get_database
from email_service import get_email_service
from budget_and_scoring import (
    BudgetTracker, AttractionScorer, ConferenceDetector,
    suggest_budget_adjustments
)
from monitoring_agent import get_monitoring_agent
from payment_service import VirtualPaymentService

# ---- PDF deps ----
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB = True
except Exception:
    REPORTLAB = False

# =========================
# Presence / Online Counter
# =========================
PRESENCE_DB = os.environ.get("PRESENCE_DB", "/tmp/myagent_presence.db")

def _presence_conn():
    conn = sqlite3.connect(PRESENCE_DB, check_same_thread=False)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS presence (
        session_id TEXT PRIMARY KEY,
        last_seen INTEGER
    )
    """)
    conn.commit()
    return conn

def presence_heartbeat(ttl_seconds: int = 90) -> int:
    if "presence_session_id" not in st.session_state:
        st.session_state.presence_session_id = str(uuid.uuid4())

    now = int(time.time())
    sid = st.session_state.presence_session_id

    conn = _presence_conn()
    try:
        conn.execute(
            "INSERT INTO presence(session_id,last_seen) VALUES(?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET last_seen=excluded.last_seen",
            (sid, now)
        )
        conn.execute("DELETE FROM presence WHERE last_seen < ?", (now - ttl_seconds,))
        conn.commit()

        cur = conn.execute("SELECT COUNT(*) FROM presence WHERE last_seen >= ?", (now - ttl_seconds,))
        return int(cur.fetchone()[0])
    finally:
        conn.close()

# =========================
# Page config (MUST be early)
# =========================
st.set_page_config(
    page_title="MyAgent Booking Premium",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Super UI (glassy)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
* {font-family: 'Inter', sans-serif;}
.stApp {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}
h1,h2,h3,h4 {font-family: 'Poppins', sans-serif !important; font-weight: 700 !important;}
.hero-section {
  text-align: center;
  padding: 70px 20px;
  background: linear-gradient(135deg,rgba(255,255,255,0.12),rgba(255,255,255,0.06));
  border-radius: 32px;
  margin: 30px 0 20px 0;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.18);
}
.hero-title {
  font-size: 3.6em;
  font-weight: 800;
  background: linear-gradient(135deg,#fff,#f0f0f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 14px;
}
.glass-card {
  background: rgba(255,255,255,0.94);
  backdrop-filter: blur(20px);
  border-radius: 22px;
  padding: 26px;
  margin: 16px 0;
  box-shadow: 0 10px 34px rgba(31,38,135,0.16);
  border: 1px solid rgba(255,255,255,0.34);
  transition: all 0.35s ease;
}
.glass-card:hover {transform: translateY(-3px); box-shadow: 0 16px 44px rgba(31,38,135,0.24);}
.stButton>button {
  background: linear-gradient(135deg,#667eea,#764ba2);
  color: white;
  border: none;
  border-radius: 999px;
  padding: 14px 28px;
  font-weight: 650;
  box-shadow: 0 6px 22px rgba(102,126,234,0.42);
  transition: all 0.25s ease;
}
.stButton>button:hover {transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102,126,234,0.62);}
.stTabs [data-baseweb="tab-list"] {
  gap: 10px;
  background: rgba(255,255,255,0.95);
  border-radius: 999px;
  padding: 8px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab"] {border-radius: 999px; padding: 10px 22px; font-weight: 650;}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg,#667eea,#764ba2);
  color: white !important;
  box-shadow: 0 4px 14px rgba(102,126,234,0.42);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,rgba(255,255,255,0.96),rgba(255,255,255,0.985));
  backdrop-filter: blur(20px);
}
.user-card {
  background: linear-gradient(135deg,#667eea,#764ba2);
  color: white;
  border-radius: 22px;
  padding: 22px;
  text-align: center;
  box-shadow: 0 10px 34px rgba(102,126,234,0.32);
  margin-bottom: 16px;
}
.mini-chip {
  display:inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(102,126,234,0.12);
  border: 1px solid rgba(102,126,234,0.22);
  color: #2b2b2b;
  font-weight: 650;
  font-size: 0.86em;
}
.budget-tracker {
  background: linear-gradient(135deg,rgba(102,126,234,0.10),rgba(118,75,162,0.10));
  border-left: 4px solid #667eea;
  padding: 20px;
  border-radius: 16px;
  margin: 14px 0;
}
.budget-alert {border-left-color: #ffc107; background: linear-gradient(135deg,rgba(255,193,7,0.12),rgba(255,193,7,0.06));}
.budget-critical {border-left-color: #dc3545; background: linear-gradient(135deg,rgba(220,53,69,0.12),rgba(220,53,69,0.06));}
.progress-bar {background: rgba(255,255,255,0.22); height: 24px; border-radius: 14px; overflow: hidden; margin: 10px 0;}
.progress-fill {height: 100%; display:flex; align-items:center; justify-content:center; color: white; font-weight: 800; font-size: 0.9em;}
.attraction-score {
  display:inline-block;
  background: linear-gradient(90deg,#ffd700,#ffed4e);
  color:#000;
  padding: 4px 12px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.9em;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# i18n (EN / ZH / FR) - minimal
# =========================
LANG_OPTIONS = {"English": "en", "中文": "zh", "Français": "fr"}

I18N = {
    "en": {
        "nav_new_trip": "🏠 New Trip",
        "nav_trip_history": "📚 Trip History",
        "nav_dashboard": "📊 Dashboard",
        "nav_login": "🔐 Login / Sign Up",

        "sidebar_guest_title": "🌟 Guest Mode",
        "sidebar_guest_line1": "Use planning & export without login",
        "sidebar_guest_line2": "Login to save history / email / monitoring",

        "login_title": "## 🔐 Login to MyAgent Booking",
        "login_tab_login": "Login",
        "login_tab_signup": "Sign Up",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "full_name": "Full Name",
        "home_location": "Home Location",
        "btn_login": "Login",
        "btn_signup": "Create Account",
        "login_ok": "Login successful!",
        "login_bad": "Invalid credentials",
        "pwd_mismatch": "Passwords don't match",
        "pwd_short": "Password must be at least 8 characters",
        "signup_ok": "Account created! Please login.",
        "signup_fail": "Email already exists",

        "dashboard_title": "## 📊 Dashboard",
        "kpi_online": "🟢 Online Now",
        "kpi_mode": "👤 Mode",
        "kpi_trip": "🧾 Current Trip",
        "kpi_monitor": "🔔 Monitoring",
        "mode_guest": "Guest",
        "mode_logged_in": "Logged In",
        "ready": "Ready",
        "none": "—",
        "overview": "Live Overview",
        "trip_status_title": "Current trip status",
        "no_active_title": "No trip generated yet",
        "no_active_desc": "Go to New Trip to generate one; KPIs, budget alerts & key bookings will show here.",
        "budget_alert_title": "Budget & Alerts",
        "budget_near": "Budget is near limit",
        "budget_near_desc": "Consider choosing more cost-effective options in Flights/Hotels.",
        "health": "System Health",
        "pdf_ok": "PDF export: OK",
        "pdf_bad": "PDF export: ReportLab not available",
        "mon_ok": "Monitoring Agent: Loaded",
        "mon_bad": "Monitoring Agent: Not available",
        "healthy": "All core services ready",
        "history_quick": "Quick History",
        "no_history": "No trip history yet.",
        "history_fail": "Failed to load history:",

        "new_trip_title": "## ✈️ Plan Your Perfect Trip",
        "new_trip_desc": "Type one sentence to generate itinerary + budget alerts + attractions + PDF/ICS export.",
        "describe_trip": "Describe your trip",
        "placeholder": "Example: Plan a 7-day trip from NJ to LA from March 15-22, budget $3600. I love culture and food and photography.",
        "trip_budget": "Trip Budget ($)",
        "add_attractions_cb": "Add attraction recommendations",
        "enable_monitoring_cb": "Enable 24/7 flight monitoring",
        "allow_guest_cb": "Allow Guest Mode (no login)",
        "allow_guest_help": "If checked, guest can generate/export without login.",
        "btn_generate": "🚀 Generate Plan",
        "btn_demo": "🎭 Demo",
        "btn_clear": "🔄 Clear",
        "err_no_query": "Please describe your trip.",
        "warn_login_or_guest": "Please login, or enable Guest Mode.",
        "status_creating": "🚀 Creating your personalized itinerary...",
        "st_init_agent": "🔍 Initializing AI agent...",
        "st_conf_detected": "📅 Conference trip detected - will add schedule blocks",
        "st_generating": "🌐 Generating plan...",
        "st_parsing": "📝 Parsing output...",
        "err_parse": "Failed to parse itinerary JSON from agent output.",
        "st_add_attractions": "⭐ Adding attraction recommendations...",
        "done_ready": "✅ Your trip is ready!",
        "err_failed": "❌ Failed to generate plan",
        "tab_itinerary": "📅 Itinerary",
        "tab_flights_hotels": "✈️ Flights & Hotels",
        "tab_attractions": "🎯 Attractions",
        "tab_export": "📥 Export",
        "itinerary_title": "### 📅 Your Itinerary",
        "dest": "Destination",
        "depart": "Departure",
        "return": "Return",
        "trip_summary": "Trip Summary",
        "all_prices_usd": "All prices shown in USD ($)",
        "fh_title": "### ✈️ Flights & Hotels",
        "fh_none": "No flight/hotel items found.",
        "export_title": "### 📥 Export & Share",
        "dl_pdf": "📄 Download PDF",
        "dl_ics": "📅 Download Calendar (ICS)",
        "pdf_disabled": "ReportLab not available — PDF export disabled.",
        "email_itin": "📧 Email Itinerary",
        "sent_to": "✅ Sent to",
        "send_fail": "Failed to send email",
        "login_needed_email": "Login to enable one-click email & monitoring binding.",

        "trip_history_title": "## 📚 Your Trip History",
        "need_login_history": "Please login to view Trip History (Guest mode does not save history).",
        "no_trips": "No trips yet. Plan your first adventure!",
        "track_external": "Track External Flight",
        "add_monitoring": "Add to Monitoring",
        "now_monitoring": "Now monitoring",
    },
    "zh": {
        "nav_new_trip": "🏠 New Trip",
        "nav_trip_history": "📚 Trip History",
        "nav_dashboard": "📊 Dashboard",
        "nav_login": "🔐 Login / Sign Up",
        "sidebar_guest_title": "🌟 Guest Mode",
        "sidebar_guest_line1": "无需登录即可使用规划与导出",
        "sidebar_guest_line2": "登录后可保存历史/邮件/监控绑定",
        "login_title": "## 🔐 登录 MyAgent Booking",
        "login_tab_login": "登录",
        "login_tab_signup": "注册",
        "email": "邮箱",
        "password": "密码",
        "confirm_password": "确认密码",
        "full_name": "姓名",
        "home_location": "常驻城市",
        "btn_login": "登录",
        "btn_signup": "创建账户",
        "login_ok": "登录成功！",
        "login_bad": "账号或密码错误",
        "pwd_mismatch": "两次密码不一致",
        "pwd_short": "密码至少 8 位",
        "signup_ok": "注册成功！请登录。",
        "signup_fail": "邮箱已存在",
        "dashboard_title": "## 📊 Dashboard",
        "kpi_online": "🟢 Online Now",
        "kpi_mode": "👤 Mode",
        "kpi_trip": "🧾 Current Trip",
        "kpi_monitor": "🔔 Monitoring",
        "mode_guest": "Guest",
        "mode_logged_in": "Logged In",
        "ready": "Ready",
        "none": "—",
        "overview": "Live Overview",
        "trip_status_title": "当前行程状态",
        "no_active_title": "还没有生成行程",
        "no_active_desc": "去 New Trip 生成后，这里会显示 KPI、预算预警、监控状态与关键预订。",
        "budget_alert_title": "预算与预警",
        "budget_near": "预算接近上限",
        "budget_near_desc": "建议在 Flights/Hotels 里优先选择性价比更高的选项。",
        "health": "系统健康",
        "pdf_ok": "PDF 导出：OK",
        "pdf_bad": "PDF 导出：ReportLab 未安装/不可用",
        "mon_ok": "Monitoring Agent：Loaded",
        "mon_bad": "Monitoring Agent：Not available",
        "healthy": "All core services ready",
        "history_quick": "历史快捷",
        "no_history": "暂无历史行程。",
        "history_fail": "History 读取失败：",
        "new_trip_title": "## ✈️ Plan Your Perfect Trip",
        "new_trip_desc": "输入一句话，生成完整行程 + 预算警报 + 景点推荐 + PDF/ICS 导出。",
        "describe_trip": "描述你的旅行",
        "placeholder": "示例：从NJ到LA，3/15-3/22，预算$3600。喜欢文化、美食、摄影。",
        "trip_budget": "旅行预算 ($)",
        "add_attractions_cb": "添加景点推荐",
        "enable_monitoring_cb": "开启 24/7 航班监控",
        "allow_guest_cb": "允许 Guest Mode（无需登录）",
        "allow_guest_help": "勾选后，无需登录也可以生成/导出。",
        "btn_generate": "🚀 Generate Plan",
        "btn_demo": "🎭 Demo",
        "btn_clear": "🔄 Clear",
        "err_no_query": "请先描述你的旅行。",
        "warn_login_or_guest": "请先登录，或开启 Guest Mode。",
        "status_creating": "🚀 正在生成你的行程...",
        "st_init_agent": "🔍 初始化 AI agent...",
        "st_conf_detected": "📅 检测到会议行程 - 将添加日程块",
        "st_generating": "🌐 生成行程中...",
        "st_parsing": "📝 解析输出中...",
        "err_parse": "解析 itinerary JSON 失败。",
        "st_add_attractions": "⭐ 正在添加景点推荐...",
        "done_ready": "✅ 行程已生成！",
        "err_failed": "❌ 生成失败",
        "tab_itinerary": "📅 Itinerary",
        "tab_flights_hotels": "✈️ Flights & Hotels",
        "tab_attractions": "🎯 Attractions",
        "tab_export": "📥 Export",
        "itinerary_title": "### 📅 Your Itinerary",
        "dest": "目的地",
        "depart": "出发",
        "return": "返回",
        "trip_summary": "Trip Summary",
        "all_prices_usd": "All prices shown in USD ($)",
        "fh_title": "### ✈️ Flights & Hotels",
        "fh_none": "未找到航班/酒店条目。",
        "export_title": "### 📥 Export & Share",
        "dl_pdf": "📄 Download PDF",
        "dl_ics": "📅 Download Calendar (ICS)",
        "pdf_disabled": "ReportLab 不可用 — PDF 导出已禁用。",
        "email_itin": "📧 Email Itinerary",
        "sent_to": "✅ 已发送至",
        "send_fail": "邮件发送失败",
        "login_needed_email": "登录后可一键邮件发送/监控绑定。",
        "trip_history_title": "## 📚 Your Trip History",
        "need_login_history": "请登录后查看 Trip History（Guest Mode 不保存历史）。",
        "no_trips": "暂无行程，先去生成一个吧！",
        "track_external": "Track External Flight",
        "add_monitoring": "Add to Monitoring",
        "now_monitoring": "Now monitoring",
    },
    "fr": {
        "nav_new_trip": "🏠 Nouveau voyage",
        "nav_trip_history": "📚 Historique",
        "nav_dashboard": "📊 Tableau de bord",
        "nav_login": "🔐 Connexion / Inscription",
        "sidebar_guest_title": "🌟 Mode invité",
        "sidebar_guest_line1": "Planification & export sans connexion",
        "sidebar_guest_line2": "Connectez-vous pour l’historique / email / monitoring",
        "login_title": "## 🔐 Connexion à MyAgent Booking",
        "login_tab_login": "Connexion",
        "login_tab_signup": "Inscription",
        "email": "Email",
        "password": "Mot de passe",
        "confirm_password": "Confirmer le mot de passe",
        "full_name": "Nom complet",
        "home_location": "Ville",
        "btn_login": "Se connecter",
        "btn_signup": "Créer un compte",
        "login_ok": "Connexion réussie !",
        "login_bad": "Identifiants invalides",
        "pwd_mismatch": "Les mots de passe ne correspondent pas",
        "pwd_short": "Mot de passe : 8 caractères minimum",
        "signup_ok": "Compte créé ! Veuillez vous connecter.",
        "signup_fail": "Email déjà utilisé",
        "dashboard_title": "## 📊 Tableau de bord",
        "kpi_online": "🟢 En ligne",
        "kpi_mode": "👤 Mode",
        "kpi_trip": "🧾 Voyage actuel",
        "kpi_monitor": "🔔 Monitoring",
        "mode_guest": "Invité",
        "mode_logged_in": "Connecté",
        "ready": "Prêt",
        "none": "—",
        "overview": "Aperçu",
        "trip_status_title": "Statut du voyage",
        "no_active_title": "Aucun voyage",
        "no_active_desc": "Allez sur Nouveau voyage : KPIs, budget, monitoring et réservations apparaîtront ici.",
        "budget_alert_title": "Budget & alertes",
        "budget_near": "Budget proche de la limite",
        "budget_near_desc": "Choisissez des options plus rentables dans Vols/Hôtels.",
        "health": "Santé du système",
        "pdf_ok": "Export PDF : OK",
        "pdf_bad": "Export PDF : ReportLab indisponible",
        "mon_ok": "Monitoring Agent : chargé",
        "mon_bad": "Monitoring Agent : indisponible",
        "healthy": "Tous les services principaux sont prêts",
        "history_quick": "Historique rapide",
        "no_history": "Aucun historique.",
        "history_fail": "Échec lecture historique :",
        "new_trip_title": "## ✈️ Planifier votre voyage",
        "new_trip_desc": "Une phrase → itinéraire + budget + attractions + export PDF/ICS.",
        "describe_trip": "Décrivez votre voyage",
        "placeholder": "Exemple : Voyage de 7 jours de NJ à LA du 15 au 22 mars, budget 3600$. J’aime culture, food et photo.",
        "trip_budget": "Budget du voyage ($)",
        "add_attractions_cb": "Ajouter des attractions",
        "enable_monitoring_cb": "Activer le monitoring 24/7",
        "allow_guest_cb": "Autoriser le mode invité (sans connexion)",
        "allow_guest_help": "Si activé, l’invité peut générer/exporter sans connexion.",
        "btn_generate": "🚀 Générer",
        "btn_demo": "🎭 Démo",
        "btn_clear": "🔄 Effacer",
        "err_no_query": "Veuillez décrire votre voyage.",
        "warn_login_or_guest": "Veuillez vous connecter ou activer le mode invité.",
        "status_creating": "🚀 Génération de l’itinéraire...",
        "st_init_agent": "🔍 Initialisation de l’agent...",
        "st_conf_detected": "📅 Voyage conférence détecté - ajout de blocs agenda",
        "st_generating": "🌐 Génération...",
        "st_parsing": "📝 Analyse...",
        "err_parse": "Impossible de parser le JSON de l’itinéraire.",
        "st_add_attractions": "⭐ Ajout des attractions...",
        "done_ready": "✅ Votre voyage est prêt !",
        "err_failed": "❌ Échec de génération",
        "tab_itinerary": "📅 Itinéraire",
        "tab_flights_hotels": "✈️ Vols & Hôtels",
        "tab_attractions": "🎯 Attractions",
        "tab_export": "📥 Export",
        "itinerary_title": "### 📅 Votre itinéraire",
        "dest": "Destination",
        "depart": "Départ",
        "return": "Retour",
        "trip_summary": "Résumé",
        "all_prices_usd": "Tous les prix en USD ($)",
        "fh_title": "### ✈️ Vols & Hôtels",
        "fh_none": "Aucun vol/hôtel trouvé.",
        "export_title": "### 📥 Export & Partage",
        "dl_pdf": "📄 Télécharger PDF",
        "dl_ics": "📅 Télécharger ICS",
        "pdf_disabled": "ReportLab indisponible — export PDF désactivé.",
        "email_itin": "📧 Envoyer par email",
        "sent_to": "✅ Envoyé à",
        "send_fail": "Échec d’envoi email",
        "login_needed_email": "Connectez-vous pour activer email & monitoring.",
        "trip_history_title": "## 📚 Historique",
        "need_login_history": "Veuillez vous connecter (le mode invité ne sauvegarde pas).",
        "no_trips": "Aucun voyage pour l’instant.",
        "track_external": "Suivre un vol externe",
        "add_monitoring": "Ajouter au monitoring",
        "now_monitoring": "Surveillance activée",
    },
}

def get_lang() -> str:
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    return st.session_state.lang

def t(key: str) -> str:
    lang = get_lang()
    return I18N.get(lang, I18N["en"]).get(key, I18N["en"].get(key, key))

# =========================
# Session init
# =========================
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "plan_md" not in st.session_state:
    st.session_state.plan_md = None
if "payload" not in st.session_state:
    st.session_state.payload = None
if "budget_tracker" not in st.session_state:
    st.session_state.budget_tracker = None
if "current_trip_id" not in st.session_state:
    st.session_state.current_trip_id = None
if "settings" not in st.session_state:
    st.session_state.settings = {
        "default_budget": 2500,
        "auto_add_attractions": True,
        "auto_enable_monitoring": True,
        "guest_mode_allowed": True,
        "presence_ttl": 90,
    }

# =========================
# Services
# =========================
db = get_database()
email_service = get_email_service()
monitoring_agent = get_monitoring_agent(db, email_service)
payment_service = VirtualPaymentService(email_service=email_service)

# =========================
# UI helpers
# =========================
def hero():
    st.markdown("""
    <div class="hero-section">
      <h1 class="hero-title">✈️ MyAgent Booking</h1>
      <p style="font-size:1.25em;color:rgba(255,255,255,0.92);margin:0;">
        AI-Powered Premium Travel Experience
      </p>
      <p style="font-size:1em;color:rgba(255,255,255,0.86);margin-top:12px;">
        Smart Planning • Budget Guard • Monitoring • Export PDF/ICS
      </p>
    </div>
    """, unsafe_allow_html=True)

def _safe(v, default="—"):
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default

def format_usd(value: Any) -> str:
    if value is None:
        return "$0.00"
    if isinstance(value, (int, float)):
        return f"${float(value):,.2f}"
    s = str(value).strip()
    num = re.sub(r"[^\d.]", "", s)
    try:
        f = float(num) if num else 0.0
    except Exception:
        f = 0.0
    return f"${f:,.2f}"

def to_float_price(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    num = re.sub(r"[^\d.]", "", s)
    try:
        return float(num) if num else 0.0
    except Exception:
        return 0.0

def get_total_price(a: Dict) -> float:
    if a.get("price_total") is not None:
        return to_float_price(a.get("price_total"))
    return to_float_price(a.get("price"))

def get_per_night(a: Dict) -> float:
    return to_float_price(a.get("price_per_night"))

def _make_search_url(query: str) -> str:
    q = re.sub(r"\s+", "+", query.strip())
    return f"https://www.google.com/search?q={q}"

def enrich_actions_with_required_fields(payload: Dict) -> Dict:
    meta = payload.get("meta", {}) or {}
    depart = meta.get("depart_date")
    ret = meta.get("return_date")

    actions = payload.get("actions", []) or []
    for a in actions:
        ttype = (a.get("type") or "").lower()

        # unify currency
        a["currency"] = a.get("currency") or meta.get("currency") or "USD"

        # unify deep_link fallback
        if not a.get("deep_link"):
            a["deep_link"] = a.get("booking_url") or a.get("provider_url") or a.get("url") or a.get("link")

        if ttype == "hotel":
            a["check_in"] = a.get("check_in") or depart
            a["check_out"] = a.get("check_out") or ret

            if not a.get("nights") and a.get("check_in") and a.get("check_out"):
                try:
                    d0 = datetime.date.fromisoformat(a["check_in"])
                    d1 = datetime.date.fromisoformat(a["check_out"])
                    a["nights"] = max(1, (d1 - d0).days)
                except Exception:
                    a["nights"] = a.get("nights") or None

            if get_total_price(a) > 0 and (get_per_night(a) <= 0) and a.get("nights"):
                try:
                    a["price_per_night"] = round(get_total_price(a) / float(a["nights"]), 2)
                except Exception:
                    pass

            if not a.get("hotel_name") and a.get("title"):
                a["hotel_name"] = a.get("title")

        if ttype == "flight":
            if not a.get("flight_number") and a.get("flight_no"):
                a["flight_number"] = a.get("flight_no")
            if not a.get("departure_time_local") and a.get("departure"):
                a["departure_time_local"] = a.get("departure")
            if not a.get("arrival_time_local") and a.get("arrival"):
                a["arrival_time_local"] = a.get("arrival")

    payload["actions"] = actions
    return payload

def render_action_detail(a: Dict):
    ttype = (a.get("type") or "").lower()
    detail_url = (
        a.get("deep_link")
        or a.get("booking_url")
        or a.get("provider_url")
        or a.get("url")
        or a.get("link")
    )

    if not detail_url:
        if ttype == "flight":
            sq = f"{a.get('airline','')} {a.get('flight_number','')} {a.get('departure_airport','')} {a.get('arrival_airport','')} price"
        elif ttype == "hotel":
            sq = f"{a.get('hotel_name') or a.get('title','')} {a.get('neighborhood','')} booking"
        else:
            sq = f"{a.get('title','')} details"
        detail_url = _make_search_url(sq)

    total = get_total_price(a)
    per_night = get_per_night(a)

    with st.expander("🔎 Detail information", expanded=False):
        if ttype == "flight":
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Airline**", _safe(a.get("airline")))
                st.write("**Flight No.**", _safe(a.get("flight_number")))
                st.write("**Class**", _safe(a.get("seat_class") or a.get("cabin")))
            with c2:
                st.write("**From**", _safe(a.get("departure_airport")))
                st.write("**To**", _safe(a.get("arrival_airport")))
                st.write("**Stops**", _safe(a.get("stops")))
            with c3:
                st.write("**Depart (local)**", _safe(a.get("departure_time_local")))
                st.write("**Arrive (local)**", _safe(a.get("arrival_time_local")))
                st.write("**Duration**", _safe(a.get("duration")))
            st.write("**Baggage**:", _safe(a.get("baggage")))
            st.write("**Refund/Change**:", _safe(a.get("refund_policy")))
            st.write("**Price (Total)**:", format_usd(total))

        elif ttype == "hotel":
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Hotel**", _safe(a.get("hotel_name") or a.get("title")))
                st.write("**Rating**", _safe(a.get("rating")))
                st.write("**Neighborhood**", _safe(a.get("neighborhood")))
            with c2:
                st.write("**Check-in**", _safe(a.get("check_in")))
                st.write("**Check-out**", _safe(a.get("check_out")))
                st.write("**Nights**", _safe(a.get("nights")))
            with c3:
                st.write("**Room**", _safe(a.get("room_type")))
                st.write("**Price / night**", format_usd(per_night) if per_night > 0 else "—")
                st.write("**Total**", format_usd(total))
            st.write("**Address**:", _safe(a.get("address")))
            st.write("**Cancellation**:", _safe(a.get("cancel_policy")))
            st.write("**Notes**:", _safe(a.get("notes")))

        else:
            st.write("**Title**:", _safe(a.get("title")))
            st.write("**Notes**:", _safe(a.get("notes")))
            st.write("**Price**:", format_usd(total))

        st.link_button("🌐 Open on provider (Booking / Google Flights)", detail_url, use_container_width=True)

def budget_status_from_total_est(total_budget: float, total_est: float) -> Dict[str, Any]:
    total_budget = float(total_budget or 0)
    used = float(total_est or 0)
    remaining = total_budget - used
    pct = (used / total_budget * 100.0) if total_budget > 0 else 0.0

    if total_budget <= 0:
        alert = "none"
    elif remaining < 0:
        alert = "critical"
    elif pct >= 90:
        alert = "warning"
    elif pct >= 75:
        alert = "caution"
    else:
        alert = "ok"

    return {
        "total_budget": total_budget,
        "used": used,
        "remaining": remaining,
        "percentage": pct,
        "alert_level": alert,
        "breakdown": {
            "selected_items": used,
            "total": used
        }
    }

def _to_float(x) -> float:
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    num = re.sub(r"[^\d.]", "", s)
    try:
        return float(num) if num else 0.0
    except Exception:
        return 0.0

def render_budget_tracker_glass(budget_tracker: BudgetTracker):
    status = budget_tracker.get_budget_status()

    cls = ""
    if status.get("alert_level") == "critical":
        cls = "budget-critical"
    elif status.get("alert_level") in ["warning", "caution"]:
        cls = "budget-alert"

    pct = float(status.get("percentage", 0))
    if pct >= 100:
        bar_color = "#dc3545"
    elif pct >= 90:
        bar_color = "#ffc107"
    elif pct >= 75:
        bar_color = "#fd7e14"
    else:
        bar_color = "#28a745"

    with st.expander("📊 Budget Breakdown"):
        breakdown = status.get("breakdown", {})
        for category, amount in breakdown.items():
            if category != "total" and amount and amount > 0:
                percent = (amount / status["total_budget"] * 100) if status["total_budget"] > 0 else 0
                st.metric(category.title(), f"${amount:.2f}", f"{percent:.1f}%")

    if status.get("alert_level") in ["warning", "critical"]:
        tips = suggest_budget_adjustments(status)
        if tips:
            st.warning("**💡 Budget Tips:**")
            for tip in tips:
                st.write(f"• {tip}")

def render_attractions_glass(destination: str, interests: Optional[List[str]] = None):
    st.markdown("### 🎯 Top Attractions")
    scorer = AttractionScorer()
    attractions = scorer.recommend_attractions(destination, interests or ["culture", "food"], "medium")

    if not attractions:
        st.info("No attractions found.")
        return

    for a in attractions:
        st.markdown(f"""
        <div class="glass-card">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h4 style="margin:0;color:#563;">{a.get('name','Attraction')}</h4>
            <span class="attraction-score">⭐ {a.get('rating','-')}</span>
          </div>
          <p style="color:#666;margin:10px 0 0;">
            {a.get('category','')} • {a.get('price_level','')} • Match: {a.get('match_score','-')}%
          </p>
        </div>
        """, unsafe_allow_html=True)

def parse_agent_output(raw_text: str) -> Tuple[str, Optional[Dict]]:
    json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
    plan_md = re.sub(r"```json.*?```", "", raw_text, flags=re.DOTALL).strip()

    payload = None
    if json_match:
        try:
            payload = json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {e}")

    return plan_md, payload

def build_beautiful_pdf(plan_md: str, meta: Dict, actions: List[Dict], budget_status: Optional[Dict] = None) -> bytes:
    if not REPORTLAB:
        return b""

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, spaceAfter=14)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceAfter=8)
    normal = ParagraphStyle("normal", parent=styles["BodyText"], fontSize=10.5, leading=14)

    story = []
    story.append(Paragraph("MyAgent Booking — Travel Itinerary", title))
    story.append(Paragraph(
        f"<b>Destination:</b> {meta.get('destination_city','')} &nbsp;&nbsp; "
        f"<b>From:</b> {meta.get('origin_city','')}<br/>"
        f"<b>Depart:</b> {meta.get('depart_date','')} &nbsp;&nbsp; "
        f"<b>Return:</b> {meta.get('return_date','')}",
        normal
    ))
    story.append(Spacer(1, 10))

    if budget_status:
        story.append(Paragraph("Budget Summary", h2))
        story.append(Paragraph(
            f"<b>Total:</b> ${budget_status.get('total_budget',0):.2f} &nbsp;&nbsp; "
            f"<b>Spent:</b> ${budget_status.get('used',0):.2f} &nbsp;&nbsp; "
            f"<b>Remaining:</b> ${budget_status.get('remaining',0):.2f} &nbsp;&nbsp; "
            f"<b>Usage:</b> {budget_status.get('percentage',0):.1f}%",
            normal
        ))
        story.append(Spacer(1, 10))

    story.append(Paragraph("Itinerary (AI Plan)", h2))
    safe_text = (
        plan_md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    safe_text = "<br/>".join([line.strip() for line in safe_text.splitlines()])
    story.append(Paragraph(safe_text, normal))
    story.append(Spacer(1, 14))

    if actions:
        story.append(Paragraph("Bookings / Actions", h2))
        table_data = [["Type", "Title", "Price", "Time/Notes"]]
        for a in actions:
            ttype = (a.get("type") or "").lower()
            if ttype == "hotel":
                time_notes = f"{a.get('check_in','')}→{a.get('check_out','')}  {a.get('nights','')} nights"
            else:
                time_notes = (str(a.get("departure_time_local") or a.get("departure") or "") + " " + str(a.get("duration") or "")).strip()

            table_data.append([
                str(a.get("type", "")),
                str(a.get("title", ""))[:60],
                format_usd(get_total_price(a)),
                time_notes[:70]
            ])

        tbl = Table(table_data, colWidths=[0.9*inch, 3.2*inch, 1.1*inch, 1.8*inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#667eea")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("FONTSIZE", (0,1), (-1,-1), 9.5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(tbl)

    doc.build(story)
    return buf.getvalue()

def build_ics(meta: Dict, actions: List[Dict]) -> bytes:
    dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    def ymd(d: str) -> str:
        return d.replace("-", "") if d else ""

    dest = meta.get("destination_city", "Trip")
    depart = ymd(meta.get("depart_date", ""))
    ret = ymd(meta.get("return_date", ""))

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MyAgentBooking//EN"]
    if depart:
        lines += [
            "BEGIN:VEVENT",
            f"UID:depart-{dtstamp}@myagentbooking",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;VALUE=DATE:{depart}",
            f"SUMMARY:Depart for {dest}",
            "END:VEVENT",
        ]
    if ret:
        lines += [
            "BEGIN:VEVENT",
            f"UID:return-{dtstamp}@myagentbooking",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;VALUE=DATE:{ret}",
            f"SUMMARY:Return from {dest}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")

# =========================
# Location helper (IP-based)
# =========================


def get_current_city() -> str:
    try:
        g = geocoder.ip("me")
        if g.ok:
            city = g.city
            country = g.country
            return f"{city}, {country}" if city else ""
    except Exception:
        pass
    return ""

# =========================
# Sidebar Auth Panel (NEW)
# =========================
def sidebar_auth_panel():
    # only show if not logged in
    if st.session_state.get("logged_in"):
        return

    st.markdown("""
    <style>
    .auth-wrap{
      background: rgba(255,255,255,0.96);
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 18px;
      padding: 16px 16px 10px 16px;
      box-shadow: 0 10px 28px rgba(0,0,0,0.06);
      margin-top: 10px;
    }
    .auth-title{
      font-weight: 850;
      color: #2b2b2b;
      margin: 2px 0 10px 0;
      font-size: 1.05em;
    }
    .auth-sub{
      color:#666;
      margin:0 0 10px 0;
      font-size:0.92em;
      line-height:1.35;
    }
    </style>
    """, unsafe_allow_html=True)

    

    tab_login, tab_signup = st.tabs([t("login_tab_login"), t("login_tab_signup")])

    with tab_login:
        with st.form("sidebar_login_form", clear_on_submit=False):
            email = st.text_input(t("email"), key="sb_login_email")
            password = st.text_input(t("password"), type="password", key="sb_login_pwd")
            submit = st.form_submit_button(t("btn_login"), use_container_width=True)

            if submit:
                user = db.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.success(t("login_ok"))
                    st.rerun()
                else:
                    st.error(t("login_bad"))

    with tab_signup:
        if "signup_default_location" not in st.session_state:
            st.session_state.signup_default_location = get_current_city()

        with st.form("sidebar_signup_form", clear_on_submit=False):
            new_email = st.text_input(t("email"), key="sb_signup_email")
            new_password = st.text_input(t("password"), type="password", key="sb_signup_pwd")
            confirm_password = st.text_input(t("confirm_password"), type="password", key="sb_signup_pwd2")
            full_name = st.text_input(t("full_name"), key="sb_signup_name")

            home_location = st.text_input(
                t("home_location"),
                value=st.session_state.signup_default_location,
                placeholder="e.g. New York, USA",
                key="sb_signup_home"
            )

            signup = st.form_submit_button(t("btn_signup"), use_container_width=True)

            if signup:
                if new_password != confirm_password:
                    st.error(t("pwd_mismatch"))
                elif len(new_password) < 8:
                    st.error(t("pwd_short"))
                else:
                    user_id = db.create_user(new_email, new_password, full_name, home_location)
                    if user_id:
                        st.success(t("signup_ok"))
                    else:
                        st.error(t("signup_fail"))

# =========================
# Sidebar + Nav
# =========================
def sidebar_navigation():
    with st.sidebar:
        if "lang" not in st.session_state:
            st.session_state.lang = "en"
        lang_label = st.selectbox(
            "Language",
            options=list(LANG_OPTIONS.keys()),
            index=list(LANG_OPTIONS.values()).index(st.session_state.lang)
            if st.session_state.lang in LANG_OPTIONS.values() else 0
        )
        st.session_state.lang = LANG_OPTIONS[lang_label]

        user = st.session_state.get("user")
        if user:
            name = getattr(user, "full_name", getattr(user, "name", "User"))
            email = getattr(user, "email", "")
            home = getattr(user, "home_location", "")
            st.markdown(f"""
            <div class="user-card">
              <h3 style="margin:0;">👤 {name}</h3>
              <p style="margin:8px 0 0 0;opacity:0.92;">{email}</p>
              <p style="margin:6px 0 0 0;opacity:0.9;font-size:0.92em;">📍 {home}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚪 Logout", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

        else:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
              <div class="mini-chip">{t("sidebar_guest_title")}</div>
              <p style="margin:10px 0 0 0;color:#444;font-weight:650;">
                {t("sidebar_guest_line1")}
              </p>
              <p style="margin:8px 0 0 0;color:#666;font-size:0.92em;">
                {t("sidebar_guest_line2")}
              </p>
            </div>
            """, unsafe_allow_html=True)

            # ✅ Login/Signup moved to sidebar (NEW)
            sidebar_auth_panel()

        st.markdown("---")

def top_nav():
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div:has(> div[data-testid="stRadio"]) {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 999px;
        padding: 10px 14px;
        box-shadow: 0 8px 26px rgba(0,0,0,0.08);
    }
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 10px; }
    div[data-testid="stRadio"] label {
        background: rgba(102,126,234,0.10);
        border: 1px solid rgba(102,126,234,0.18);
        padding: 10px 16px;
        border-radius: 999px;
        font-weight: 700;
        color: #222;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg,#667eea,#764ba2);
        border: 1px solid rgba(255,255,255,0.35);
        color: white;
        box-shadow: 0 6px 16px rgba(102,126,234,0.35);
    }
    div[data-testid="stRadio"] input { display:none; }
    </style>
    """, unsafe_allow_html=True)

    # ✅ Always show main pages (login is in sidebar now)
    nav_items = [t("nav_new_trip"), t("nav_trip_history"), t("nav_dashboard")]

    if "active_nav" not in st.session_state:
        st.session_state.active_nav = nav_items[0]

    st.session_state.active_nav = st.radio(
        "nav",
        nav_items,
        horizontal=True,
        label_visibility="collapsed",
        index=nav_items.index(st.session_state.active_nav) if st.session_state.active_nav in nav_items else 0
    )
    return st.session_state.active_nav

# =========================
# Pages
# =========================
def dashboard_page():
    st.markdown(t("dashboard_title"))
    ttl = int(st.session_state.get("settings", {}).get("presence_ttl", 90))
    online = presence_heartbeat(ttl_seconds=ttl)

    payload = st.session_state.get("payload")
    budget_tracker = st.session_state.get("budget_tracker")
    trip_id = st.session_state.get("current_trip_id")
    logged_in = st.session_state.get("logged_in", False)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(t("kpi_online"), f"{online}")
    with k2:
        st.metric(t("kpi_mode"), t("mode_logged_in") if logged_in else t("mode_guest"))
    with k3:
        st.metric(t("kpi_trip"), t("ready") if payload else t("none"))
    with k4:
        st.metric(t("kpi_monitor"), "Active" if (trip_id and logged_in) else t("none"))

    st.markdown("---")

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(f"""
        <div class="glass-card">
          <div class="mini-chip">{t("overview")}</div>
          <h3 style="margin:12px 0 6px 0;color:#222;">{t("trip_status_title")}</h3>
        </div>
        """, unsafe_allow_html=True)

        if payload:
            meta = payload.get("meta", {})
            actions = payload.get("actions", [])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Destination", meta.get("destination_city", "—"))
            with c2:
                st.metric("Depart", meta.get("depart_date", "—"))
            with c3:
                st.metric("Return", meta.get("return_date", "—"))

            st.markdown("### 📌 Key Items")
            for a in actions[:6]:
                ttype = (a.get("type") or "").lower()
                badge = "✈️ Flight" if ttype == "flight" else "🏨 Hotel" if ttype == "hotel" else "🧭 Item"
                total = get_total_price(a)
                per_night = get_per_night(a)

                if ttype == "hotel":
                    sub = f"{a.get('check_in','')}→{a.get('check_out','')} • {a.get('nights','')} nights"
                else:
                    sub = (str(a.get("departure_time_local") or "") + " " + str(a.get("duration") or "")).strip()

                st.markdown(f"""
                <div class="glass-card" style="padding:18px;">
                  <div style="display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;">
                    <div>
                      <span class="mini-chip">{badge}</span>
                      <div style="margin-top:10px;font-weight:850;color:#333;">{a.get("title","")}</div>
                      <div style="color:#777;margin-top:6px;font-size:0.95em;">{sub}</div>
                      {"<div style='color:#666;margin-top:6px;font-weight:800;'>" + format_usd(per_night) + "/night</div>" if (ttype=="hotel" and per_night>0) else "<div style='color:#666;margin-top:6px;font-weight:800;'>No nightly price</div>"}
                    </div>
                    <div style="text-align:right;min-width:170px;">
                      <div class="mini-chip">Total (USD)</div>
                      <div style="margin-top:10px;font-size:1.55em;font-weight:900;color:#667eea;">
                        {format_usd(total)}
                      </div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                render_action_detail(a)
        else:
            st.markdown(f"""
            <div class="glass-card" style="background: rgba(255,255,255,0.92);">
              <span class="mini-chip">{t("none")}</span>
              <h3 style="margin:12px 0 6px 0;color:#222;">{t("no_active_title")}</h3>
              <p style="margin:0;color:#666;">{t("no_active_desc")}</p>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div class="glass-card">
          <div class="mini-chip">Budget</div>
          <h3 style="margin:12px 0 6px 0;color:#222;">{t("budget_alert_title")}</h3>
        </div>
        """, unsafe_allow_html=True)

        if budget_tracker:
            render_budget_tracker_glass(budget_tracker)
        else:
            st.info("Budget tracker will appear after you generate a trip.")

        st.markdown(f"### 🧠 {t('health')}")
        ok = True

        if not REPORTLAB:
            ok = False
            st.warning(t("pdf_bad"))
        else:
            st.success(t("pdf_ok"))

        if monitoring_agent:
            st.success(t("mon_ok"))
        else:
            ok = False
            st.warning(t("mon_bad"))

        if ok:
            st.markdown(f"""
            <div class="glass-card" style="background: rgba(40,167,69,0.08);">
              <span class="mini-chip">✅ Healthy</span>
              <div style="margin-top:10px;color:#2b2b2b;font-weight:800;">{t("healthy")}</div>
            </div>
            """, unsafe_allow_html=True)

def new_trip_page():
    st.markdown(t("new_trip_title"))
    

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_area(t("describe_trip"), placeholder=t("placeholder"), height=110)

    with col2:
        s = st.session_state.get("settings", {})
        budget = st.number_input(t("trip_budget"), min_value=0, value=int(s.get("default_budget", 2500)), step=100)
        add_attractions = st.checkbox(t("add_attractions_cb"), value=bool(s.get("auto_add_attractions", True)))
        enable_monitoring = st.checkbox(t("enable_monitoring_cb"), value=bool(s.get("auto_enable_monitoring", True)))
        guest_ok = st.checkbox(t("allow_guest_cb"), value=bool(s.get("guest_mode_allowed", True)), help=t("allow_guest_help"))

    c1, c2, c3 = st.columns(3)
    with c1:
        run = st.button(t("btn_generate"), type="primary", use_container_width=True)
    with c2:
        demo = st.button(t("btn_demo"), use_container_width=True)
    with c3:
        clear = st.button(t("btn_clear"), use_container_width=True)

    if clear:
        st.session_state.plan_md = None
        st.session_state.payload = None
        st.session_state.budget_tracker = None
        st.session_state.current_trip_id = None
        st.rerun()

    if demo:
        query = "Plan a 7-day trip from NJ to LA from March 15-22, budget must lower than $3600. I love culture and food and photography."
        run = True

    if run:
        if not query and not demo:
            st.error(t("err_no_query"))
            return
        if (not st.session_state.logged_in) and (not guest_ok):
            st.warning(t("warn_login_or_guest"))
            return

        with st.status(t("status_creating"), expanded=True) as status:
            try:
                st.write(t("st_init_agent"))
                agent = TravelAgent()
                budget_tracker = BudgetTracker(budget)

                is_conf = ConferenceDetector.is_conference_trip(query, [])
                if is_conf:
                    st.write(t("st_conf_detected"))

                st.write(t("st_generating"))
                resp = agent.plan_trip(query + f" (Budget: ${budget})")

                st.write(t("st_parsing"))
                plan_md, payload = parse_agent_output(resp.text)
                if not payload:
                    st.error(t("err_parse"))
                    status.update(label=t("err_failed"), state="error")
                    return

                payload = enrich_actions_with_required_fields(payload)

                for action in payload.get("actions", []):
                    category, price = budget_tracker.parse_price_from_action(action)
                    budget_tracker.add_expense(category, price)

                if add_attractions:
                    st.write(t("st_add_attractions"))
                    scorer = AttractionScorer()
                    payload = scorer.integrate_with_itinerary(payload)

                st.session_state.plan_md = plan_md
                st.session_state.payload = payload
                st.session_state.budget_tracker = budget_tracker

                user = st.session_state.get("user")
                if user:
                    meta = payload.get("meta", {})
                    trip_id = db.save_trip(
                        user_id=user.id,
                        trip_name=f"{meta.get('destination_city', 'Trip')} {meta.get('depart_date', '')}",
                        destination=meta.get("destination_city", ""),
                        depart_date=meta.get("depart_date", ""),
                        return_date=meta.get("return_date", ""),
                        budget=budget,
                        itinerary_json=json.dumps(payload)
                    )
                    st.session_state.current_trip_id = trip_id

                    if enable_monitoring and monitoring_agent:
                        monitoring_agent.start_monitoring(trip_id)

                status.update(label=t("done_ready"), state="complete")
                st.success(t("done_ready"))
                st.balloons()

            except Exception as e:
                st.error(f"Error: {str(e)}")
                status.update(label=t("err_failed"), state="error")
                return

    if st.session_state.payload:
        payload = st.session_state.payload
        plan_md = st.session_state.plan_md or ""
        budget_tracker = st.session_state.budget_tracker

        meta = payload.get("meta", {})
        actions = payload.get("actions", [])

        if budget_tracker:
            render_budget_tracker_glass(budget_tracker)

        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs([t("tab_itinerary"), t("tab_flights_hotels"), t("tab_attractions"), t("tab_export")])

        with tab1:
            st.markdown(t("itinerary_title"))
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(t("dest"), meta.get("destination_city", "N/A"))
            with c2:
                st.metric(t("depart"), meta.get("depart_date", "N/A"))
            with c3:
                st.metric(t("return"), meta.get("return_date", "N/A"))

            origin = meta.get("origin_city", "")
            dest = meta.get("destination_city", "")
            depart = meta.get("depart_date", "")
            ret = meta.get("return_date", "")

            st.markdown(f"""
            <div class="glass-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap;">
                    <div>
                        <div class="mini-chip">{t("trip_summary")}</div>
                        <h3 style="margin:12px 0 6px 0;">{origin} → {dest}</h3>
                        <p style="margin:0;color:#666;">🗓 {depart}  →  {ret}</p>
                    </div>
                    <div style="text-align:right;min-width:220px;">
                    <div class="mini-chip">Budget</div>
                    <h3 style="margin:12px 0 6px 0;">{format_usd(budget_tracker.total_budget if hasattr(budget_tracker,'total_budget') else 0)}</h3>
                    <p style="margin:0;color:#666;">{t("all_prices_usd")}</p>
                </div>
                </div>
                <hr style="border:none;border-top:1px solid rgba(0,0,0,0.08);margin:18px 0;">
            <div style="color:#333;line-height:1.65;font-size:1.02em;white-space:pre-wrap;">{plan_md}</div>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.markdown(t("fh_title"))

            st.markdown("### 💳 Pay Everything Together")

            user_obj = st.session_state.get("user")
            logged_in = bool(user_obj)
            trip_id_for_pay = st.session_state.get("current_trip_id")

            if logged_in:
                payer_email_all = getattr(user_obj, "email", "")
            else:
                payer_email_all = st.text_input(
                    "Receipt Email (Guest) — for all payments",
                    placeholder="you@example.com",
                    key="guest_email_pay_all"
                )

            if actions:
                if "pay_all_selected" not in st.session_state:
                    st.session_state.pay_all_selected = {i: True for i in range(len(actions))}

                total_est = 0.0
                for i, a in enumerate(actions):
                    if st.session_state.pay_all_selected.get(i, True):
                        total_est += get_total_price(a)

                st.caption("选择要合并支付的项目（默认全选）")

                with st.expander("🧾 Select items to pay together", expanded=False):
                    for i, a in enumerate(actions):
                        tt = (a.get("type") or "").lower()
                        badge = "✈️ Flight" if tt == "flight" else "🏨 Hotel" if tt == "hotel" else "🧭 Item"
                        title = a.get("title", "")
                        price_str = format_usd(get_total_price(a))
                        st.session_state.pay_all_selected[i] = st.checkbox(
                            f"{badge} — {title} ({price_str})",
                            value=st.session_state.pay_all_selected.get(i, True),
                            key=f"pay_all_ck_{i}"
                        )

                cpay1, cpay2 = st.columns([1, 1])
                with cpay1:
                    st.metric("Estimated Total (USD)", format_usd(total_est))
                with cpay2:
                    pay_all = st.button("💳 Pay Everything (Virtual)", type="primary", use_container_width=True)

                if pay_all:
                    if (not payer_email_all) or ("@" not in payer_email_all):
                        st.error("Please provide a valid email to receive the receipt.")
                    else:
                        items = []
                        for i, a in enumerate(actions):
                            if not st.session_state.pay_all_selected.get(i, True):
                                continue
                            items.append({
                                "name": f"{(a.get('type','Item') or 'Item').title()} — {a.get('title','')}",
                                "amount": get_total_price(a),
                                "qty": 1,
                                "meta": {
                                    "type": a.get("type"),
                                    "title": a.get("title"),
                                    "departure": a.get("departure_time_local"),
                                    "duration": a.get("duration"),
                                    "check_in": a.get("check_in"),
                                    "check_out": a.get("check_out"),
                                    "nights": a.get("nights"),
                                    "rating": a.get("rating"),
                                }
                            })

                        if not items:
                            st.warning("No items selected.")
                        else:
                            selection_sig = "|".join([
                                f"{i}:{a.get('type','')}:{a.get('title','')}:{get_total_price(a)}"
                                for i, a in enumerate(actions) if st.session_state.pay_all_selected.get(i, True)
                            ])
                            idem = f"payall-{trip_id_for_pay}-{hash(selection_sig)}"

                            invoice = payment_service.create_invoice(
                                items=items,
                                trip_id=trip_id_for_pay,
                                user_id=getattr(user_obj, "id", None) if user_obj else None,
                                payer_email=payer_email_all,
                                currency="USD",
                                tax_rate=0.0,
                                idempotency_key=idem
                            )
                            invoice = payment_service.mark_paid(invoice["invoice_id"], payer_email=payer_email_all)

                            ok = payment_service.send_receipt_email(
                                invoice=invoice,
                                payer_email=payer_email_all,
                                title="Everything (Flights/Hotels) Paid"
                            )
                            if ok:
                                st.success(f"✅ Paid! Receipt sent to {payer_email_all}")
                            else:
                                st.warning("✅ Paid! But receipt email failed (check email_service).")
            else:
                st.info("No booking items yet. Generate a trip first.")

            st.markdown("---")

            if not actions:
                st.info(t("fh_none"))

            for a in actions:
                ttype = (a.get("type") or "").lower()
                badge = "✈️ Flight" if ttype == "flight" else "🏨 Hotel" if ttype == "hotel" else "🧭 Item"

                total = get_total_price(a)
                per_night = get_per_night(a)

                detail_url = a.get("deep_link") or a.get("link") or a.get("url") or a.get("booking_url") or a.get("provider_url")
                title = a.get("title", "")
                if detail_url:
                    title_html = f'<a href="{detail_url}" target="_blank" style="text-decoration:none;color:#555;">{title}</a>'
                else:
                    title_html = title

                if ttype == "flight":
                    sub = " ".join([_safe(a.get("departure_time_local"), ""), _safe(a.get("duration"), "")]).strip()
                elif ttype == "hotel":
                    sub = f"{_safe(a.get('check_in'))} → {_safe(a.get('check_out'))} • {_safe(a.get('nights'))} nights"
                else:
                    sub = ""

                extra = []
                if ttype == "hotel" and per_night > 0:
                    extra.append(f"💤 {format_usd(per_night)}/night")
                if a.get("rating"):
                    extra.append(f"⭐ {a.get('rating')}")
                extra_line = " • ".join([x for x in extra if x])

                st.markdown(f"""
                <div class="glass-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
                    <div style="min-width:260px;">
                      <div class="mini-chip">{badge}</div>
                      <h3 style="margin:12px 0 6px 0;color:#666;">{title_html}</h3>
                      <p style="margin:0;color:#888;">{sub}</p>
                      <p style="margin:8px 0 0 0;color:#689;">{extra_line}</p>
                    </div>
                    <div style="text-align:right;min-width:220px;">
                      <div class="mini-chip">Total (USD)</div>
                      <div style="font-size:2.1em;font-weight:900;color:#667eea;margin-top:10px;">
                        {format_usd(total)}
                      </div>
                      {"<div style='color:#666;margin-top:6px;font-weight:800;'>" + format_usd(per_night) + "/night</div>" if (ttype=="hotel" and per_night>0) else "<div style='color:#666;margin-top:6px;font-weight:800;'>No nightly price</div>"}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                render_action_detail(a)

                pay_col1, pay_col2 = st.columns([1, 2])
                with pay_col1:
                    if st.session_state.get("user"):
                        payer_email = getattr(st.session_state.user, "email", "")
                    else:
                        payer_email = st.text_input("Receipt Email (Guest)", placeholder="you@example.com", key=f"guest_email_{title}_{uuid.uuid4()}")

                with pay_col2:
                    if st.button("💳 Pay & Confirm (Virtual)", key=f"pay_{title}_{uuid.uuid4()}", use_container_width=True):
                        amount = total
                        trip_id_for_pay = st.session_state.get("current_trip_id")
                        user_obj = st.session_state.get("user")
                        user_id_for_pay = getattr(user_obj, "id", None) if user_obj else None

                        idem = f"{trip_id_for_pay}-{a.get('type','')}-{a.get('title','')}-{amount}"

                        invoice = payment_service.create_invoice(
                            items=[{
                                "name": f"{a.get('type','Item').title()} — {a.get('title','')}",
                                "amount": amount,
                                "qty": 1,
                                "meta": {
                                    "type": a.get("type"),
                                    "title": a.get("title"),
                                    "departure": a.get("departure_time_local"),
                                    "duration": a.get("duration"),
                                    "check_in": a.get("check_in"),
                                    "check_out": a.get("check_out"),
                                    "nights": a.get("nights"),
                                }
                            }],
                            trip_id=trip_id_for_pay,
                            user_id=user_id_for_pay,
                            payer_email=payer_email,
                            currency="USD",
                            tax_rate=0.0,
                            idempotency_key=idem
                        )
                        invoice = payment_service.mark_paid(invoice["invoice_id"], payer_email=payer_email)

                        if payer_email:
                            ok = payment_service.send_receipt_email(
                                invoice=invoice,
                                payer_email=payer_email,
                                title=f"{a.get('type','Booking').title()} Confirmation"
                            )
                            if ok:
                                st.success(f"✅ Paid! Receipt sent to {payer_email}")
                            else:
                                st.warning("✅ Paid! But receipt email failed to send (check email_service).")
                        else:
                            st.success("✅ Paid! (No email provided, so no receipt was sent.)")

        with tab3:
            if meta.get("destination_city"):
                render_attractions_glass(meta["destination_city"], interests=["culture", "food"])

        with tab4:
            st.markdown(t("export_title"))
            col1, col2, col3 = st.columns(3)

            budget_status = budget_tracker.get_budget_status() if budget_tracker else None
            pdf_bytes = build_beautiful_pdf(plan_md, meta, actions, budget_status=budget_status)
            ics_bytes = build_ics(meta, actions)

            with col1:
                if REPORTLAB and pdf_bytes:
                    st.download_button(t("dl_pdf"), data=pdf_bytes, file_name="itinerary.pdf", mime="application/pdf", use_container_width=True)
                else:
                    st.warning(t("pdf_disabled"))

            with col2:
                st.download_button(t("dl_ics"), data=ics_bytes, file_name="trip.ics", mime="text/calendar", use_container_width=True)

            with col3:
                user = st.session_state.get("user")
                if user:
                    if st.button(t("email_itin"), use_container_width=True):
                        ok = email_service.send_itinerary_email(
                            to_email=user.email,
                            user_name=getattr(user, "full_name", "User"),
                            trip_name=f"{meta.get('destination_city','Your Trip')}",
                            destination=meta.get("destination_city", ""),
                            depart_date=meta.get("depart_date", ""),
                            return_date=meta.get("return_date", ""),
                            pdf_content=pdf_bytes,
                            ics_content=ics_bytes
                        )
                        if ok:
                            st.success(f"{t('sent_to')} {user.email}")
                        else:
                            st.error(t("send_fail"))
                else:
                    st.info(t("login_needed_email"))

def trip_history_page():
    st.markdown(t("trip_history_title"))

    user = st.session_state.get("user")
    if not user:
        st.warning(t("need_login_history"))
        return

    trips = db.get_user_trips(user.id)
    if not trips:
        st.info(t("no_trips"))
        return

    for trip in trips:
        with st.expander(f"✈️ {trip['trip_name']} - {trip['status'].title()}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(t("dest"), trip["destination"])
                st.metric("Dates", f"{trip['depart_date']} → {trip['return_date']}")
            with c2:
                st.metric("Budget", f"${trip['budget']:.2f}")
                st.metric("Actual Cost", f"${trip['actual_cost']:.2f}")
            with c3:
                st.metric("Status", trip["status"].title())

                if trip["status"] == "ongoing":
                    flight_num = st.text_input(t("track_external"), key=f"flight_{trip['id']}", placeholder="e.g., UA123")
                    if st.button(t("add_monitoring"), key=f"btn_{trip['id']}"):
                        if flight_num and monitoring_agent:
                            monitoring_agent.add_external_flight(
                                trip_id=trip["id"],
                                flight_number=flight_num,
                                flight_date=trip["depart_date"],
                                user_email=getattr(user, "email", "")
                            )
                            st.success(f"{t('now_monitoring')} {flight_num}")

def main():
    hero()
    sidebar_navigation()
    page = top_nav()

    if t("nav_new_trip") in page:
        new_trip_page()
    elif t("nav_trip_history") in page:
        trip_history_page()
    elif t("nav_dashboard") in page:
        dashboard_page()
    else:
        new_trip_page()

if __name__ == "__main__":
    main()
