"""
Ride Booking UI Component for Streamlit
打车预订界面组件
"""
import streamlit as st
from rebooking_and_rides import RideHailingIntegration


def render_ride_booking_widget(trip_data: dict):
    """
    渲染打车预订组件
    
    Args:
        trip_data: 行程数据,包含pickup和dropoff信息
    """
    st.markdown("### 🚖 打车服务")
    
    ride_service = RideHailingIntegration()
    
    # 输入起点和终点
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📍 上车地点**")
        pickup_address = st.text_input(
            "起点地址",
            value=trip_data.get('pickup_address', 'Piscataway, NJ'),
            key="pickup_addr"
        )
        
        # 如果有经纬度可以输入
        with st.expander("高级选项: 指定坐标"):
            pickup_lat = st.number_input("纬度", value=40.5548, key="pickup_lat")
            pickup_lon = st.number_input("经度", value=-74.4605, key="pickup_lon")
    
    with col2:
        st.markdown("**🎯 目的地**")
        dropoff_address = st.text_input(
            "终点地址",
            value=trip_data.get('dropoff_address', 'Newark Airport (EWR)'),
            key="dropoff_addr"
        )
        
        with st.expander("高级选项: 指定坐标"):
            dropoff_lat = st.number_input("纬度", value=40.6895, key="dropoff_lat")
            dropoff_lon = st.number_input("经度", value=-74.1745, key="dropoff_lon")
    
    # 获取价格估算
    if st.button("🔍 比较价格", type="primary", use_container_width=True):
        with st.spinner("正在查询各平台价格..."):
            pickup = {
                'address': pickup_address,
                'lat': pickup_lat,
                'lon': pickup_lon
            }
            
            dropoff = {
                'address': dropoff_address,
                'lat': dropoff_lat,
                'lon': dropoff_lon
            }
            
            # 获取估价
            estimates = ride_service.estimate_ride_price(pickup, dropoff, region='US')
            
            if estimates:
                st.success(f"找到 {len(estimates)} 个打车选项")
                
                # 显示价格卡片
                for est in estimates:
                    with st.container():
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #ffc107;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin: 0;">{est['platform']}</h3>
                                    <p style="color: #8b949e; margin: 5px 0;">{est['service_type']}</p>
                                </div>
                                <div style="text-align: right;">
                                    <p style="font-size: 1.8em; font-weight: bold; color: #ffc107; margin: 0;">
                                        ${est['price_min']:.2f} - ${est['price_max']:.2f}
                                    </p>
                                    <p style="color: #8b949e; font-size: 0.9em; margin: 5px 0;">
                                        {est['estimated_time']} • {est['distance']}
                                    </p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 预订按钮
                        col_btn1, col_btn2 = st.columns([1, 1])
                        
                        with col_btn1:
                            # 生成深度链接
                            links = ride_service.generate_booking_link(
                                est['platform'].lower().replace('滴滴出行', 'didi'),
                                pickup,
                                dropoff
                            )
                            
                            if links.get('app_link'):
                                st.markdown(
                                    f'<a href="{links["app_link"]}" '
                                    f'class="action-btn" style="background: #ffc107; color: #000;">'
                                    f'📱 打开APP预订</a>',
                                    unsafe_allow_html=True
                                )
                        
                        with col_btn2:
                            st.markdown(
                                f'<a href="{links["web_link"]}" target="_blank" '
                                f'class="action-btn" style="background: #667eea;">'
                                f'🌐 网页预订</a>',
                                unsafe_allow_html=True
                            )
                        
                        st.markdown("---")
            else:
                st.warning("未找到可用的打车选项")
    
    # 自动安排行程打车
    st.markdown("### 📅 自动安排行程打车")
    
    if st.checkbox("为此行程自动安排打车"):
        trip_info = {
            'home_address': pickup_address,
            'departure_airport': 'Newark Airport (EWR)',
            'arrival_airport': 'Tokyo Narita Airport (NRT)',
            'hotel_address': 'Shibuya, Tokyo',
            'departure_time': trip_data.get('departure_time', '2025-03-15T10:00:00'),
            'arrival_time': trip_data.get('arrival_time', '2025-03-15T14:00:00')
        }
        
        schedules = ride_service.auto_schedule_ride(trip_info, ride_type='airport')
        
        if schedules.get('schedules'):
            st.info("系统已为您规划以下打车行程:")
            
            for schedule in schedules['schedules']:
                st.markdown(f"""
                <div class="glass-card">
                    <h4>🚖 {schedule['type'].replace('_', ' ').title()}</h4>
                    <p><strong>预约时间:</strong> {schedule['pickup_time'][:16].replace('T', ' ')}</p>
                    <p><strong>上车地点:</strong> {schedule['pickup_location']}</p>
                    <p><strong>目的地:</strong> {schedule['dropoff_location']}</p>
                    <p style="color: #ffc107;"><strong>💡 提示:</strong> {schedule['note']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.warning("⚠️ 自动预约功能需要API集成。当前请手动预订。")


def render_rebooking_alerts(trip_id: int, database):
    """
    渲染改签提醒组件
    
    Args:
        trip_id: 行程ID
        database: 数据库实例
    """
    # 获取未解决的改签警报
    alerts = database.get_unresolved_alerts(trip_id)
    
    rebooking_alerts = [a for a in alerts if a.get('alert_type') == 'rebooking_recommended']
    
    if rebooking_alerts:
        st.markdown("### 🔄 改签建议")
        
        for alert in rebooking_alerts:
            severity_color = {
                'low': '#17a2b8',
                'medium': '#ffc107',
                'high': '#fd7e14',
                'critical': '#dc3545'
            }
            
            color = severity_color.get(alert.get('severity', 'medium'), '#ffc107')
            
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: {color};">⚠️ 需要改签</h4>
                        <p style="margin: 10px 0;">{alert.get('message', '')}</p>
                        <p style="color: #8b949e; font-size: 0.9em;">
                            {alert.get('created_at', '')}
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button(f"查看改签选项 #{alert['id']}", key=f"rebook_{alert['id']}"):
                    st.info("改签详情已通过邮件发送,请查收")
            
            with col2:
                if st.button(f"标记已处理 #{alert['id']}", key=f"resolve_{alert['id']}"):
                    database.resolve_alert(alert['id'])
                    st.success("已标记为已处理")
                    st.rerun()


# 使用示例
if __name__ == "__main__":
    # Streamlit测试
    st.set_page_config(page_title="打车预订测试", layout="wide")
    
    st.title("🚖 打车预订系统测试")
    
    # 模拟行程数据
    test_trip = {
        'pickup_address': 'Piscataway, NJ',
        'dropoff_address': 'Newark Airport (EWR)',
        'departure_time': '2025-03-15T10:00:00',
        'arrival_time': '2025-03-15T14:00:00'
    }
    
    # 渲染组件
    render_ride_booking_widget(test_trip)
    
    st.markdown("---")
    
    # 测试改签警报
    st.markdown("### 测试改签警报")
    st.info("改签警报会在航班延误/取消时自动显示")
