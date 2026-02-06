"""
MyAgent Booking Premium - 完整旗舰版
Features:
- Google OAuth登录 + 游客模式
- 虚拟支付系统 + 真实邮件确认
- PDF/ICS生成下载
- 智能改签系统
- 天气/航班监控
- Demo模式演示
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
from typing import Tuple, Optional, Dict, List, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入模块
try:
    from agent import TravelAgent
    from database import get_database
    from email_service import get_email_service
    from free_flight_monitor import FlightMonitor
    from rebooking_and_rides import FlightRebookingAgent, RideHailingIntegration
except ImportError as e:
    st.error(f"导入错误: {e}")

# PDF生成
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ICS日历生成
from datetime import datetime as dt, timedelta

# 页面配置
st.set_page_config(
    page_title="MyAgent Booking Premium",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 超级精美样式 ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    h1, h2, h3, h4 { 
        font-family: 'Poppins', sans-serif !important; 
        font-weight: 700 !important; 
    }
    
    /* 玻璃态卡片 */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 32px;
        margin: 20px 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 16px 48px 0 rgba(31, 38, 135, 0.25);
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 80px 20px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        border-radius: 32px;
        margin: 40px 0;
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.8s ease-out;
    }
    
    .hero-title {
        font-size: 4em;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        letter-spacing: -2px;
        text-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        font-size: 1.4em;
        color: rgba(255, 255, 255, 0.9);
        margin: 20px 0;
        font-weight: 400;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 16px 40px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 4px 20px 0 rgba(102, 126, 234, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px 0 rgba(102, 126, 234, 0.6);
    }
    
    .stButton>button:active {
        transform: translateY(-1px);
    }
    
    /* 输入框 */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        border-radius: 16px;
        border: 2px solid rgba(102, 126, 234, 0.2);
        padding: 16px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.95);
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 50px;
        padding: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        padding: 12px 32px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.98) 100%);
        backdrop-filter: blur(20px);
    }
    
    [data-testid="stSidebar"] .element-container {
        backdrop-filter: none;
    }
    
    /* 用户卡片 */
    .user-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 24px;
        padding: 28px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        margin-bottom: 24px;
        animation: slideInRight 0.5s ease-out;
    }
    
    .user-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        margin: 0 auto 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5em;
        border: 4px solid rgba(255, 255, 255, 0.3);
    }
    
    /* 价格标签 */
    .price-badge {
        font-size: 2.8em;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 24px 0;
        font-family: 'Poppins', sans-serif;
        letter-spacing: -1px;
    }
    
    /* 航班/酒店卡片 */
    .flight-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-left: 5px solid #667eea;
        position: relative;
        overflow: hidden;
    }
    
    .flight-card::before {
        content: '✈️';
        position: absolute;
        font-size: 8em;
        opacity: 0.05;
        right: -20px;
        top: -20px;
    }
    
    .hotel-card {
        background: linear-gradient(135deg, rgba(243, 172, 18, 0.08) 0%, rgba(241, 39, 17, 0.08) 100%);
        border-left: 5px solid #f3ac12;
        position: relative;
        overflow: hidden;
    }
    
    .hotel-card::before {
        content: '🏨';
        position: absolute;
        font-size: 8em;
        opacity: 0.05;
        right: -20px;
        top: -20px;
    }
    
    /* 时间线 */
    .timeline {
        position: relative;
        padding-left: 40px;
        margin: 32px 0;
    }
    
    .timeline::before {
        content: '';
        position: absolute;
        left: 12px;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
    }
    
    .timeline-item {
        position: relative;
        margin: 24px 0;
        padding-left: 24px;
        animation: fadeInLeft 0.5s ease-out;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -32px;
        top: 8px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: 4px solid white;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2);
        z-index: 1;
    }
    
    /* 活动卡片 */
    .activity-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    
    .activity-card:hover {
        transform: translateX(8px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    
    /* 徽章 */
    .badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 50px;
        font-size: 0.9em;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .time-badge {
        background: linear-gradient(135deg, #f3ac12 0%, #f1a917 100%);
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.95em;
        font-weight: 600;
        color: white;
        display: inline-block;
        box-shadow: 0 2px 10px rgba(243, 172, 18, 0.3);
    }
    
    /* 日标题 */
    .day-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 28px 32px;
        border-radius: 20px;
        margin: 32px 0 24px 0;
        font-size: 1.8em;
        font-weight: 700;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* 警报 */
    .alert-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 20px;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
        animation: shake 0.5s ease-in-out;
    }
    
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 20px;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(17, 153, 142, 0.3);
    }
    
    /* 动画 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(0.98); }
    }
    
    .pulse { animation: pulse 2s infinite; }
    
    /* Google按钮 */
    .google-btn {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background: white;
        color: #444;
        border: 2px solid #e8e8e8;
        border-radius: 50px;
        padding: 14px 32px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .google-btn:hover {
        background: #f8f8f8;
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.12);
    }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 加载动画 */
    .loading-spinner {
        border: 4px solid rgba(102, 126, 234, 0.1);
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


# === 虚拟支付系统 ===
class VirtualPaymentSystem:
    """虚拟支付处理系统"""
    
    def __init__(self):
        self.processing_time = 2  # 模拟处理时间
    
    def process_payment(self, card_info: Dict, amount: float, 
                       item_type: str, item_details: Dict) -> Dict:
        """处理虚拟支付"""
        time.sleep(self.processing_time)
        
        transaction_id = f"TXN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        confirmation_code = f"CONF-{secrets.token_hex(4).upper()}"
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "confirmation_code": confirmation_code,
            "amount": amount,
            "currency": "USD",
            "timestamp": datetime.datetime.now().isoformat(),
            "card_last4": card_info.get("card_number", "")[-4:],
            "card_type": self._detect_card_type(card_info.get("card_number", "")),
            "item_type": item_type,
            "item_details": item_details,
            "status": "confirmed"
        }
    
    def _detect_card_type(self, card_number: str) -> str:
        """检测卡类型"""
        if card_number.startswith('4'):
            return "Visa"
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return "Mastercard"
        elif card_number.startswith(('34', '37')):
            return "American Express"
        else:
            return "Unknown"


# === PDF生成系统 ===
def generate_trip_pdf(trip_data: Dict, itinerary: Dict) -> BytesIO:
    """生成精美PDF行程单"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # 样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # 内容
    story = []
    
    # 标题
    story.append(Paragraph("✈️ MyAgent Booking", title_style))
    story.append(Paragraph("Your Travel Itinerary", styles['Heading3']))
    story.append(Spacer(1, 20))
    
    # 行程概览
    overview = trip_data.get('trip_overview', {})
    story.append(Paragraph("📍 Trip Overview", heading_style))
    
    overview_data = [
        ['Destination:', overview.get('destination', 'N/A')],
        ['Duration:', overview.get('duration', 'N/A')],
        ['Budget:', overview.get('total_budget', 'N/A')],
        ['Theme:', overview.get('theme', 'N/A')]
    ]
    
    table = Table(overview_data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # 每日行程
    daily_plans = itinerary.get('daily_itinerary', [])
    for day in daily_plans[:2]:  # 只显示前2天作为示例
        story.append(Paragraph(f"Day {day.get('day')} - {day.get('date')}", heading_style))
        story.append(Paragraph(day.get('theme', ''), styles['Normal']))
        story.append(Spacer(1, 12))
        
        for activity in day.get('activities', [])[:3]:  # 每天前3个活动
            story.append(Paragraph(
                f"• {activity.get('time')} - {activity.get('title')}", 
                styles['Normal']
            ))
        story.append(Spacer(1, 12))
    
    # 联系信息
    story.append(Spacer(1, 30))
    story.append(Paragraph("For support: support@myagentbooking.com", styles['Normal']))
    
    # 生成PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# === ICS日历生成 ===
def generate_ics_calendar(itinerary: Dict) -> str:
    """生成ICS日历文件"""
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyAgent Booking//Travel Itinerary//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:My Trip
X-WR-TIMEZONE:America/New_York
"""
    
    daily_plans = itinerary.get('daily_itinerary', [])
    
    for day in daily_plans:
        for activity in day.get('activities', []):
            # 解析时间
            date_str = day.get('date', '2024-03-15')
            time_str = activity.get('time', '09:00')
            
            try:
                start_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(hours=2)  # 默认2小时
                
                ics_content += f"""BEGIN:VEVENT
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{activity.get('title', 'Activity')}
DESCRIPTION:{activity.get('description', '')}
LOCATION:{activity.get('location', '')}
STATUS:CONFIRMED
END:VEVENT
"""
            except:
                continue
    
    ics_content += "END:VCALENDAR"
    return ics_content


# === 示例行程数据 ===
def get_sample_itinerary() -> Dict:
    """获取示例详细行程"""
    return {
        "trip_overview": {
            "destination": "Tokyo, Japan",
            "duration": "5 days",
            "total_budget": "$2,500",
            "theme": "Culture & Cuisine",
            "best_time": "Spring (Cherry Blossom) or Fall"
        },
        "daily_itinerary": [
            {
                "day": 1,
                "date": "2024-03-15",
                "theme": "Arrival & Shibuya Exploration",
                "activities": [
                    {
                        "time": "14:00",
                        "duration": "1h",
                        "title": "Hotel Check-in",
                        "description": "Check into Shibuya Hilton Hotel",
                        "location": "Shibuya Hilton",
                        "cost": "$0",
                        "type": "checkin",
                        "tips": "Early check-in available with advance notice"
                    },
                    {
                        "time": "16:00",
                        "duration": "2h",
                        "title": "Shibuya Crossing & Hachiko Statue",
                        "description": "Experience the world's busiest intersection",
                        "location": "Shibuya Station",
                        "cost": "$0",
                        "type": "sightseeing",
                        "tips": "Best photo time: evening when lights turn on"
                    },
                    {
                        "time": "19:00",
                        "duration": "1.5h",
                        "title": "Dinner at Shibuya Food Street",
                        "description": "Authentic Japanese cuisine",
                        "location": "Shibuya Center Gai",
                        "cost": "$50",
                        "type": "dining",
                        "tips": "Try Ichiran Ramen - famous chain"
                    }
                ],
                "meals": {
                    "breakfast": {"name": "In-flight meal", "cost": "$0"},
                    "lunch": {"name": "Airport food court", "cost": "$15"},
                    "dinner": {"name": "Ichiran Ramen", "cost": "$15"}
                },
                "total_cost": "$65",
                "notes": "Don't pack too much for Day 1 - jet lag adjustment"
            },
            {
                "day": 2,
                "date": "2024-03-16",
                "theme": "Traditional Culture Tour",
                "activities": [
                    {
                        "time": "09:00",
                        "duration": "3h",
                        "title": "Senso-ji Temple & Nakamise Street",
                        "description": "Visit Tokyo's oldest temple",
                        "location": "Asakusa",
                        "cost": "$30",
                        "type": "sightseeing",
                        "tips": "Arrive before 9 AM to avoid crowds"
                    },
                    {
                        "time": "13:00",
                        "duration": "2h",
                        "title": "Tokyo Skytree",
                        "description": "Observation deck at 350m height",
                        "location": "Sumida",
                        "cost": "$25",
                        "type": "sightseeing",
                        "tips": "Book fast track tickets online"
                    },
                    {
                        "time": "16:00",
                        "duration": "2h",
                        "title": "Akihabara Electric Town",
                        "description": "Anime, manga & electronics district",
                        "location": "Akihabara",
                        "cost": "$50",
                        "type": "shopping",
                        "tips": "Visit maid cafes for unique experience"
                    }
                ],
                "meals": {
                    "breakfast": {"name": "Hotel buffet", "cost": "$20"},
                    "lunch": {"name": "Tempura Tenya", "cost": "$12"},
                    "dinner": {"name": "Isomaru Suisan", "cost": "$40"}
                },
                "total_cost": "$177",
                "notes": "Akihabara is very lively at night"
            }
        ],
        "local_tips": [
            "Buy Suica/Pasmo IC card for transportation",
            "Convenience stores (konbini) are everywhere",
            "Tipping is not customary in Japan",
            "Learn basic phrases: Arigatou (thanks), Sumimasen (excuse me)"
        ]
    }


# === 渲染函数 ===
def render_hero():
    """渲染英雄区域"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">✈️ MyAgent Booking</h1>
        <p class="hero-subtitle">AI-Powered Premium Travel Experience</p>
        <p style="font-size: 1em; color: rgba(255, 255, 255, 0.8); margin-top: 16px;">
            Smart Planning • Best Prices • 24/7 Support • Auto Rebooking
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_google_login_button():
    """渲染Google登录按钮"""
    st.markdown("""
    <div style="text-align: center; margin: 40px 0;">
        <div class="google-btn" style="display: inline-flex;">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="24" height="24">
            <span>Continue with Google</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 模拟Google登录(实际需要OAuth)
    if st.button("🔐 Google Login (Demo)", use_container_width=True):
        st.session_state.user = {
            "email": "demo@gmail.com",
            "name": "Demo User",
            "avatar": "👤",
            "logged_in": True
        }
        st.success("✅ Logged in successfully!")
        st.balloons()
        time.sleep(1)
        st.rerun()


def render_daily_itinerary(itinerary: Dict):
    """渲染详细每日行程"""
    overview = itinerary.get('trip_overview', {})
    daily_plans = itinerary.get('daily_itinerary', [])
    
    # 行程概览
    st.markdown("### 🗺️ Trip Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📍 Destination", overview.get('destination', 'N/A'))
    with col2:
        st.metric("📅 Duration", overview.get('duration', 'N/A'))
    with col3:
        st.metric("💰 Budget", overview.get('total_budget', 'N/A'))
    with col4:
        st.metric("🎯 Theme", overview.get('theme', 'N/A'))
    
    st.markdown("---")
    
    # 每日行程
    for day in daily_plans:
        day_num = day.get('day', 1)
        date = day.get('date', '')
        theme = day.get('theme', '')
        
        st.markdown(f"""
        <div class="day-header">
            Day {day_num} - {date}<br>
            <small style="font-size: 0.6em; font-weight: 400; opacity: 0.9;">{theme}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # 时间线
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        
        type_icons = {
            "sightseeing": "🏛️", "dining": "🍽️", "shopping": "🛍️",
            "entertainment": "🎭", "checkin": "🏨", "transport": "🚇"
        }
        
        for activity in day.get('activities', []):
            icon = type_icons.get(activity.get('type', ''), "📍")
            
            st.markdown(f"""
            <div class="timeline-item">
                <div class="activity-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <span class="time-badge">{icon} {activity.get('time', '')}</span>
                            <span style="color: #999; margin-left: 12px; font-size: 0.95em;">⏱️ {activity.get('duration', '')}</span>
                        </div>
                        <span style="font-weight: 700; color: #667eea; font-size: 1.3em;">{activity.get('cost', '')}</span>
                    </div>
                    <h4 style="margin: 12px 0 8px 0; color: #333;">{activity.get('title', '')}</h4>
                    <p style="color: #666; margin: 8px 0; line-height: 1.6;">{activity.get('description', '')}</p>
                    <p style="color: #999; font-size: 0.95em; margin: 8px 0;">📍 {activity.get('location', '')}</p>
                    {f'<div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); padding: 12px 16px; border-radius: 12px; margin-top: 12px; border-left: 3px solid #667eea;"><small style="color: #667eea; font-weight: 600;">💡 Tip: {activity.get("tips", "")}</small></div>' if activity.get('tips') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 餐饮
        meals = day.get('meals', {})
        if meals:
            st.markdown("#### 🍽️ Daily Meals")
            mcol1, mcol2, mcol3 = st.columns(3)
            
            meal_icons = ["🌅", "☀️", "🌙"]
            meal_times = ["Breakfast", "Lunch", "Dinner"]
            meal_keys = ["breakfast", "lunch", "dinner"]
            
            for idx, (col, icon, time, key) in enumerate(zip([mcol1, mcol2, mcol3], meal_icons, meal_times, meal_keys)):
                meal = meals.get(key)
                if meal:
                    with col:
                        st.markdown(f"""
                        <div class="glass-card" style="padding: 20px; text-align: center; min-height: 180px;">
                            <div style="font-size: 2.5em; margin-bottom: 12px;">{icon}</div>
                            <h5 style="margin: 8px 0; color: #667eea;">{time}</h5>
                            <p style="margin: 8px 0;"><strong>{meal.get('name', 'N/A')}</strong></p>
                            <p style="color: #667eea; font-weight: 600; font-size: 1.2em; margin: 8px 0;">{meal.get('cost', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # 每日总结
        total = day.get('total_cost', '$0')
        notes = day.get('notes', '')
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(17, 153, 142, 0.1) 0%, rgba(56, 239, 125, 0.1) 100%); 
                    padding: 20px 24px; border-radius: 16px; margin: 24px 0; border-left: 4px solid #11998e;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="font-size: 1.1em;">💰 Daily Total:</strong>
                <span style="font-size: 1.8em; color: #11998e; font-weight: 700; font-family: 'Poppins', sans-serif;">{total}</span>
            </div>
            {f'<p style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(17, 153, 142, 0.2); color: #666;"><strong>📝 Note:</strong> {notes}</p>' if notes else ''}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)


# === 主应用 ===
def main():
    # 初始化会话状态
    if "user" not in st.session_state:
        st.session_state.user = None
    if "trip_plan" not in st.session_state:
        st.session_state.trip_plan = None
    if "payment_history" not in st.session_state:
        st.session_state.payment_history = []
    if "saved_cards" not in st.session_state:
        st.session_state.saved_cards = []
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False
    if "show_reschedule_demo" not in st.session_state:
        st.session_state.show_reschedule_demo = False
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard")
        
        # 用户信息
        if st.session_state.user and st.session_state.user.get('logged_in'):
            user = st.session_state.user
            st.markdown(f"""
            <div class="user-card">
                <div class="user-avatar">{user.get('avatar', '👤')}</div>
                <h3 style="margin: 8px 0; font-size: 1.3em;">{user.get('name', 'User')}</h3>
                <p style="margin: 4px 0; font-size: 0.95em; opacity: 0.9;">{user.get('email', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 24px; background: rgba(255,255,255,0.9); 
                        border-radius: 20px; margin-bottom: 20px;">
                <p style="font-size: 1.1em; color: #667eea; font-weight: 600; margin-bottom: 16px;">
                    🌟 Guest Mode Active
                </p>
                <p style="font-size: 0.95em; color: #666; line-height: 1.6;">
                    You can browse and plan trips. Login to book tickets and enable auto-rebooking.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            render_google_login_button()
        
        st.markdown("---")
        
        # 支付信息(仅登录用户)
        if st.session_state.user and st.session_state.user.get('logged_in'):
            with st.expander("💳 Payment Methods"):
                with st.form("add_card_form"):
                    card_num = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                    ccol1, ccol2 = st.columns(2)
                    with ccol1:
                        exp = st.text_input("Expiry", placeholder="MM/YY")
                    with ccol2:
                        cvv = st.text_input("CVV", placeholder="123", type="password")
                    holder = st.text_input("Cardholder", placeholder="JOHN DOE")
                    
                    if st.form_submit_button("💾 Save Card"):
                        if all([card_num, exp, cvv, holder]):
                            st.session_state.saved_cards.append({
                                "number": card_num,
                                "expiry": exp,
                                "cvv": cvv,
                                "holder": holder,
                                "last4": card_num[-4:]
                            })
                            st.success("✅ Card saved!")
                            st.rerun()
            
            # 支付历史
            if st.session_state.payment_history:
                st.markdown("#### 📜 Recent Payments")
                for payment in st.session_state.payment_history[-3:]:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                                padding: 12px 16px; border-radius: 12px; margin: 8px 0; border-left: 3px solid #667eea;'>
                        <small style="color: #999;">{payment.get('timestamp', '')[:10]}</small><br>
                        <strong style="font-size: 1.2em; color: #667eea;">${payment.get('amount', 0):.2f}</strong><br>
                        <small style="color: #999;">•••• {payment.get('card_last4', '****')}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Demo模式
        st.markdown("#### 🎭 Demo Features")
        demo = st.checkbox("Enable Demo Mode", value=st.session_state.demo_mode)
        st.session_state.demo_mode = demo
        
        if demo:
            st.info("Demo will simulate:\n- Flight delays\n- Auto-rebooking\n- Weather alerts")
    
    # 主内容区
    render_hero()
    
    # 查询输入
    st.markdown("### 🔍 Plan Your Trip")
    
    query_placeholder = """例如：
• Plan a 5-day trip to Tokyo from March 15-20
• 预算 $2500，喜欢文化和美食
• 住在涩谷区域"""
    
    query = st.text_area(
        "Describe your travel plans",
        placeholder=query_placeholder,
        height=120,
        label_visibility="collapsed"
    )
    
    bcol1, bcol2, bcol3, bcol4 = st.columns([3, 1, 1, 1])
    
    with bcol1:
        plan_btn = st.button("🚀 Generate Complete Plan", type="primary", use_container_width=True)
    with bcol2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.trip_plan = None
            st.session_state.show_reschedule_demo = False
            st.rerun()
    with bcol3:
        if st.button("🎭 Demo", use_container_width=True):
            st.session_state.demo_mode = True
            plan_btn = True
            query = "Plan a 5-day trip to Tokyo from March 15-20, budget $2500"
    with bcol4:
        if st.button("👁️ Guest", use_container_width=True):
            st.session_state.user = None
            plan_btn = True
            query = "Tokyo 3 days"
    
    # 生成计划
    if plan_btn and query:
        with st.status("🚀 Generating your perfect trip...", expanded=True) as status:
            try:
                st.write("🤖 Initializing AI Agent...")
                time.sleep(1)
                
                # 使用示例数据
                itinerary = get_sample_itinerary()
                
                st.write("🗺️ Planning detailed itinerary...")
                time.sleep(1)
                
                st.write("✅ Optimizing routes and prices...")
                time.sleep(1)
                
                st.session_state.trip_plan = {
                    "query": query,
                    "itinerary": itinerary,
                    "flights": [
                        {
                            "title": "EWR → NRT (United Airlines UA78)",
                            "price": "$850",
                            "route": "EWR-NRT",
                            "departure": "2024-03-15 11:00",
                            "arrival": "2024-03-16 14:30",
                            "duration": "13h 30m",
                            "link": "https://www.united.com/booking",
                            "notes": "Direct flight, meals included"
                        },
                        {
                            "title": "NRT → EWR (United Airlines UA79)",
                            "price": "$920",
                            "route": "NRT-EWR",
                            "departure": "2024-03-20 16:00",
                            "arrival": "2024-03-20 15:30",
                            "duration": "12h 30m",
                            "link": "https://www.united.com/booking",
                            "notes": "Return flight, entertainment system"
                        }
                    ],
                    "hotels": [
                        {
                            "title": "Shibuya Hilton Hotel (Luxury)",
                            "price": "$450/night",
                            "total": "$1,800",
                            "rating": "4.8",
                            "location": "Shibuya, Tokyo",
                            "amenities": "Pool, Spa, Restaurant, City View",
                            "link": "https://www.hilton.com/booking"
                        },
                        {
                            "title": "Hotel Mystays Asakusa (Comfort)",
                            "price": "$180/night",
                            "total": "$720",
                            "rating": "4.3",
                            "location": "Asakusa, Tokyo",
                            "amenities": "Free WiFi, Breakfast, Near Metro",
                            "link": "https://www.mystays.com/booking"
                        }
                    ]
                }
                
                status.update(label="✅ Trip plan ready!", state="complete")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
                status.update(label="❌ Failed", state="error")
    
    # 显示计划
    if st.session_state.trip_plan:
        plan = st.session_state.trip_plan
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 Daily Itinerary",
            "✈️ Flights & Hotels",
            "📥 Export & Share",
            "🎭 Simulations"
        ])
        
        with tab1:
            if plan.get('itinerary'):
                render_daily_itinerary(plan['itinerary'])
        
        with tab2:
            # Demo改签提醒
            if st.session_state.demo_mode and not st.session_state.show_reschedule_demo:
                time.sleep(2)
                st.session_state.show_reschedule_demo = True
                st.rerun()
            
            if st.session_state.show_reschedule_demo:
                st.markdown("""
                <div class="alert-card">
                    <h3 style="margin: 0 0 12px 0;">⚠️ Flight Delay Detected!</h3>
                    <p style="margin: 8px 0; font-size: 1.05em;">UA78 delayed by 3 hours. Auto-rebooking system activated...</p>
                    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.3);">
                        ✅ Alternative flight reserved<br>
                        ✅ Hotel notified of late arrival<br>
                        ✅ Email confirmation sent
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 🔄 Rebooking Options")
                
                options = [
                    {
                        "id": 1,
                        "title": "Next Available Direct Flight",
                        "flight": "UA456",
                        "time": "18:30 → 21:45+1",
                        "price_diff": "+$120",
                        "recommended": "✨ Fastest option"
                    },
                    {
                        "id": 2,
                        "title": "Tomorrow Morning Flight",
                        "flight": "UA789",
                        "time": "08:00 → 11:15+1",
                        "price_diff": "$0",
                        "hotel": "Free airport hotel included",
                        "recommended": "💰 Most economical"
                    },
                    {
                        "id": 3,
                        "title": "Full Refund",
                        "refund": "$850",
                        "processing": "3-5 business days",
                        "recommended": "📅 If not urgent"
                    }
                ]
                
                for opt in options:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #667eea;">
                        <h4 style="margin: 0 0 12px 0; color: #667eea;">Option {opt['id']}: {opt['title']}</h4>
                        <p style="color: #11998e; font-weight: 600; margin: 8px 0;">{opt['recommended']}</p>
                    """, unsafe_allow_html=True)
                    
                    if 'flight' in opt:
                        st.markdown(f"**Flight:** {opt['flight']} | **Time:** {opt['time']} | **Price:** {opt['price_diff']}")
                    if 'hotel' in opt:
                        st.info(opt['hotel'])
                    if 'refund' in opt:
                        st.markdown(f"**Refund:** {opt['refund']} | **Processing:** {opt['processing']}")
                    
                    if st.button(f"✅ Select Option {opt['id']}", key=f"rebook_{opt['id']}"):
                        st.success(f"✅ Confirmed! Confirmation email sent.")
                        st.balloons()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # 航班
            st.markdown("### ✈️ Flights")
            for idx, flight in enumerate(plan.get('flights', [])):
                st.markdown(f"""
                <div class="glass-card flight-card">
                    <h3 style="margin: 0 0 16px 0; color: #333;">{flight.get('title', '')}</h3>
                    <div class="price-badge">{flight.get('price', '')}</div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 20px 0;">
                        <div>
                            <strong style="color: #999; font-size: 0.9em;">DEPARTURE</strong><br>
                            <span style="font-size: 1.2em; color: #333;">{flight.get('departure', '')}</span>
                        </div>
                        <div>
                            <strong style="color: #999; font-size: 0.9em;">ARRIVAL</strong><br>
                            <span style="font-size: 1.2em; color: #333;">{flight.get('arrival', '')}</span>
                        </div>
                    </div>
                    <p style="color: #666; margin: 12px 0;"><strong>Duration:</strong> {flight.get('duration', '')}</p>
                    <p style="color: #666; margin: 12px 0;">{flight.get('notes', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                fcol1, fcol2 = st.columns(2)
                
                logged_in = st.session_state.user and st.session_state.user.get('logged_in')
                
                with fcol1:
                    if logged_in:
                        if st.button(f"💳 Pay ${flight.get('price', '').replace('$', '')}", 
                                   key=f"pay_flight_{idx}", 
                                   use_container_width=True):
                            if st.session_state.saved_cards:
                                with st.spinner("Processing payment..."):
                                    payment_sys = VirtualPaymentSystem()
                                    card = st.session_state.saved_cards[0]
                                    
                                    try:
                                        amount = float(flight.get('price', '$850').replace('$', '').replace(',', ''))
                                    except:
                                        amount = 850.0
                                    
                                    result = payment_sys.process_payment(card, amount, "flight", flight)
                                    
                                    if result["success"]:
                                        st.session_state.payment_history.append(result)
                                        st.success(f"✅ Payment successful! Confirmation: {result['confirmation_code']}")
                                        st.balloons()
                                        
                                        # 发送邮件
                                        try:
                                            email_service = get_email_service()
                                            email_service.send_email(
                                                st.session_state.user['email'],
                                                f"Booking Confirmation - {flight['title']}",
                                                f"Your booking is confirmed!\n\nConfirmation Code: {result['confirmation_code']}\nAmount: ${amount}"
                                            )
                                            st.success("📧 Confirmation email sent!")
                                        except:
                                            pass
                            else:
                                st.error("Please add a payment method first")
                    else:
                        st.warning("🔒 Login required to book")
                
                with fcol2:
                    st.link_button("🔗 View Details", flight.get('link', '#'), use_container_width=True)
            
            # 酒店
            st.markdown("### 🏨 Hotels")
            for idx, hotel in enumerate(plan.get('hotels', [])):
                st.markdown(f"""
                <div class="glass-card hotel-card">
                    <h3 style="margin: 0 0 16px 0; color: #333;">{hotel.get('title', '')}</h3>
                    <div style="display: flex; align-items: center; gap: 12px; margin: 12px 0;">
                        <span class="badge">⭐ {hotel.get('rating', 'N/A')}</span>
                        <span style="color: #999;">📍 {hotel.get('location', '')}</span>
                    </div>
                    <div class="price-badge">{hotel.get('price', '')}</div>
                    <p style="color: #11998e; font-size: 1.2em; font-weight: 600; margin: 8px 0;">Total: {hotel.get('total', '')}</p>
                    <p style="color: #666; margin: 12px 0;"><strong>Amenities:</strong> {hotel.get('amenities', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                hcol1, hcol2 = st.columns(2)
                
                with hcol1:
                    if logged_in:
                        if st.button(f"💳 Pay {hotel.get('total', '')}", 
                                   key=f"pay_hotel_{idx}", 
                                   use_container_width=True):
                            if st.session_state.saved_cards:
                                with st.spinner("Processing..."):
                                    payment_sys = VirtualPaymentSystem()
                                    card = st.session_state.saved_cards[0]
                                    
                                    try:
                                        amount = float(hotel.get('total', '$720').replace('$', '').replace(',', ''))
                                    except:
                                        amount = 720.0
                                    
                                    result = payment_sys.process_payment(card, amount, "hotel", hotel)
                                    
                                    if result["success"]:
                                        st.session_state.payment_history.append(result)
                                        st.success(f"✅ Booked! Confirmation: {result['confirmation_code']}")
                                        st.balloons()
                            else:
                                st.error("Please add a payment method")
                    else:
                        st.warning("🔒 Login required")
                
                with hcol2:
                    st.link_button("🔗 View Details", hotel.get('link', '#'), use_container_width=True)
        
        with tab3:
            st.markdown("### 📥 Export & Share Options")
            
            ecol1, ecol2, ecol3 = st.columns(3)
            
            with ecol1:
                st.markdown("""
                <div class="glass-card" style="text-align: center; padding: 24px;">
                    <div style="font-size: 3em; margin-bottom: 12px;">📄</div>
                    <h4>Download PDF</h4>
                    <p style="color: #666; font-size: 0.95em;">Get a beautiful PDF itinerary</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("📄 Generate PDF", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        pdf_buffer = generate_trip_pdf(
                            plan.get('itinerary', {}).get('trip_overview', {}),
                            plan.get('itinerary', {})
                        )
                        
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_buffer,
                            file_name=f"trip_itinerary_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("✅ PDF ready!")
            
            with ecol2:
                st.markdown("""
                <div class="glass-card" style="text-align: center; padding: 24px;">
                    <div style="font-size: 3em; margin-bottom: 12px;">📅</div>
                    <h4>Add to Calendar</h4>
                    <p style="color: #666; font-size: 0.95em;">Import to Google Calendar</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("📅 Generate ICS", use_container_width=True):
                    ics_content = generate_ics_calendar(plan.get('itinerary', {}))
                    
                    st.download_button(
                        label="⬇️ Download ICS",
                        data=ics_content,
                        file_name=f"trip_calendar_{datetime.datetime.now().strftime('%Y%m%d')}.ics",
                        mime="text/calendar",
                        use_container_width=True
                    )
                    st.success("✅ Calendar file ready!")
            
            with ecol3:
                st.markdown("""
                <div class="glass-card" style="text-align: center; padding: 24px;">
                    <div style="font-size: 3em; margin-bottom: 12px;">📧</div>
                    <h4>Email Itinerary</h4>
                    <p style="color: #666; font-size: 0.95em;">Send to your email</p>
                </div>
                """, unsafe_allow_html=True)
                
                if logged_in:
                    if st.button("📧 Send Email", use_container_width=True):
                        try:
                            email_service = get_email_service()
                            email_service.send_email(
                                st.session_state.user['email'],
                                "Your Trip Itinerary",
                                f"Your trip plan is ready!\n\nQuery: {plan.get('query', '')}"
                            )
                            st.success("✅ Email sent!")
                        except Exception as e:
                            st.error(f"Failed: {e}")
                else:
                    st.warning("🔒 Login required")
        
        with tab4:
            st.markdown("### 🎭 Demo Simulations")
            st.info("Demo mode shows how the system handles real-world scenarios")
            
            dcol1, dcol2 = st.columns(2)
            
            with dcol1:
                st.markdown("""
                <div class="glass-card">
                    <h4>✈️ Flight Delay Simulation</h4>
                    <p style="color: #666;">See automatic rebooking in action</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("▶️ Run Flight Delay Demo", use_container_width=True):
                    st.session_state.show_reschedule_demo = True
                    st.rerun()
            
            with dcol2:
                st.markdown("""
                <div class="glass-card">
                    <h4>🌦️ Weather Alert Simulation</h4>
                    <p style="color: #666;">Test weather monitoring system</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("▶️ Run Weather Demo", use_container_width=True):
                    st.markdown("""
                    <div class="alert-card">
                        <h4>🌦️ Weather Alert</h4>
                        <p>Heavy rain expected in Tokyo on Day 2</p>
                        <p style="margin-top: 12px;">
                            ✅ Itinerary adjusted<br>
                            ✅ Indoor alternatives suggested<br>
                            ✅ Email notification sent
                        </p>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
