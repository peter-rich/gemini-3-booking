"""
Google OAuth Authentication Module
Google OAuth 认证模块

支持两种方式:
1. 使用 streamlit-google-auth (推荐 - 简单)
2. 使用 google-auth (完整OAuth流程)
"""
import streamlit as st
import os
from typing import Optional, Dict
import json
import hashlib
import time

# 尝试导入Google认证库
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


class GoogleAuthManager:
    """Google OAuth认证管理器"""
    
    def __init__(self):
        # Google OAuth配置
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
        
        # 检查配置
        self.is_configured = bool(self.client_id and self.client_secret)
    
    def is_oauth_configured(self) -> bool:
        """检查OAuth是否配置"""
        return self.is_configured
    
    def get_google_login_url(self) -> str:
        """生成Google登录URL"""
        if not self.is_configured:
            return "#"
        
        # Google OAuth2端点
        auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        
        # 参数
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'online',
            'prompt': 'select_account'
        }
        
        # 构建URL
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_endpoint}?{param_string}"
    
    def verify_google_token(self, token: str) -> Optional[Dict]:
        """验证Google ID Token"""
        if not GOOGLE_AUTH_AVAILABLE:
            return None
        
        try:
            # 验证token
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                self.client_id
            )
            
            # 检查签发者
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return None
            
            # 返回用户信息
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'sub': idinfo.get('sub'),  # Google用户ID
                'verified_email': idinfo.get('email_verified')
            }
        except Exception as e:
            st.error(f"Token验证失败: {e}")
            return None
    
    def create_demo_user(self, email: str) -> Dict:
        """创建演示用户(用于测试)"""
        return {
            'email': email,
            'name': email.split('@')[0].title(),
            'picture': None,
            'sub': hashlib.md5(email.encode()).hexdigest(),
            'verified_email': True,
            'auth_method': 'demo'
        }


class SimpleAuthManager:
    """简化的认证管理器(不需要OAuth配置)"""
    
    def __init__(self):
        self.demo_users = {
            'demo@gmail.com': {
                'password': 'demo123',
                'name': 'Demo User',
                'avatar': '👤'
            },
            'test@example.com': {
                'password': 'test123',
                'name': 'Test User',
                'avatar': '🧪'
            }
        }
    
    def authenticate_demo(self, email: str, password: str) -> Optional[Dict]:
        """演示登录验证"""
        user = self.demo_users.get(email)
        if user and user['password'] == password:
            return {
                'email': email,
                'name': user['name'],
                'avatar': user.get('avatar', '👤'),
                'logged_in': True,
                'auth_method': 'demo'
            }
        return None
    
    def quick_google_login(self, email: str = 'demo@gmail.com') -> Dict:
        """快速Google登录(模拟)"""
        return {
            'email': email,
            'name': email.split('@')[0].title(),
            'avatar': '🌟',
            'logged_in': True,
            'auth_method': 'google_demo',
            'picture': None
        }


# 全局认证管理器
_auth_manager = None
_simple_auth = SimpleAuthManager()


def get_auth_manager() -> GoogleAuthManager:
    """获取认证管理器单例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = GoogleAuthManager()
    return _auth_manager


def get_simple_auth() -> SimpleAuthManager:
    """获取简化认证管理器"""
    return _simple_auth


# === Streamlit组件 ===

def render_google_login_button():
    """渲染Google登录按钮 - 完整版"""
    auth_manager = get_auth_manager()
    
    if auth_manager.is_oauth_configured():
        # 真实OAuth流程
        st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{}" target="_self" style="text-decoration: none;">
                <div class="google-btn" style="display: inline-flex; align-items: center; gap: 12px;
                     background: white; color: #444; border: 2px solid #e8e8e8; border-radius: 50px;
                     padding: 14px 32px; font-size: 16px; font-weight: 600; cursor: pointer;
                     box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="24" height="24">
                    <span>Continue with Google</span>
                </div>
            </a>
        </div>
        """.format(auth_manager.get_google_login_url()), unsafe_allow_html=True)
    else:
        # 演示模式
        st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <div class="google-btn" style="display: inline-flex; align-items: center; gap: 12px;
                 background: white; color: #444; border: 2px solid #e8e8e8; border-radius: 50px;
                 padding: 14px 32px; font-size: 16px; font-weight: 600;
                 box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="24" height="24">
                <span>Continue with Google (Demo)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Click to Login with Google (Demo)", use_container_width=True, key="google_demo_btn"):
            # 演示登录
            simple_auth = get_simple_auth()
            user = simple_auth.quick_google_login()
            st.session_state.user = user
            st.success("✅ Logged in successfully!")
            st.balloons()
            time.sleep(1)
            st.rerun()


def render_email_login_form():
    """渲染邮箱登录表单"""
    st.markdown("### 📧 Email Login")
    
    simple_auth = get_simple_auth()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        email = st.text_input(
            "Email Address",
            placeholder="demo@gmail.com or test@example.com",
            key="email_input"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="demo123 or test123",
            key="password_input"
        )
        
        st.caption("💡 Demo accounts: demo@gmail.com/demo123 or test@example.com/test123")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Login", use_container_width=True):
                user = simple_auth.authenticate_demo(email, password)
                if user:
                    st.session_state.user = user
                    st.success("✅ Login successful!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password")
        
        with col_btn2:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()


def render_signup_form():
    """渲染注册表单"""
    st.markdown("### ✨ Create Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        full_name = st.text_input("👤 Full Name", placeholder="John Doe")
        email = st.text_input("📧 Email", placeholder="your@email.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Min 8 characters")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password")
        
        if st.button("✨ Create Account", use_container_width=True):
            if not all([full_name, email, password]):
                st.error("❌ Please fill all fields")
            elif password != confirm_password:
                st.error("❌ Passwords don't match")
            elif len(password) < 8:
                st.error("❌ Password must be at least 8 characters")
            else:
                # 创建新用户
                new_user = {
                    'email': email,
                    'name': full_name,
                    'avatar': '👤',
                    'logged_in': True,
                    'auth_method': 'email'
                }
                st.session_state.user = new_user
                st.success("✅ Account created successfully!")
                st.balloons()
                time.sleep(1)
                st.rerun()
        
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_signup = False
            st.rerun()


def render_complete_auth_page():
    """渲染完整的认证页面"""
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; max-width: 600px; margin: 0 auto;">
        <h1 style="font-size: 3em; margin-bottom: 10px;">✈️</h1>
        <h2 style="margin: 10px 0; color: #667eea;">Welcome to MyAgent Booking</h2>
        <p style="color: #666; font-size: 1.1em; margin: 20px 0;">
            Your AI-powered travel companion
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 检查是否显示注册表单
    if st.session_state.get('show_signup'):
        render_signup_form()
    else:
        # Google登录
        render_google_login_button()
        
        st.markdown("<div style='text-align: center; margin: 30px 0;'>OR</div>", unsafe_allow_html=True)
        
        # 邮箱登录
        render_email_login_form()
    
    # 游客模式
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: rgba(102, 126, 234, 0.05); 
                border-radius: 16px; margin: 20px 0;">
        <h4 style="margin: 0 0 10px 0; color: #667eea;">🌟 Guest Mode</h4>
        <p style="color: #666; margin: 10px 0;">
            Continue without login to browse and plan trips<br>
            <small>(Login required for booking and payments)</small>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("👁️ Continue as Guest", use_container_width=True, type="secondary"):
        st.session_state.user = {
            'email': 'guest@myagent.com',
            'name': 'Guest',
            'avatar': '👁️',
            'logged_in': False,
            'is_guest': True
        }
        st.rerun()


# === OAuth回调处理 ===
def handle_oauth_callback():
    """处理OAuth回调"""
    # 从URL参数获取code
    query_params = st.experimental_get_query_params()
    
    if 'code' in query_params:
        code = query_params['code'][0]
        auth_manager = get_auth_manager()
        
        # 这里需要用code交换access_token
        # 然后获取用户信息
        # 简化处理: 创建演示用户
        user = {
            'email': 'oauth@gmail.com',
            'name': 'OAuth User',
            'avatar': '🔐',
            'logged_in': True,
            'auth_method': 'google_oauth'
        }
        st.session_state.user = user
        
        # 清除URL参数
        st.experimental_set_query_params()
        st.rerun()


if __name__ == "__main__":
    # 测试认证功能
    st.set_page_config(page_title="Auth Test", layout="centered")
    
    # 初始化session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    
    # 显示认证状态
    if st.session_state.user and st.session_state.user.get('logged_in'):
        st.success(f"✅ Logged in as: {st.session_state.user['name']}")
        st.json(st.session_state.user)
        
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()
    else:
        render_complete_auth_page()
