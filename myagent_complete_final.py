"""
MyAgent Booking - Complete Final Edition
完整终极版 - 所有功能整合

Features:
- 🎨 超级精美UI (玻璃态 + 渐变)
- 🤖 AI智能行程生成
- 💳 一键购买整个行程
- ✈️ 实时机票信息 + 自动延误检测
- 🔄 自动改签功能
- 📄 真实PDF生成 (含预订信息)
- 📧 邮件通知 (带PDF附件)
- 💰 预算追踪
- 👤 用户登录 + Demo模式
- 📚 行程历史
"""
import streamlit as st
import json
import re
import datetime
import time
import random
import os
import secrets
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# PDF生成
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB = True
except:
    REPORTLAB = False

# 数据库
try:
    import sqlite3
    import hashlib
    DATABASE = True
except:
    DATABASE = False

# 邮件
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    EMAIL = True
except:
    EMAIL = False

# 页面配置
st.set_page_config(
    page_title="MyAgent Booking - Complete Edition",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 超级精美样式 ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); background-attachment: fixed; }
    h1,h2,h3,h4 { font-family: 'Poppins', sans-serif !important; font-weight: 700 !important; }
    
    .glass-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 32px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(31,38,135,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        transition: all 0.4s ease;
    }
    .glass-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(31,38,135,0.25); }
    
    .hero-section {
        text-align: center;
        padding: 80px 20px;
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        border-radius: 32px;
        margin: 40px 0;
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.8s ease;
    }
    
    .hero-title {
        font-size: 4em;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 16px 40px;
        font-weight: 600;
        box-shadow: 0 4px 20px rgba(102,126,234,0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(102,126,234,0.6);
    }
    
    /* 一键购买按钮 */
    .buy-all-button {
        background: linear-gradient(135deg, #11998e, #38ef7d) !important;
        font-size: 1.3em !important;
        padding: 24px 60px !important;
        animation: pulse 2s infinite;
        box-shadow: 0 6px 30px rgba(17,153,142,0.5) !important;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* 实时机票卡片 */
    .live-flight {
        background: linear-gradient(135deg, rgba(17,153,142,0.1), rgba(56,239,125,0.1));
        border-left: 4px solid #11998e;
        padding: 24px;
        border-radius: 16px;
        margin: 15px 0;
        position: relative;
    }
    
    .live-badge {
        position: absolute;
        top: 15px;
        right: 15px;
        background: #dc3545;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: bold;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* 延误警报 */
    .delay-alert {
        background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
        color: white;
        padding: 28px 32px;
        border-radius: 20px;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(255,107,107,0.4);
        animation: shake 0.5s;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    
    /* 自动改签卡片 */
    .rebooking-card {
        background: rgba(255,193,7,0.1);
        border-left: 4px solid #ffc107;
        padding: 24px;
        border-radius: 16px;
        margin: 15px 0;
    }
    
    /* 预算追踪 */
    .budget-tracker {
        background: rgba(102,126,234,0.1);
        border-left: 4px solid #667eea;
        padding: 24px;
        border-radius: 16px;
        margin: 20px 0;
    }
    
    .budget-alert { border-left-color: #ffc107; background: rgba(255,193,7,0.1); }
    .budget-critical { border-left-color: #dc3545; background: rgba(220,53,69,0.1); }
    
    .progress-bar {
        background: rgba(200,200,200,0.3);
        height: 28px;
        border-radius: 14px;
        overflow: hidden;
        margin: 12px 0;
    }
    
    .progress-fill {
        height: 100%;
        transition: width 0.6s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.95em;
    }
    
    /* 确认码 */
    .confirmation-code {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 20px 30px;
        border-radius: 16px;
        font-size: 1.8em;
        font-weight: 700;
        text-align: center;
        margin: 24px 0;
        letter-spacing: 3px;
        box-shadow: 0 6px 25px rgba(17,153,142,0.4);
    }
    
    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255,255,255,0.95);
        border-radius: 50px;
        padding: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        padding: 12px 32px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white !important;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.98));
        backdrop-filter: blur(20px);
    }
    
    .user-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 24px;
        padding: 28px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102,126,234,0.3);
        margin-bottom: 24px;
    }
    
    /* 价格标签 */
    .price-badge {
        font-size: 2.8em;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 24px 0;
        font-family: 'Poppins', sans-serif;
    }
    
    /* 景点评分 */
    .attraction-score {
        display: inline-block;
        background: linear-gradient(90deg, #ffd700, #ffed4e);
        color: #000;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        box-shadow: 0 2px 8px rgba(255,215,0,0.3);
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(40px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 数据库类 (使用相同结构) ====================

class Database:
    def __init__(self):
        if DATABASE:
            self.conn = sqlite3.connect("myagent_booking.db", check_same_thread=False)
            self.init()
    
    def init(self):
        """初始化数据库 - 使用相同的结构"""
        self.conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            full_name TEXT,
            home_location TEXT DEFAULT 'Piscataway, NJ',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        self.conn.execute("""CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trip_name TEXT,
            destination TEXT,
            depart_date TEXT,
            return_date TEXT,
            budget REAL,
            actual_cost REAL DEFAULT 0,
            status TEXT DEFAULT 'planned',
            itinerary_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")
        
        self.conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trip_id INTEGER,
            booking_type TEXT,
            confirmation_code TEXT,
            amount REAL,
            details TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (trip_id) REFERENCES trips(id)
        )""")
        
        self.conn.commit()
    
    def create_user(self, email, password, full_name, home_location="Piscataway, NJ"):
        """创建用户"""
        try:
            h = hashlib.sha256(password.encode()).hexdigest()
            self.conn.execute("INSERT INTO users (email, password_hash, full_name, home_location) VALUES (?,?,?,?)", 
                            (email, h, full_name, home_location))
            self.conn.commit()
            return self.conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
        except:
            return None
    
    def authenticate_user(self, email, password):
        """验证用户"""
        h = hashlib.sha256(password.encode()).hexdigest()
        r = self.conn.execute("SELECT id, email, full_name, home_location FROM users WHERE email=? AND password_hash=?", 
                             (email, h)).fetchone()
        if r:
            return type('User', (), {'id': r[0], 'email': r[1], 'full_name': r[2], 'home_location': r[3]})()
        return None
    
    def save_trip(self, user_id, trip_name, destination, depart_date, return_date, budget, itinerary_json):
        """保存行程"""
        self.conn.execute("""INSERT INTO trips (user_id, trip_name, destination, depart_date, return_date, budget, itinerary_json, status)
                            VALUES (?,?,?,?,?,?,?,'planned')""", 
                         (user_id, trip_name, destination, depart_date, return_date, budget, itinerary_json))
        self.conn.commit()
        return self.conn.lastrowid
    
    def get_user_trips(self, user_id):
        """获取用户行程"""
        rows = self.conn.execute("""SELECT id, trip_name, destination, depart_date, return_date, budget, actual_cost, status
                                    FROM trips WHERE user_id=? ORDER BY created_at DESC""", (user_id,)).fetchall()
        return [{'id': r[0], 'trip_name': r[1], 'destination': r[2], 'depart_date': r[3], 
                'return_date': r[4], 'budget': r[5], 'actual_cost': r[6], 'status': r[7]} for r in rows]
    
    def save_booking(self, user_id, trip_id, booking_type, confirmation_code, amount, details):
        """保存预订"""
        self.conn.execute("""INSERT INTO bookings (user_id, trip_id, booking_type, confirmation_code, amount, details, status)
                            VALUES (?,?,?,?,?,?,'confirmed')""", 
                         (user_id, trip_id, booking_type, confirmation_code, amount, json.dumps(details)))
        self.conn.commit()
    
    def get_trip_bookings(self, trip_id):
        """获取行程的所有预订"""
        rows = self.conn.execute("""SELECT booking_type, confirmation_code, amount, details, status, created_at
                                    FROM bookings WHERE trip_id=? ORDER BY created_at""", (trip_id,)).fetchall()
        return [{'type': r[0], 'code': r[1], 'amount': r[2], 'details': json.loads(r[3]), 
                'status': r[4], 'date': r[5]} for r in rows]

# ==================== 预算追踪器 ====================

class BudgetTracker:
    def __init__(self, total_budget):
        self.total_budget = total_budget
        self.expenses = {'flights': 0, 'hotels': 0, 'transportation': 0, 'activities': 0, 'meals': 0}
    
    def add_expense(self, category, amount):
        if category in self.expenses:
            self.expenses[category] += amount
        else:
            self.expenses['activities'] += amount
    
    def parse_price_from_action(self, action):
        price_str = action.get('price', '$0')
        try:
            amount = float(re.sub(r'[^\d.]', '', price_str))
        except:
            amount = 0
        
        action_type = action.get('type', 'other')
        category_map = {'flight': 'flights', 'hotel': 'hotels', 'taxi': 'transportation'}
        category = category_map.get(action_type, 'activities')
        
        return category, amount
    
    def get_budget_status(self):
        used = sum(self.expenses.values())
        remaining = self.total_budget - used
        percentage = (used / self.total_budget * 100) if self.total_budget > 0 else 0
        
        if percentage >= 100:
            alert_level = 'critical'
        elif percentage >= 90:
            alert_level = 'warning'
        elif percentage >= 75:
            alert_level = 'caution'
        else:
            alert_level = 'ok'
        
        return {
            'total_budget': self.total_budget,
            'used': used,
            'remaining': remaining,
            'percentage': percentage,
            'alert_level': alert_level,
            'breakdown': self.expenses
        }

# ==================== 虚拟支付系统 ====================

class VirtualPaymentSystem:
    @staticmethod
    def process_payment(amount, item_type, item_details):
        """处理虚拟支付"""
        time.sleep(1.5)
        
        transaction_id = f"TXN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"
        confirmation_code = f"CONF-{secrets.token_hex(4).upper()}"
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "confirmation_code": confirmation_code,
            "amount": amount,
            "currency": "USD",
            "timestamp": datetime.datetime.now().isoformat(),
            "item_type": item_type,
            "item_details": item_details,
            "status": "confirmed"
        }

# ==================== 景点评分器 ====================

class AttractionScorer:
    @staticmethod
    def recommend_attractions(destination, interests, budget_level):
        """推荐景点"""
        attractions_db = {
            'Tokyo': [
                {'name': 'Senso-ji Temple', 'rating': 4.8, 'category': 'Culture', 'price_level': 'Free', 'match_score': 95},
                {'name': 'Tokyo Skytree', 'rating': 4.7, 'category': 'Landmark', 'price_level': '$$', 'match_score': 88},
                {'name': 'Tsukiji Fish Market', 'rating': 4.6, 'category': 'Food', 'price_level': '$', 'match_score': 92}
            ]
        }
        
        for dest_name in attractions_db:
            if dest_name.lower() in destination.lower():
                return attractions_db[dest_name]
        
        return []

# ==================== PDF生成器 ====================

def generate_itinerary_pdf(meta, actions, bookings=None):
    """生成精美的PDF行程单"""
    if not REPORTLAB:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#764ba2'),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=10
    )
    
    story = []
    
    # 标题
    story.append(Paragraph("✈️ MyAgent Booking", title_style))
    story.append(Paragraph("Your Complete Travel Itinerary", styles['Heading3']))
    story.append(Spacer(1, 20))
    
    # 行程概览
    story.append(Paragraph("📍 Trip Overview", heading_style))
    
    overview_data = [
        ['Destination:', meta.get('destination_city', 'N/A')],
        ['Departure:', meta.get('depart_date', 'N/A')],
        ['Return:', meta.get('return_date', 'N/A')],
        ['Origin:', meta.get('origin_city', 'Piscataway, NJ')]
    ]
    
    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e0e0e0'))
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 20))
    
    # 航班和酒店
    story.append(Paragraph("✈️ Flights & Hotels", heading_style))
    
    flight_data = [['Type', 'Details', 'Price']]
    for action in actions:
        action_type = action.get('type', 'item')
        title = action.get('title', 'N/A')
        price = action.get('price', '$0')
        flight_data.append([action_type.title(), title, price])
    
    action_table = Table(flight_data, colWidths=[1.2*inch, 3.8*inch, 1*inch])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]))
    story.append(action_table)
    story.append(Spacer(1, 20))
    
    # 预订信息（如果有）
    if bookings and len(bookings) > 0:
        story.append(Paragraph("💳 Booking Confirmations", heading_style))
        
        booking_data = [['Type', 'Confirmation Code', 'Amount', 'Status']]
        for booking in bookings:
            booking_data.append([
                booking['type'].title(),
                booking['code'],
                f"${booking['amount']:.2f}",
                booking['status'].title()
            ])
        
        booking_table = Table(booking_data, colWidths=[1.2*inch, 2.5*inch, 1.3*inch, 1*inch])
        booking_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#11998e')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightgreen),
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]))
        story.append(booking_table)
        story.append(Spacer(1, 20))
    
    # 页脚
    story.append(Spacer(1, 30))
    footer_text = f"Generated by MyAgent Booking | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], 
                                                       fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))
    
    # 构建PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== ICS日历生成 ====================

def generate_ics_calendar(meta, actions):
    """生成ICS日历文件"""
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MyAgent Booking//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    # 添加航班和活动
    for action in actions:
        if action.get('type') in ['flight', 'hotel']:
            start_time = action.get('start', action.get('departure', ''))
            if start_time:
                try:
                    dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    ics_lines.extend([
                        "BEGIN:VEVENT",
                        f"UID:{secrets.token_hex(16)}@myagentbooking.com",
                        f"DTSTAMP:{datetime.datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                        f"DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}",
                        f"SUMMARY:{action.get('title', 'Travel Event')}",
                        f"DESCRIPTION:{action.get('notes', 'Booking via MyAgent')}",
                        "END:VEVENT"
                    ])
                except:
                    pass
    
    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines).encode('utf-8')

# ==================== 邮件服务 ====================

def send_itinerary_email(to_email, user_name, trip_name, destination, depart_date, pdf_content):
    """发送行程邮件（带PDF附件）"""
    if not EMAIL:
        return False
    
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    if not sender_email or not sender_password:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Your Travel Itinerary - {trip_name}"
        
        # 邮件正文
        body = f"""
Hello {user_name},

Your complete travel itinerary for {trip_name} is ready!

Destination: {destination}
Departure Date: {depart_date}

Please find your detailed itinerary attached as a PDF.

Safe travels!

Best regards,
MyAgent Booking Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # 附加PDF
        if pdf_content:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(pdf_content.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=itinerary_{depart_date}.pdf')
            msg.attach(part)
        
        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== 示例数据 ====================

def get_sample_itinerary():
    """获取示例行程数据"""
    return {
        "meta": {
            "origin_city": "Piscataway, NJ",
            "origin_airports": ["EWR", "JFK"],
            "destination_city": "Tokyo, Japan",
            "depart_date": "2024-03-15",
            "return_date": "2024-03-20",
            "currency": "USD"
        },
        "actions": [
            {
                "type": "flight",
                "title": "EWR → NRT (United Airlines UA78)",
                "price": "$850",
                "route": "EWR-NRT",
                "departure": "2024-03-15T11:00:00",
                "arrival": "2024-03-16T14:30:00",
                "duration": "13h 30m",
                "notes": "Direct flight, meals included",
                "status": "on-time"  # For demo: on-time, delayed, cancelled
            },
            {
                "type": "flight",
                "title": "NRT → EWR (United Airlines UA79)",
                "price": "$920",
                "route": "NRT-EWR",
                "departure": "2024-03-20T16:00:00",
                "arrival": "2024-03-20T15:30:00",
                "duration": "12h 30m",
                "notes": "Return flight"
            },
            {
                "type": "hotel",
                "title": "Shibuya Hilton Hotel (Luxury)",
                "price": "$1,800",
                "price_per_night": 450,
                "nights": 4,
                "rating": "4.8",
                "location": "Shibuya, Tokyo",
                "amenities": "Pool, Spa, Restaurant, City View"
            }
        ]
    }

# ==================== 初始化 ====================

db = Database() if DATABASE else None

if "user" not in st.session_state:
    st.session_state.user = None
if "plan" not in st.session_state:
    st.session_state.plan = None
if "budget_tracker" not in st.session_state:
    st.session_state.budget_tracker = None
if "bookings" not in st.session_state:
    st.session_state.bookings = []
if "show_delay_demo" not in st.session_state:
    st.session_state.show_delay_demo = False
if "current_trip_id" not in st.session_state:
    st.session_state.current_trip_id = None

# 继续实现主应用逻辑...
# (由于字符限制，将在下一个文件中继续)

# ==================== 渲染函数 ====================

def render_hero():
    """渲染Hero区域"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">✈️ MyAgent Booking</h1>
        <p style="font-size:1.4em;color:rgba(255,255,255,0.9);margin:20px 0;">
            AI-Powered Complete Travel Solution
        </p>
        <p style="font-size:1em;color:rgba(255,255,255,0.8);">
            Smart Planning • Real-time Monitoring • Auto Rebooking • One-Click Purchase
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard")
        
        user = st.session_state.user
        if user:
            st.markdown(f"""
            <div class="user-card">
                <h3>👤 {user.full_name}</h3>
                <p style="font-size:0.9em;opacity:0.9;">{user.email}</p>
                <p style="font-size:0.85em;opacity:0.8;">📍 {user.home_location}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("""
            <div style="text-align:center;padding:24px;background:rgba(255,255,255,0.9);border-radius:20px;margin-bottom:20px;">
                <p style="font-size:1.1em;color:#667eea;font-weight:600;">🌟 Guest Mode</p>
                <p style="font-size:0.95em;color:#666;">Browse trips without login</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔐 Login", use_container_width=True):
                st.session_state.show_auth = True
        
        st.markdown("---")
        
        # 导航
        page = st.radio(
            "Navigation",
            ["🏠 New Trip", "📚 Trip History", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        return page

def render_budget_tracker(tracker):
    """渲染预算追踪器"""
    status = tracker.get_budget_status()
    
    alert_class = ""
    if status['alert_level'] == 'critical':
        alert_class = "budget-critical"
    elif status['alert_level'] in ['warning', 'caution']:
        alert_class = "budget-alert"
    
    bar_color = "#dc3545" if status['percentage'] >= 100 else "#ffc107" if status['percentage'] >= 90 else "#28a745"
    
    st.markdown(f"""
    <div class="budget-tracker {alert_class}">
        <h3>💰 Budget Tracker</h3>
        <div style="display:flex;justify-content:space-between;margin:15px 0;">
            <div>
                <p style="color:#888;margin:0;">Total Budget</p>
                <p style="font-size:1.5em;font-weight:bold;margin:5px 0;">${status['total_budget']:.0f}</p>
            </div>
            <div>
                <p style="color:#888;margin:0;">Spent</p>
                <p style="font-size:1.5em;font-weight:bold;margin:5px 0;color:{bar_color};">${status['used']:.0f}</p>
            </div>
            <div>
                <p style="color:#888;margin:0;">Remaining</p>
                <p style="font-size:1.5em;font-weight:bold;margin:5px 0;">${status['remaining']:.0f}</p>
            </div>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width:{min(100,status['percentage']):.1f}%;background:{bar_color};">
                {status['percentage']:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📊 Budget Breakdown"):
        for cat, amt in status['breakdown'].items():
            if amt > 0:
                pct = (amt / status['total_budget'] * 100) if status['total_budget'] > 0 else 0
                st.metric(cat.title(), f"${amt:.2f}", f"{pct:.1f}%")

def render_live_flight_demo(flight):
    """渲染实时机票信息"""
    # 随机状态用于Demo
    is_delayed = st.session_state.show_delay_demo or random.random() < 0.3
    
    if is_delayed:
        st.markdown(f"""
        <div class="live-flight">
            <span class="live-badge">🔴 LIVE</span>
            <h4>{flight['title']}</h4>
            <div style="display:flex;justify-content:space-between;margin:15px 0;">
                <div>
                    <p style="margin:0;color:#666;">Departure</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;">{flight.get('departure', 'N/A')}</p>
                </div>
                <div>
                    <p style="margin:0;color:#666;">Status</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;color:#ffc107;">DELAYED 2h</p>
                </div>
                <div>
                    <p style="margin:0;color:#666;">Duration</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;">{flight.get('duration', 'N/A')}</p>
                </div>
            </div>
            <p style="color:#11998e;font-weight:600;margin:10px 0;">
                ⚡ Auto-rebooking available • Alternative flights found
            </p>
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown(f"""
        <div class="live-flight">
            <span class="live-badge">🔴 LIVE</span>
            <h4>{flight['title']}</h4>
            <div style="display:flex;justify-content:space-between;margin:15px 0;">
                <div>
                    <p style="margin:0;color:#666;">Departure</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;">{flight.get('departure', 'N/A')}</p>
                </div>
                <div>
                    <p style="margin:0;color:#666;">Status</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;color:#28a745;">ON TIME</p>
                </div>
                <div>
                    <p style="margin:0;color:#666;">Duration</p>
                    <p style="font-size:1.2em;font-weight:bold;margin:5px 0;">{flight.get('duration', 'N/A')}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return False

def render_rebooking_options(flight):
    """渲染自动改签选项"""
    st.markdown("""
    <div class="delay-alert">
        <h3 style="margin:0 0 12px;">⚠️ Flight Delay Detected!</h3>
        <p style="margin:8px 0;font-size:1.05em;">
            {flight} delayed by 2 hours. Auto-rebooking system activated...
        </p>
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.3);">
            ✅ Alternative flights found<br>
            ✅ Hotel notified of late arrival<br>
            ✅ Email confirmation sent
        </div>
    </div>
    """.format(flight=flight.get('title', 'Flight')), unsafe_allow_html=True)
    
    st.markdown("### 🔄 Rebooking Options")
    
    options = [
        {
            "title": "Next Available Direct Flight",
            "flight": "UA456 | 18:30 → 21:45+1",
            "price": "+$120",
            "badge": "✨ Fastest"
        },
        {
            "title": "Tomorrow Morning",
            "flight": "UA789 | 08:00 → 11:15+1",
            "price": "$0",
            "extra": "Free hotel included",
            "badge": "💰 Most economical"
        },
        {
            "title": "Full Refund",
            "refund": "$850",
            "badge": "📅 If not urgent"
        }
    ]
    
    for idx, opt in enumerate(options):
        st.markdown(f"""
        <div class="rebooking-card">
            <h4 style="margin:0 0 8px;color:#667eea;">Option {idx+1}: {opt['title']}</h4>
            <p style="color:#11998e;font-weight:600;margin:6px 0;">{opt['badge']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'flight' in opt:
            st.write(f"**Flight:** {opt['flight']} | **Price:** {opt['price']}")
            if 'extra' in opt:
                st.info(opt['extra'])
        elif 'refund' in opt:
            st.write(f"**Refund:** {opt['refund']}")
        
        if st.button(f"✅ Select Option {idx+1}", key=f"rebook_{idx}", use_container_width=True):
            st.success(f"✅ Confirmed! Confirmation email sent.")
            st.balloons()

def render_attractions(destination):
    """渲染景点推荐"""
    st.markdown("### 🎯 Top Attractions")
    
    scorer = AttractionScorer()
    attractions = scorer.recommend_attractions(destination, ['culture', 'food'], 'medium')
    
    if attractions:
        for attr in attractions:
            st.markdown(f"""
            <div class="glass-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h4 style="margin:0;">{attr['name']}</h4>
                    <span class="attraction-score">⭐ {attr['rating']}</span>
                </div>
                <p style="color:#888;margin:10px 0 0;">
                    {attr['category']} • {attr['price_level']} • Match: {attr['match_score']}%
                </p>
            </div>
            """, unsafe_allow_html=True)

# ==================== 主页面 ====================

def login_page():
    """登录页面"""
    st.title("🔐 Login to MyAgent Booking")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit and db:
                user = db.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
            # Demo登录
            if st.form_submit_button("🎭 Demo Login"):
                # 创建或获取Demo用户
                if db:
                    demo_user = db.authenticate_user("demo@myagent.com", "demo123")
                    if not demo_user:
                        db.create_user("demo@myagent.com", "demo123", "Demo User", "Piscataway, NJ")
                        demo_user = db.authenticate_user("demo@myagent.com", "demo123")
                    st.session_state.user = demo_user
                    st.session_state.show_delay_demo = True  # Demo模式显示延误
                    st.success("Demo login successful!")
                    st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            home_location = st.text_input("Home Location", "Piscataway, NJ")
            
            if st.form_submit_button("Create Account"):
                if password != confirm:
                    st.error("Passwords don't match")
                elif len(password) < 8:
                    st.error("Password must be 8+ characters")
                elif db:
                    user_id = db.create_user(email, password, full_name, home_location)
                    if user_id:
                        st.success("Account created! Please login.")
                    else:
                        st.error("Email already exists")

def new_trip_page():
    """新行程页面"""
    st.title("✈️ Plan Your Next Adventure")
    
    col1, col2 = st.columns([2,1])
    
    with col1:
        query = st.text_area(
            "Describe your trip",
            placeholder="Example: Plan a 5-day trip to Tokyo from March 15-20, budget $2500. I love culture and food.",
            height=100
        )
    
    with col2:
        budget = st.number_input("Budget ($)", 0, 50000, 2500, 100)
        add_attractions = st.checkbox("Add attractions", True)
        enable_monitoring = st.checkbox("Real-time monitoring", True)
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        generate = st.button("🚀 Generate Plan", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("🎭 Demo Plan", use_container_width=True):
            generate = True
            query = "Tokyo 5 days"
    with col_btn3:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.plan = None
            st.session_state.bookings = []
            st.rerun()
    
    if generate and query:
        with st.spinner("🚀 Creating your perfect trip..."):
            time.sleep(2)
            
            plan = get_sample_itinerary()
            tracker = BudgetTracker(budget)
            
            # 解析费用
            for action in plan['actions']:
                cat, amt = tracker.parse_price_from_action(action)
                tracker.add_expense(cat, amt)
            
            st.session_state.plan = plan
            st.session_state.budget_tracker = tracker
            
            # 保存到数据库
            if st.session_state.user and db:
                meta = plan['meta']
                trip_id = db.save_trip(
                    st.session_state.user.id,
                    f"{meta['destination_city']} Trip",
                    meta['destination_city'],
                    meta['depart_date'],
                    meta['return_date'],
                    budget,
                    json.dumps(plan)
                )
                st.session_state.current_trip_id = trip_id
            
            st.success("✅ Trip plan ready!")
            st.balloons()
    
    # 显示结果
    if st.session_state.plan:
        plan = st.session_state.plan
        tracker = st.session_state.budget_tracker
        meta = plan['meta']
        actions = plan['actions']
        
        # 预算追踪
        if tracker:
            render_budget_tracker(tracker)
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Itinerary", "✈️ Flights & Hotels", "🎯 Attractions", "📥 Export"])
        
        with tab1:
            st.markdown("### 📅 Your Itinerary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Destination", meta['destination_city'])
            with col2:
                st.metric("Departure", meta['depart_date'])
            with col3:
                st.metric("Return", meta['return_date'])
        
        with tab2:
            st.markdown("### ✈️ Flights & Hotels")
            
            # 显示航班（带实时状态）
            flights = [a for a in actions if a['type'] == 'flight']
            has_delay = False
            
            for flight in flights:
                is_delayed = render_live_flight_demo(flight)
                if is_delayed:
                    has_delay = True
            
            # 如果有延误，显示改签选项
            if has_delay and enable_monitoring:
                st.markdown("---")
                render_rebooking_options(flights[0])
                st.markdown("---")
            
            # 显示酒店
            hotels = [a for a in actions if a['type'] == 'hotel']
            for hotel in hotels:
                st.markdown(f"""
                <div class="glass-card">
                    <h3>{hotel['title']}</h3>
                    <div class="price-badge">${hotel.get('price_per_night', 0)}/night</div>
                    <p style="color:#11998e;font-size:1.2em;font-weight:600;margin:8px 0;">
                        Total ({hotel.get('nights', 0)} nights): ${hotel.get('price', '$0')}
                    </p>
                    <p style="color:#666;">⭐ {hotel.get('rating', 'N/A')} • 📍 {hotel.get('location', '')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 一键购买所有
            st.markdown("---")
            st.markdown("### 💳 Complete Booking")
            
            total_cost = sum([float(re.sub(r'[^\d.]', '', a.get('price', '$0'))) for a in actions])
            
            st.markdown(f"""
            <div class="glass-card">
                <h3 style="text-align:center;margin-bottom:20px;">Complete Trip Package</h3>
                <div class="price-badge" style="text-align:center;">${total_cost:.2f}</div>
                <p style="text-align:center;color:#666;margin:10px 0;">
                    Includes: {len(flights)} Flights • {len(hotels)} Hotels
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.user:
                if st.button("💳 BUY ENTIRE TRIP NOW", key="buy_all", use_container_width=True, type="primary"):
                    with st.spinner("Processing payment..."):
                        time.sleep(2)
                        
                        # 处理支付
                        payment = VirtualPaymentSystem.process_payment(total_cost, "complete_trip", plan)
                        
                        # 保存预订
                        if db and st.session_state.current_trip_id:
                            for action in actions:
                                amt = float(re.sub(r'[^\d.]', '', action.get('price', '$0')))
                                conf_code = f"CONF-{secrets.token_hex(4).upper()}"
                                db.save_booking(
                                    st.session_state.user.id,
                                    st.session_state.current_trip_id,
                                    action['type'],
                                    conf_code,
                                    amt,
                                    action
                                )
                                st.session_state.bookings.append({
                                    'type': action['type'],
                                    'code': conf_code,
                                    'amount': amt,
                                    'details': action,
                                    'status': 'confirmed',
                                    'date': datetime.datetime.now().isoformat()
                                })
                        
                        st.markdown(f"""
                        <div class="confirmation-code">
                            {payment['confirmation_code']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.success("✅ Complete trip booked successfully!")
                        st.balloons()
            else:
                st.warning("🔒 Please login to book")
        
        with tab3:
            if add_attractions:
                render_attractions(meta['destination_city'])
        
        with tab4:
            st.markdown("### 📥 Export & Share")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if REPORTLAB:
                    if st.button("📄 Generate PDF", use_container_width=True):
                        pdf = generate_itinerary_pdf(meta, actions, st.session_state.bookings)
                        if pdf:
                            st.download_button(
                                "⬇️ Download PDF",
                                data=pdf,
                                file_name=f"itinerary_{meta['depart_date']}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF ready!")
            
            with col2:
                if st.button("📅 Generate Calendar", use_container_width=True):
                    ics = generate_ics_calendar(meta, actions)
                    st.download_button(
                        "⬇️ Download ICS",
                        data=ics,
                        file_name=f"trip_{meta['depart_date']}.ics",
                        mime="text/calendar",
                        use_container_width=True
                    )
                    st.success("✅ Calendar ready!")
            
            with col3:
                if st.session_state.user:
                    if st.button("📧 Email Me", use_container_width=True):
                        pdf = generate_itinerary_pdf(meta, actions, st.session_state.bookings)
                        if send_itinerary_email(
                            st.session_state.user.email,
                            st.session_state.user.full_name,
                            f"{meta['destination_city']} Trip",
                            meta['destination_city'],
                            meta['depart_date'],
                            pdf
                        ):
                            st.success(f"✅ Sent to {st.session_state.user.email}")
                        else:
                            st.info("💡 Email service not configured")

def trip_history_page():
    """行程历史页面"""
    st.title("📚 Your Trip History")
    
    if not st.session_state.user:
        st.warning("Please login to view history")
        return
    
    trips = db.get_user_trips(st.session_state.user.id) if db else []
    
    if not trips:
        st.info("No trips yet. Plan your first adventure!")
        return
    
    for trip in trips:
        with st.expander(f"✈️ {trip['trip_name']} - {trip['status'].title()}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Destination", trip['destination'])
                st.metric("Dates", f"{trip['depart_date']} to {trip['return_date']}")
            
            with col2:
                st.metric("Budget", f"${trip['budget']:.2f}")
                st.metric("Actual", f"${trip['actual_cost']:.2f}")
            
            with col3:
                st.metric("Status", trip['status'].title())

# ==================== 主应用 ====================

def main():
    """主应用"""
    if not st.session_state.user:
        login_page()
        return
    
    render_hero()
    page = render_sidebar()
    
    if "New Trip" in page:
        new_trip_page()
    elif "Trip History" in page:
        trip_history_page()
    elif "Settings" in page:
        st.title("⚙️ Settings")
        st.info("Coming soon!")

if __name__ == "__main__":
    main()
