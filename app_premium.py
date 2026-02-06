"""
MyAgent Booking - Ultimate Premium Edition (Merged)
超美玻璃态UI + Enhanced功能 + 无需登录即可使用

Guest Mode:
- ✅ AI 行程生成
- ✅ 预算追踪 + 警报 + 建议
- ✅ 景点评分推荐
- ✅ PDF/ICS 导出下载

Login Mode (Optional):
- ✅ 用户认证 & Trip History
- ✅ 保存行程到数据库
- ✅ Email 通知
- ✅ 实时监控(绑定 trip_id)
- ✅ 外部航班监控

Language:
- ✅ English / 中文 / Français
"""

import streamlit as st
import json
import re
import datetime
from io import BytesIO
from typing import Tuple, Optional, Dict, List, Any
import os
import sqlite3
import time
import uuid

from dotenv import load_dotenv
load_dotenv()

# ---- Imports from your enhanced app (keep core logic unchanged) ----
try:
    from agent import TravelAgent
except ImportError:
    from agents.agent import TravelAgent

from database import get_database
from email_service import get_email_service
from budget_and_scoring import (
    BudgetTracker, AttractionScorer, ConferenceDetector,
    calculate_daily_budget, suggest_budget_adjustments
)
from monitoring_agent import get_monitoring_agent

# ---- PDF deps ----
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
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
    """
    Update heartbeat for current session and return online count.
    Works across multiple Streamlit processes if they share filesystem (/tmp).
    """
    if "presence_session_id" not in st.session_state:
        st.session_state.presence_session_id = str(uuid.uuid4())

    now = int(time.time())
    sid = st.session_state.presence_session_id

    conn = _presence_conn()
    try:
        # Upsert heartbeat
        conn.execute(
            "INSERT INTO presence(session_id,last_seen) VALUES(?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET last_seen=excluded.last_seen",
            (sid, now)
        )
        # Cleanup old sessions
        conn.execute("DELETE FROM presence WHERE last_seen < ?", (now - ttl_seconds,))
        conn.commit()

        # Count
        cur = conn.execute("SELECT COUNT(*) FROM presence WHERE last_seen >= ?", (now - ttl_seconds,))
        online = int(cur.fetchone()[0])
        return online
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
# i18n (EN / ZH / FR)
# =========================
LANG_OPTIONS = {
    "English": "en",
    "中文": "zh",
    "Français": "fr",
}

I18N = {
    "en": {
        "nav_new_trip": "🏠 New Trip",
        "nav_trip_history": "📚 Trip History",
        "nav_dashboard": "📊 Dashboard",
        "nav_settings": "⚙️ Settings",
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

        "settings_title": "## ⚙️ Settings",
        "prefs_center": "Preferences Center",
        "prefs_desc": "Control defaults, density, export habits & monitoring behavior (all prices in USD $).",
        "ui_usage": "### 🧊 UI & Usage",
        "compact_mode": "Compact Mode (tighter)",
        "guest_allowed": "Allow Guest Mode by default",
        "presence_ttl": "Online count window (seconds)",
        "planning_defaults": "### ✨ Planning Defaults",
        "default_budget": "Default budget (USD)",
        "auto_add_attractions": "Auto add attraction recommendations",
        "auto_enable_monitoring": "Auto enable monitoring (bind trip_id after login)",
        "export_defaults": "### 📥 Export Defaults",
        "export_pdf_default": "Enable PDF export by default",
        "export_ics_default": "Enable ICS export by default",
        "notifications": "### 📧 Notifications",
        "email_notify_default": "Allow email sending by default (logged-in users)",
        "currency_title": "Unified currency display",
        "currency_desc": "All prices are displayed as USD ($).",
        "saved_session": "✅ Saved to current session. Want to persist for logged-in users? I can write settings into DB.",

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
        "nav_settings": "⚙️ Settings",
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

        "settings_title": "## ⚙️ Settings",
        "prefs_center": "Preferences Center",
        "prefs_desc": "控制默认开关、UI密度、导出习惯与监控行为（所有价格统一 USD $）。",
        "ui_usage": "### 🧊 UI & Usage",
        "compact_mode": "Compact Mode（更紧凑）",
        "guest_allowed": "默认允许 Guest Mode",
        "presence_ttl": "在线人数统计窗口（秒）",
        "planning_defaults": "### ✨ Planning Defaults",
        "default_budget": "默认预算（USD）",
        "auto_add_attractions": "默认添加景点推荐",
        "auto_enable_monitoring": "默认开启监控（登录后绑定 trip_id）",
        "export_defaults": "### 📥 Export Defaults",
        "export_pdf_default": "默认启用 PDF 导出",
        "export_ics_default": "默认启用 ICS 导出",
        "notifications": "### 📧 Notifications",
        "email_notify_default": "默认允许邮件发送（登录用户）",
        "currency_title": "统一货币显示",
        "currency_desc": "当前版本所有价格固定显示为 USD ($)。",
        "saved_session": "✅ 已保存到当前会话。若你希望“登录用户永久保存”，我可以帮你把 settings 写进数据库。",

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
        "nav_settings": "⚙️ Paramètres",
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

        "settings_title": "## ⚙️ Paramètres",
        "prefs_center": "Centre de préférences",
        "prefs_desc": "Gérez les options par défaut, la densité UI, l’export et le monitoring (prix en USD $).",
        "ui_usage": "### 🧊 UI & Usage",
        "compact_mode": "Mode compact",
        "guest_allowed": "Autoriser le mode invité par défaut",
        "presence_ttl": "Fenêtre du compteur en ligne (secondes)",
        "planning_defaults": "### ✨ Planning Defaults",
        "default_budget": "Budget par défaut (USD)",
        "auto_add_attractions": "Ajouter automatiquement des attractions",
        "auto_enable_monitoring": "Activer automatiquement le monitoring (après connexion)",
        "export_defaults": "### 📥 Export Defaults",
        "export_pdf_default": "Activer l’export PDF par défaut",
        "export_ics_default": "Activer l’export ICS par défaut",
        "notifications": "### 📧 Notifications",
        "email_notify_default": "Autoriser l’envoi d’emails par défaut (connecté)",
        "currency_title": "Devise unifiée",
        "currency_desc": "Tous les prix sont affichés en USD ($).",
        "saved_session": "✅ Enregistré dans la session. Si vous voulez persister pour les utilisateurs connectés, on peut écrire en DB.",

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

# =========================
# Services
# =========================
db = get_database()
email_service = get_email_service()
monitoring_agent = get_monitoring_agent(db, email_service)

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

def format_usd(value: Any) -> str:
    """
    Normalize any price input to USD string like $1,234.56
    Accepts: "$850", "850", 850, 850.2, None
    """
    if value is None:
        return "$0.00"
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    s = str(value).strip()
    num = re.sub(r"[^\d.]", "", s)
    try:
        f = float(num) if num else 0.0
    except Exception:
        f = 0.0
    return f"${f:,.2f}"

def sidebar_navigation():
    with st.sidebar:
        # Language selector (EN / 中文 / FR)
        if "lang" not in st.session_state:
            st.session_state.lang = "en"

        lang_label = st.selectbox(
            "Language",
            options=list(LANG_OPTIONS.keys()),
            index=list(LANG_OPTIONS.values()).index(st.session_state.lang) if st.session_state.lang in LANG_OPTIONS.values() else 0
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

        st.markdown("---")

# =========================
# Pages
# =========================
def login_page():
    st.markdown(t("login_title"))
    tab1, tab2 = st.tabs([t("login_tab_login"), t("login_tab_signup")])

    with tab1:
        with st.form("login_form"):
            email = st.text_input(t("email"))
            password = st.text_input(t("password"), type="password")
            submit = st.form_submit_button(t("btn_login"))
            if submit:
                user = db.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.success(t("login_ok"))
                    st.rerun()
                else:
                    st.error(t("login_bad"))

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input(t("email"), key="signup_email")
            new_password = st.text_input(t("password"), type="password", key="signup_password")
            confirm_password = st.text_input(t("confirm_password"), type="password")
            full_name = st.text_input(t("full_name"))
            home_location = st.text_input(t("home_location"), value="Piscataway, NJ")
            signup = st.form_submit_button(t("btn_signup"))

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

def settings_page():
    st.markdown(t("settings_title"))

    if "settings" not in st.session_state:
        st.session_state.settings = {
            "compact_mode": False,
            "auto_add_attractions": True,
            "auto_enable_monitoring": True,
            "guest_mode_allowed": True,
            "default_budget": 2500,
            "presence_ttl": 90,
            "export_pdf_default": True,
            "export_ics_default": True,
            "email_notify_default": True,
        }

    s = st.session_state.settings

    st.markdown(f"""
    <div class="glass-card">
      <div class="mini-chip">{t("prefs_center")}</div>
      <h3 style="margin:12px 0 6px 0;color:#222;">{t("settings_title").replace("## ","")}</h3>
      <p style="margin:0;color:#666;">{t("prefs_desc")}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown(t("ui_usage"))
        s["compact_mode"] = st.toggle(t("compact_mode"), value=s["compact_mode"])
        s["guest_mode_allowed"] = st.toggle(t("guest_allowed"), value=s["guest_mode_allowed"])
        s["presence_ttl"] = st.slider(t("presence_ttl"), 30, 300, int(s["presence_ttl"]), step=15)

        st.markdown(t("planning_defaults"))
        s["default_budget"] = st.number_input(t("default_budget"), min_value=0, value=int(s["default_budget"]), step=100)
        s["auto_add_attractions"] = st.toggle(t("auto_add_attractions"), value=s["auto_add_attractions"])
        s["auto_enable_monitoring"] = st.toggle(t("auto_enable_monitoring"), value=s["auto_enable_monitoring"])

    with c2:
        st.markdown(t("export_defaults"))
        s["export_pdf_default"] = st.toggle(t("export_pdf_default"), value=s["export_pdf_default"])
        s["export_ics_default"] = st.toggle(t("export_ics_default"), value=s["export_ics_default"])

        st.markdown(t("notifications"))
        s["email_notify_default"] = st.toggle(t("email_notify_default"), value=s["email_notify_default"])

        st.markdown(f"""
        <div class="glass-card" style="background: rgba(102,126,234,0.08);">
          <span class="mini-chip">Currency</span>
          <h4 style="margin:12px 0 6px 0;color:#222;">{t("currency_title")}</h4>
          <p style="margin:0;color:#666;">{t("currency_desc")}</p>
        </div>
        """, unsafe_allow_html=True)

    if s["compact_mode"]:
        st.markdown("""
        <style>
          .glass-card { padding: 18px !important; }
          p, li, div { line-height: 1.45 !important; }
          .stButton>button { padding: 10px 18px !important; }
        </style>
        """, unsafe_allow_html=True)

    st.session_state.settings = s

    user = st.session_state.get("user")
    if user:
        st.info(t("saved_session"))

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

    st.markdown(f"""
    <div class="budget-tracker {cls}">
      <h3 style="margin-top:0;">💰 Budget Tracker</h3>
      <div style="display:flex;justify-content:space-between;margin:12px 0;">
        <div>
          <p style="color:#777;margin:0;">Total</p>
          <p style="font-size:1.6em;font-weight:900;margin:6px 0;">${status['total_budget']:.2f}</p>
        </div>
        <div>
          <p style="color:#777;margin:0;">Spent</p>
          <p style="font-size:1.6em;font-weight:900;margin:6px 0;color:{bar_color};">${status['used']:.2f}</p>
        </div>
        <div>
          <p style="color:#777;margin:0;">Left</p>
          <p style="font-size:1.6em;font-weight:900;margin:6px 0;">${status['remaining']:.2f}</p>
        </div>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" style="width:{min(100,pct):.1f}%;background:{bar_color};">
          {pct:.1f}%
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

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

# =========================
# Parsing / Export
# =========================
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
        plan_md.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
    )
    safe_text = "<br/>".join([line.strip() for line in safe_text.splitlines()])
    story.append(Paragraph(safe_text, normal))
    story.append(Spacer(1, 14))

    if actions:
        story.append(Paragraph("Bookings / Actions", h2))
        table_data = [["Type", "Title", "Price", "Time/Notes"]]
        for a in actions:
            table_data.append([
                str(a.get("type", "")),
                str(a.get("title", ""))[:60],
                str(a.get("price", "")),
                (str(a.get("departure", "")) + " " + str(a.get("duration", ""))).strip()[:70]
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

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MyAgentBooking//EN",
    ]
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
# Dashboard
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
                st.markdown(f"""
                <div class="glass-card" style="padding:18px;">
                  <div style="display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;">
                    <div>
                      <span class="mini-chip">{badge}</span>
                      <div style="margin-top:10px;font-weight:850;color:#333;">{a.get("title","")}</div>
                      <div style="color:#777;margin-top:6px;font-size:0.95em;">
                        {(str(a.get("departure","")) + " " + str(a.get("duration",""))).strip()}
                      </div>
                    </div>
                    <div style="text-align:right;min-width:170px;">
                      <div class="mini-chip">Price (USD)</div>
                      <div style="margin-top:10px;font-size:1.55em;font-weight:900;color:#667eea;">
                        {format_usd(a.get("price", 0))}
                      </div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
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
            status = budget_tracker.get_budget_status()
            alert = status.get("alert_level")
            if alert in ["warning", "critical"]:
                st.markdown(f"""
                <div class="glass-card" style="background: rgba(255,193,7,0.10);">
                  <span class="mini-chip">⚠️ Alert</span>
                  <h4 style="margin:10px 0 0 0;color:#222;">{t("budget_near")}</h4>
                  <p style="margin:8px 0 0 0;color:#666;">{t("budget_near_desc")}</p>
                </div>
                """, unsafe_allow_html=True)
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

        st.markdown(f"### 📚 {t('history_quick')}")
        user = st.session_state.get("user")
        if user:
            try:
                trips = db.get_user_trips(user.id) or []
                if trips:
                    for trip in trips[:4]:
                        st.markdown(f"""
                        <div class="glass-card" style="padding:16px;">
                          <div style="display:flex;justify-content:space-between;gap:10px;">
                            <div>
                              <div style="font-weight:850;color:#333;">{trip.get('trip_name','Trip')}</div>
                              <div style="color:#777;font-size:0.92em;margin-top:4px;">
                                {trip.get('depart_date','')} → {trip.get('return_date','')}
                              </div>
                            </div>
                            <div style="text-align:right;min-width:120px;">
                              <span class="mini-chip">{str(trip.get('status','')).title()}</span>
                            </div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(t("no_history"))
            except Exception as e:
                st.warning(f"{t('history_fail')} {e}")
        else:
            st.info("Login to see quick history cards.")

# =========================
# New Trip Page
# =========================
def new_trip_page():
    st.markdown(t("new_trip_title"))
    st.markdown(
        f'<div class="glass-card"><span class="mini-chip">🚀 Ultimate Premium</span>'
        f'<div style="margin-top:10px;color:#555;">{t("new_trip_desc")}</div></div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_area(
            t("describe_trip"),
            placeholder=t("placeholder"),
            height=110
        )

    with col2:
        s = st.session_state.get("settings", {})
        budget = st.number_input(t("trip_budget"), min_value=0, value=int(s.get("default_budget", 2500)), step=100)
        add_attractions = st.checkbox(t("add_attractions_cb"), value=bool(s.get("auto_add_attractions", True)))
        enable_monitoring = st.checkbox(t("enable_monitoring_cb"), value=bool(s.get("auto_enable_monitoring", True)))
        guest_ok = st.checkbox(
            t("allow_guest_cb"),
            value=bool(s.get("guest_mode_allowed", True)),
            help=t("allow_guest_help")
        )

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
        query = "Plan a 7-day trip from NJ to LA from March 15-22, budget $3600. I love culture and food and photography."
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
            if not actions:
                st.info(t("fh_none"))
            for a in actions:
                title = a.get("title", "")
                p = format_usd(a.get("price", 0))
                ttype = a.get("type", "").lower()
                badge = "✈️ Flight" if ttype == "flight" else "🏨 Hotel" if ttype == "hotel" else "🧭 Item"
                sub = " ".join([str(a.get("departure","")).strip(), str(a.get("duration","")).strip()]).strip()
                extra = []
                if a.get("nights") is not None:
                    extra.append(f"🌙 {a.get('nights')} nights")
                if a.get("rating"):
                    extra.append(f"⭐ {a.get('rating')}")

                extra_line = " • ".join([x for x in extra if x])

                st.markdown(f"""
        <div class="glass-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
            <div style="min-width:260px;">
              <div class="mini-chip">{badge}</div>
              <h3 style="margin:12px 0 6px 0;color:#888;">{title}</h3>
              <p style="margin:0;color:#888;">{sub}</p>
              <p style="margin:8px 0 0 0;color:#689;">{extra_line}</p>
            </div>
            <div style="text-align:right;min-width:200px;">
              <div class="mini-chip">Price (USD)</div>
              <div style="font-size:2.1em;font-weight:900;color:#667eea;margin-top:10px;">{p}</div>
            </div>
          </div>
        </div>
            """, unsafe_allow_html=True)

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
                    st.download_button(
                        t("dl_pdf"),
                        data=pdf_bytes,
                        file_name="itinerary.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.warning(t("pdf_disabled"))

            with col2:
                st.download_button(
                    t("dl_ics"),
                    data=ics_bytes,
                    file_name="trip.ics",
                    mime="text/calendar",
                    use_container_width=True
                )

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

# =========================
# Trip History
# =========================
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
                    flight_num = st.text_input(
                        t("track_external"),
                        key=f"flight_{trip['id']}",
                        placeholder="e.g., UA123"
                    )
                    if st.button(t("add_monitoring"), key=f"btn_{trip['id']}"):
                        if flight_num and monitoring_agent:
                            monitoring_agent.add_external_flight(
                                trip_id=trip["id"],
                                flight_number=flight_num,
                                flight_date=trip["depart_date"],
                                user_email=getattr(user, "email", "")
                            )
                            st.success(f"{t('now_monitoring')} {flight_num}")

# =========================
# Top Nav (pill style)
# =========================
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

    nav_items = [t("nav_new_trip"), t("nav_trip_history"), t("nav_dashboard"), t("nav_settings")]
    if not st.session_state.get("logged_in"):
        nav_items = [t("nav_new_trip"), t("nav_login"), t("nav_settings")]

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
# Main
# =========================
def main():
    hero()
    sidebar_navigation()

    page = top_nav()

    if t("nav_login") in page:
        login_page()
    elif t("nav_new_trip") in page:
        new_trip_page()
    elif t("nav_trip_history") in page:
        trip_history_page()
    elif t("nav_dashboard") in page:
        dashboard_page()
    elif t("nav_settings") in page:
        settings_page()
    else:
        # Fallback
        new_trip_page()

if __name__ == "__main__":
    main()
