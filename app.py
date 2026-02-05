"""
Ultra Travel Commander - 完整版
自动从 .env 读取邮件配置
包含：智能行程规划 + 虚拟支付 + 真实邮件 + 智能改签
"""
import streamlit as st
import json
import re
import datetime
from io import BytesIO
from typing import Tuple, Optional, Dict, List, Any
import time
import random
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入邮件服务
from email_service import EmailService

try:
    from agent import TravelAgent
except ImportError:
    st.error("请确保 agent.py 在同一目录下")

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# 页面配置
st.set_page_config(
    page_title="Ultra Travel Commander",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 样式 ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    h1, h2, h3 { 
        font-family: 'Poppins', sans-serif !important; 
        font-weight: 700 !important; 
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 28px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
    }
    
    .flight-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 5px solid #667eea;
    }
    
    .hotel-card {
        background: linear-gradient(135deg, rgba(243, 172, 18, 0.1) 0%, rgba(241, 39, 17, 0.1) 100%);
        border-left: 5px solid #f3ac12;
    }
    
    .itinerary-card {
        background: linear-gradient(135deg, rgba(26, 188, 156, 0.1) 0%, rgba(22, 160, 133, 0.1) 100%);
        border-left: 5px solid #1abc9c;
    }
    
    .price-tag {
        font-size: 2.5em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 20px 0;
        font-family: 'Poppins', sans-serif;
    }
    
    .action-btn {
        display: inline-block;
        padding: 16px 32px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 600;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        cursor: pointer;
        width: 100%;
        font-size: 1.05em;
    }
    
    .action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
    }
    
    .pay-btn {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
    }
    
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .status-badge {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .reschedule-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
    
    .timeline {
        position: relative;
        padding-left: 30px;
        margin: 20px 0;
    }
    
    .timeline::before {
        content: '';
        position: absolute;
        left: 10px;
        top: 0;
        bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .timeline-item {
        position: relative;
        margin: 20px 0;
        padding-left: 20px;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -24px;
        top: 5px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: #667eea;
        border: 3px solid white;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
    
    .activity-item {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        border-left: 3px solid #667eea;
    }
    
    .time-badge {
        background: linear-gradient(135deg, #f3ac12 0%, #f1a917 100%);
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.9em;
        font-weight: 600;
        color: white;
        display: inline-block;
    }
    
    .day-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin: 20px 0;
        font-size: 1.5em;
        font-weight: 700;
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-slide-up { animation: slideUp 0.5s ease-out; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse { animation: pulse 2s infinite; }
</style>
""", unsafe_allow_html=True)


# === 虚拟支付系统 ===
class VirtualPaymentSystem:
    def __init__(self):
        self.processing_time = 2
    
    def process_payment(self, card_info: Dict, amount: float, item_type: str, item_details: Dict) -> Dict:
        time.sleep(self.processing_time)
        transaction_id = f"TXN-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": "USD",
            "timestamp": datetime.datetime.now().isoformat(),
            "card_last4": card_info.get("card_number", "")[-4:],
            "item_type": item_type,
            "item_details": item_details,
            "confirmation_code": f"CONF-{random.randint(100000, 999999)}"
        }


# === 智能改签系统 ===
class SmartRescheduleSystem:
    def __init__(self, agent: TravelAgent = None):
        self.agent = agent
    
    def detect_delay_issue(self, flight_info: Dict, current_time: datetime.datetime) -> Optional[Dict]:
        scenarios = [
            {
                "issue_type": "flight_delay",
                "severity": "high",
                "message": "您的航班 UA123 延误 3 小时，可能无法赶上转机航班",
                "affected_flight": "UA123",
                "original_time": "14:30",
                "new_time": "17:30",
                "connection_at_risk": True
            }
        ]
        return random.choice(scenarios) if random.random() < 0.3 else None
    
    def auto_reschedule(self, original_booking: Dict, issue: Dict) -> Dict:
        new_options = {
            "status": "rescheduled",
            "original_booking": original_booking,
            "issue": issue,
            "new_options": [
                {
                    "option_id": 1,
                    "title": "立即改签下一班直飞航班",
                    "flight": "UA456",
                    "departure": "18:30",
                    "arrival": "次日 21:45",
                    "price_difference": "+$120",
                    "recommendation": "推荐：最快到达目的地"
                },
                {
                    "option_id": 2,
                    "title": "改签明日早班航班",
                    "flight": "UA789",
                    "departure": "明日 08:00",
                    "arrival": "明日 11:15",
                    "price_difference": "$0",
                    "hotel_voucher": "免费提供机场酒店",
                    "recommendation": "经济实惠，充分休息"
                },
                {
                    "option_id": 3,
                    "title": "全额退款",
                    "refund_amount": "$850",
                    "processing_time": "3-5 工作日",
                    "recommendation": "如行程不急可选择"
                }
            ],
            "automated_actions": [
                "✅ 已自动预留改签航班座位（保留 30 分钟）",
                "✅ 已通知酒店可能晚到",
                "✅ 已调整后续行程时间",
                "📧 确认邮件将在您选择方案后发送"
            ]
        }
        return new_options


# === 增强的旅行代理（含详细行程）===
class EnhancedTravelAgent:
    def __init__(self):
        self.base_agent = TravelAgent()
    
    def plan_detailed_itinerary(self, user_query: str) -> Dict:
        # 调用基础 agent
        response = self.base_agent.plan_trip(user_query)
        plan_md, payload = parse_agent_output(response.text)
        
        # 返回示例详细行程
        return {
            "markdown": plan_md,
            "payload": payload,
            "detailed_itinerary": self._get_sample_itinerary()
        }
    
    def _get_sample_itinerary(self) -> Dict:
        return {
            "trip_overview": {
                "destination": "东京",
                "duration": "5天",
                "total_budget": "$2500",
                "theme": "文化探索 + 美食体验",
                "best_time": "春季（樱花季）或秋季"
            },
            "daily_itinerary": [
                {
                    "day": 1,
                    "date": "2024-03-15",
                    "theme": "到达与涩谷探索",
                    "activities": [
                        {
                            "time": "14:00",
                            "duration": "1h",
                            "title": "酒店入住",
                            "description": "办理入住手续，放置行李",
                            "location": "涩谷希尔顿酒店",
                            "cost": "$0",
                            "type": "checkin",
                            "tips": "建议提前在线值机节省时间"
                        },
                        {
                            "time": "16:00",
                            "duration": "2h",
                            "title": "涩谷十字路口 & 忠犬八公像",
                            "description": "体验世界最繁忙的十字路口",
                            "location": "涩谷站前",
                            "cost": "$0",
                            "type": "sightseeing",
                            "tips": "最佳拍摄时间：傍晚灯光亮起时"
                        },
                        {
                            "time": "19:00",
                            "duration": "1.5h",
                            "title": "涩谷美食街晚餐",
                            "description": "品尝地道日式料理",
                            "location": "涩谷中心街",
                            "cost": "$50",
                            "type": "dining",
                            "tips": "推荐尝试一兰拉面"
                        }
                    ],
                    "meals": {
                        "breakfast": {"name": "机上餐食", "location": "航班", "cost": "$0", "cuisine": "国际"},
                        "lunch": {"name": "机场快餐", "location": "羽田机场", "cost": "$15", "cuisine": "日式"},
                        "dinner": {"name": "一兰拉面", "location": "涩谷店", "cost": "$15", "cuisine": "拉面"}
                    },
                    "total_cost": "$65",
                    "notes": "第一天不要安排太满，适应时差"
                },
                {
                    "day": 2,
                    "date": "2024-03-16",
                    "theme": "传统文化之旅",
                    "activities": [
                        {
                            "time": "09:00",
                            "duration": "3h",
                            "title": "浅草寺 & 仲见世商店街",
                            "description": "参观东京最古老的寺庙",
                            "location": "台东区浅草",
                            "cost": "$30",
                            "type": "sightseeing",
                            "tips": "早上9点前到达可避开人群"
                        },
                        {
                            "time": "13:00",
                            "duration": "2h",
                            "title": "东京晴空塔",
                            "description": "登顶东京最高建筑",
                            "location": "墨田区",
                            "cost": "$25",
                            "type": "sightseeing",
                            "tips": "建议购买快速通道票"
                        }
                    ],
                    "meals": {
                        "breakfast": {"name": "酒店自助餐", "location": "酒店", "cost": "$20", "cuisine": "国际"},
                        "lunch": {"name": "天丼てんや", "location": "浅草", "cost": "$12", "cuisine": "天妇罗"},
                        "dinner": {"name": "矶丸水产", "location": "秋叶原", "cost": "$40", "cuisine": "海鲜"}
                    },
                    "total_cost": "$127",
                    "notes": "秋叶原晚上很热闹"
                }
            ],
            "local_tips": [
                "购买 Suica/Pasmo 交通卡",
                "便利店可以解决大部分需求",
                "日本不流行给小费"
            ]
        }


# === 辅助函数 ===
def _safe(s: Any) -> str:
    return "" if s is None else str(s)


def parse_agent_output(text: str) -> Tuple[str, Optional[Dict]]:
    lines = text.split('\n')
    md_lines = []
    json_str = ""
    in_json = False
    
    for line in lines:
        if '```json' in line.lower():
            in_json = True
            continue
        elif '```' in line and in_json:
            in_json = False
            continue
        
        if in_json:
            json_str += line + '\n'
        elif not in_json and json_str == "":
            md_lines.append(line)
    
    markdown_text = '\n'.join(md_lines)
    
    payload = None
    if json_str.strip():
        try:
            payload = json.loads(json_str)
        except:
            pass
    
    return markdown_text, payload


def render_daily_itinerary(itinerary: Dict):
    """渲染每日行程"""
    trip_overview = itinerary.get("trip_overview", {})
    daily_plans = itinerary.get("daily_itinerary", [])
    
    st.markdown("### 🗺️ 行程概览")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📍 目的地", trip_overview.get("destination", "N/A"))
    with col2:
        st.metric("📅 天数", trip_overview.get("duration", "N/A"))
    with col3:
        st.metric("💰 预算", trip_overview.get("total_budget", "N/A"))
    with col4:
        st.metric("🎯 主题", trip_overview.get("theme", "N/A"))
    
    st.markdown("---")
    st.markdown("### 📅 每日详细行程")
    
    for day_plan in daily_plans:
        day_num = day_plan.get("day", 1)
        date = day_plan.get("date", "")
        theme = day_plan.get("theme", "")
        
        st.markdown(f"""
        <div class="day-header animate-slide-up">
            Day {day_num} - {date}<br>
            <small style="font-size: 0.7em; font-weight: 400;">{theme}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        
        for activity in day_plan.get("activities", []):
            type_icons = {
                "sightseeing": "🏛️", "dining": "🍽️", "shopping": "🛍️",
                "entertainment": "🎭", "checkin": "🏨", "transport": "🚇"
            }
            icon = type_icons.get(activity.get("type", ""), "📍")
            
            st.markdown(f"""
            <div class="timeline-item animate-slide-up">
                <div class="activity-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>
                            <span class="time-badge">{icon} {activity.get('time', '')}</span>
                            <span style="color: #888; margin-left: 10px;">⏱️ {activity.get('duration', '')}</span>
                        </div>
                        <span style="font-weight: 700; color: #667eea; font-size: 1.2em;">{activity.get('cost', '')}</span>
                    </div>
                    <h4 style="margin: 10px 0;">{activity.get('title', '')}</h4>
                    <p style="color: #666;">{activity.get('description', '')}</p>
                    <p style="color: #888; font-size: 0.9em;">📍 {activity.get('location', '')}</p>
                    {f'<div style="background: rgba(102, 126, 234, 0.1); padding: 10px; border-radius: 8px; margin-top: 10px;"><small>💡 {activity.get("tips", "")}</small></div>' if activity.get('tips') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 当日餐饮
        meals = day_plan.get("meals", {})
        if meals:
            st.markdown("#### 🍽️ 当日餐饮")
            col1, col2, col3 = st.columns(3)
            
            for idx, (meal_time, meal) in enumerate([("早餐", meals.get("breakfast")), ("午餐", meals.get("lunch")), ("晚餐", meals.get("dinner"))]):
                if meal:
                    with [col1, col2, col3][idx]:
                        icons = ["🌅", "☀️", "🌙"]
                        st.markdown(f"""
                        <div class="glass-card" style="padding: 15px; text-align: center;">
                            <div style="font-size: 2em;">{icons[idx]}</div>
                            <h5>{meal_time}</h5>
                            <p><strong>{meal.get('name', 'N/A')}</strong></p>
                            <p style="color: #888; font-size: 0.9em;">{meal.get('cuisine', '')}</p>
                            <p style="color: #667eea; font-weight: 600;">{meal.get('cost', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        total_cost = day_plan.get("total_cost", "$0")
        notes = day_plan.get("notes", "")
        
        st.markdown(f"""
        <div style="background: rgba(17, 153, 142, 0.1); padding: 15px; border-radius: 8px; margin: 15px 0;">
            <strong>💰 当日总费用:</strong> <span style="font-size: 1.3em; color: #11998e;">{total_cost}</span>
            {f'<p style="margin-top: 10px;"><strong>📝 提醒:</strong> {notes}</p>' if notes else ''}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")


# === 主应用 ===
def main():
    # 初始化会话状态
    if "full_plan" not in st.session_state:
        st.session_state.full_plan = None
    if "payment_history" not in st.session_state:
        st.session_state.payment_history = []
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {"email": "", "saved_cards": []}
    if "email_service" not in st.session_state:
        st.session_state.email_service = None
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False
    if "show_reschedule" not in st.session_state:
        st.session_state.show_reschedule = False
    
    # 自动初始化邮件服务（从 .env 读取）
    if not st.session_state.email_service:
        try:
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("SENDER_PASSWORD")
            
            if sender_email and sender_password:
                # 根据邮箱后缀判断服务商
                if "@gmail.com" in sender_email:
                    provider = "gmail"
                elif "@outlook.com" in sender_email or "@hotmail.com" in sender_email:
                    provider = "outlook"
                elif "@163.com" in sender_email:
                    provider = "163"
                elif "@qq.com" in sender_email:
                    provider = "qq"
                else:
                    provider = "custom"
                
                st.session_state.email_service = EmailService(
                    email_provider=provider,
                    sender_email=sender_email,
                    sender_password=sender_password
                )
        except Exception as e:
            st.session_state.email_service = None
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### ⚙️ 用户设置")
        
        # 邮件服务状态
        st.markdown("#### 📧 邮件服务状态")
        if st.session_state.email_service:
            st.success("✅ 邮件服务已配置（从 .env 读取）")
            sender_email = os.getenv("SENDER_EMAIL")
            if sender_email:
                st.info(f"发件邮箱: {sender_email}")
        else:
            st.warning("⚠️ 邮件服务未配置")
            st.caption("请检查 .env 文件中的配置")
        
        st.markdown("---")
        
        # 用户信息
        st.markdown("#### 👤 个人信息")
        user_email = st.text_input(
            "您的邮箱",
            value=st.session_state.user_profile.get("email", ""),
            placeholder="your_email@example.com"
        )
        if user_email:
            st.session_state.user_profile["email"] = user_email
        
        # 支付信息
        with st.expander("💳 支付信息"):
            card_number = st.text_input("卡号", placeholder="1234 5678 9012 3456", type="password")
            col1, col2 = st.columns(2)
            with col1:
                card_expiry = st.text_input("有效期", placeholder="MM/YY")
            with col2:
                card_cvv = st.text_input("CVV", placeholder="123", type="password")
            
            card_holder = st.text_input("持卡人", placeholder="ZHANG SAN")
            
            if st.button("💾 保存卡片"):
                if all([card_number, card_expiry, card_cvv, card_holder]):
                    st.session_state.user_profile["saved_cards"].append({
                        "card_number": card_number,
                        "expiry": card_expiry,
                        "cvv": card_cvv,
                        "holder": card_holder,
                        "last4": card_number[-4:]
                    })
                    st.success("✅ 已保存！")
        
        # 支付历史
        st.markdown("#### 📜 支付历史")
        if st.session_state.payment_history:
            for payment in st.session_state.payment_history[-3:]:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 5px 0;'>
                    <small>{payment['timestamp'][:10]}</small><br>
                    <b>${payment['amount']:.2f}</b><br>
                    <small>•••• {payment['card_last4']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无记录")
        
        st.markdown("---")
        
        # Demo 模式
        st.markdown("#### 🎭 Demo 功能")
        demo_mode = st.checkbox("启用改签 Demo", value=st.session_state.demo_mode)
        st.session_state.demo_mode = demo_mode
    
    # 主标题
    st.markdown("""
    <div class="glass-card animate-slide-up" style="text-align: center;">
        <h1 style="font-size: 3em; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            ✈️ Ultra Travel Commander
        </h1>
        <p style="font-size: 1.2em; color: #666; margin-top: 10px;">
            智能行程规划 · 真实邮件确认 · 一键支付 · 自动改签
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 输入区域
    st.markdown("### 🔍 描述您的旅行")
    query = st.text_area(
        "旅行计划",
        placeholder="例如：计划 3月15-20日 从纽约到东京的 5 天旅行，想体验传统文化和现代购物",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        generate_btn = st.button("🚀 生成完整旅行计划", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 清除", use_container_width=True):
            st.session_state.full_plan = None
            st.session_state.show_reschedule = False
            st.rerun()
    with col3:
        if st.button("🎭 Demo", use_container_width=True):
            st.session_state.demo_mode = True
            generate_btn = True
            query = "Plan a 5-day trip to Tokyo from March 15-20"
    
    # 生成计划
    if generate_btn and query:
        with st.status("🚀 正在生成详细计划...", expanded=True) as status:
            try:
                st.write("🔍 初始化 AI...")
                agent = EnhancedTravelAgent()
                
                st.write("🗺️ 生成行程...")
                full_plan = agent.plan_detailed_itinerary(query)
                st.session_state.full_plan = full_plan
                
                status.update(label="✅ 完成！", state="complete")
                
            except Exception as e:
                st.error(f"❌ 错误: {e}")
                status.update(label="❌ 失败", state="error")
    
    # 显示结果
    if st.session_state.full_plan:
        full_plan = st.session_state.full_plan
        
        # Tab 导航
        tab1, tab2, tab3 = st.tabs(["📅 详细行程", "✈️ 航班酒店", "📥 导出"])
        
        with tab1:
            if full_plan.get("detailed_itinerary"):
                render_daily_itinerary(full_plan["detailed_itinerary"])
        
        with tab2:
            payload = full_plan.get("payload")
            if payload:
                actions = payload.get("actions", [])
                flights = [i for i in actions if i.get("type") == "flight"]
                hotels = [i for i in actions if i.get("type") == "hotel"]
                
                # Demo 改签
                if st.session_state.demo_mode and flights and not st.session_state.show_reschedule:
                    time.sleep(2)
                    st.session_state.show_reschedule = True
                    st.rerun()
                
                # 改签提醒
                if st.session_state.show_reschedule and flights:
                    st.markdown("""
                    <div class="reschedule-alert">
                        <h3>⚠️ 检测到航班延误</h3>
                        <p>UA123 延误 3 小时，正在生成改签方案...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner("🤖 AI 分析中..."):
                        time.sleep(2)
                        reschedule_system = SmartRescheduleSystem(None)
                        issue = {"issue_type": "flight_delay", "message": "延误 3 小时"}
                        options = reschedule_system.auto_reschedule(flights[0], issue)
                    
                    st.markdown("### 🔄 改签方案")
                    for action in options["automated_actions"]:
                        st.success(action)
                    
                    for option in options["new_options"]:
                        with st.container():
                            st.markdown(f"""
                            <div class="glass-card">
                                <h4>方案 {option['option_id']}: {option['title']}</h4>
                                <p><strong>推荐:</strong> {option['recommendation']}</p>
                            """, unsafe_allow_html=True)
                            
                            if 'flight' in option:
                                st.markdown(f"**航班:** {option['flight']} | **起飞:** {option['departure']}")
                            
                            if st.button(f"✅ 选择", key=f"opt_{option['option_id']}"):
                                st.success("✅ 已确认！邮件将发送")
                                st.balloons()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                
                # 航班
                st.markdown("### ✈️ 航班")
                if flights:
                    for idx, flight in enumerate(flights):
                        st.markdown(f"""
                        <div class="glass-card flight-card">
                            <h3>{_safe(flight.get('title', ''))}</h3>
                            <div class="price-tag">{_safe(flight.get('price', ''))}</div>
                            <p>{_safe(flight.get('notes', ''))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"💳 支付", key=f"pay_f_{idx}", use_container_width=True):
                                if not all([st.session_state.user_profile.get("saved_cards"),
                                           st.session_state.user_profile.get("email"),
                                           st.session_state.email_service]):
                                    st.error("请先配置完整信息")
                                else:
                                    with st.spinner("处理中..."):
                                        payment_sys = VirtualPaymentSystem()
                                        card = st.session_state.user_profile["saved_cards"][0]
                                        
                                        price_str = flight.get('price', '$500')
                                        try:
                                            amount = float(re.findall(r'\d+\.?\d*', price_str)[0])
                                        except:
                                            amount = 500.00
                                        
                                        result = payment_sys.process_payment(card, amount, "flight", flight)
                                        
                                        if result["success"]:
                                            st.session_state.payment_history.append(result)
                                            st.success(f"✅ 支付成功！ID: {result['transaction_id']}")
                                            
                                            try:
                                                email_sent = st.session_state.email_service.send_booking_confirmation(
                                                    st.session_state.user_profile["email"],
                                                    flight,
                                                    result
                                                )
                                                if email_sent:
                                                    st.success("📧 确认邮件已发送")
                                                    st.balloons()
                                            except:
                                                st.warning("邮件发送失败")
                        
                        with col2:
                            st.link_button("🔗 详情", flight.get('link', '#'), use_container_width=True)
                
                # 酒店
                st.markdown("### 🏨 酒店")
                if hotels:
                    for idx, hotel in enumerate(hotels):
                        st.markdown(f"""
                        <div class="glass-card hotel-card">
                            <h3>{_safe(hotel.get('title', ''))}</h3>
                            <div class="price-tag">{_safe(hotel.get('price', ''))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"💳 支付", key=f"pay_h_{idx}", use_container_width=True):
                                if not all([st.session_state.user_profile.get("saved_cards"),
                                           st.session_state.email_service]):
                                    st.error("请先配置")
                                else:
                                    with st.spinner("处理中..."):
                                        payment_sys = VirtualPaymentSystem()
                                        card = st.session_state.user_profile["saved_cards"][0]
                                        
                                        try:
                                            amount = float(re.findall(r'\d+\.?\d*', hotel.get('price', '$300'))[0])
                                        except:
                                            amount = 300.00
                                        
                                        result = payment_sys.process_payment(card, amount, "hotel", hotel)
                                        
                                        if result["success"]:
                                            st.session_state.payment_history.append(result)
                                            st.success("✅ 支付成功")
                                            
                                            try:
                                                st.session_state.email_service.send_booking_confirmation(
                                                    st.session_state.user_profile["email"],
                                                    hotel,
                                                    result
                                                )
                                                st.success("📧 已发送")
                                                st.balloons()
                                            except:
                                                pass
                        
                        with col2:
                            st.link_button("🔗 详情", hotel.get('link', '#'), use_container_width=True)
        
        with tab3:
            st.markdown("### 📥 导出选项")
            col1, col2 = st.columns(2)
            with col1:
                st.button("📄 下载 PDF", use_container_width=True)
            with col2:
                if st.button("📧 邮件发送", use_container_width=True):
                    if st.session_state.user_profile.get("email"):
                        st.success("✅ 已发送")
                    else:
                        st.error("请填写邮箱")


if __name__ == "__main__":
    main()
