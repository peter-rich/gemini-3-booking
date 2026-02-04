import streamlit as st
import json, re
from agents.agent import TravelAgent
from dotenv import load_dotenv

load_dotenv()

def main():
    st.title("🛡️ 深度链接锁定系统 (已修复)")
    
    query = st.text_input("描述行程", placeholder="3月10日从皮斯卡塔韦去东京...")

    if st.button("生成方案", type="primary") and query:
        agent = TravelAgent()
        with st.status("正在编排深度跳转链路...", expanded=True):
            try:
                response = agent.plan_trip(query).text
                
                # 提取 JSON
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                text_content = re.sub(r'```json.*?```', '', response, flags=re.DOTALL)

                # 展示行程
                st.markdown(text_content)

                if json_match:
                    try:
                        items = json.loads(json_match.group(1))
                        
                        # 核心修复：确保 items 是列表且不是字符串
                        if isinstance(items, list):
                            st.subheader("📍 深度跳转入口")
                            for item in items:
                                # 再次检查 item 是否为字典
                                if isinstance(item, dict):
                                    with st.container():
                                        st.markdown(f"""
                                        <div style="border:1px solid #333; padding:15px; border-radius:10px; margin-bottom:10px; background:#161b22;">
                                            <h4 style="color:#58a6ff;">{item.get('type', '未知')} - {item.get('title', '无标题')}</h4>
                                            <p style="color:#00ffaa; font-weight:bold;">价格: {item.get('price', '实时查询')}</p>
                                            <a href="{item.get('link', '#')}" target="_blank" 
                                               style="background:#238636; color:white; padding:8px 16px; border-radius:5px; text-decoration:none;">
                                               立即跳转订票 (已锁定参数) ➔
                                            </a>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.warning("AI 返回的数据格式不正确，无法生成跳转按钮。")
                    except json.JSONDecodeError:
                        st.error("JSON 解析失败，请重试。")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
