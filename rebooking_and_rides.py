"""
Automatic Rebooking and Ride-Hailing Integration
自动改签和打车预订系统
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class FlightRebookingAgent:
    """
    自动航班改签系统
    Automatic Flight Rebooking System
    
    功能:
    - 检测航班延误/取消
    - 自动搜索替代航班
    - 生成改签建议
    - 一键改签(需要航空公司API)
    """
    
    def __init__(self, email_service=None):
        self.email_service = email_service
        self.rebooking_rules = {
            'delay_threshold': 120,  # 延误超过2小时触发改签
            'cancel_immediate': True,  # 取消立即改签
            'same_airline_priority': True,  # 优先同航空公司
            'max_price_increase': 200,  # 最多接受加价$200
            'time_window': 6  # 在原航班前后6小时内寻找
        }
    
    def check_need_rebooking(self, flight_status) -> Tuple[bool, str]:
        """
        检查是否需要改签
        
        Returns:
            (需要改签, 原因)
        """
        if flight_status.status == 'cancelled':
            return True, 'flight_cancelled'
        
        if flight_status.delay_minutes >= self.rebooking_rules['delay_threshold']:
            return True, f'delayed_{flight_status.delay_minutes}_minutes'
        
        return False, 'no_action_needed'
    
    def find_alternative_flights(self, original_flight: Dict, 
                                departure_date: str) -> List[Dict]:
        """
        查找替代航班
        
        使用免费的AviationStack API搜索同航线航班
        """
        try:
            from free_flight_monitor import AviationStackAPI
            
            api = AviationStackAPI()
            
            # 解析原始航班信息
            dep_airport = original_flight.get('departure_airport')
            arr_airport = original_flight.get('arrival_airport')
            
            if not dep_airport or not arr_airport:
                logger.warning("Missing airport information")
                return []
            
            # 搜索同航线的其他航班
            alternatives = []
            
            # 在前后时间窗口内搜索
            time_window = self.rebooking_rules['time_window']
            
            # 模拟搜索结果(实际应该调用API)
            # 这里返回示例数据
            alternatives = [
                {
                    'flight_number': 'UA2015',
                    'airline': 'United Airlines',
                    'departure_time': '14:30',
                    'arrival_time': '18:45',
                    'price_estimate': '+$50',
                    'available_seats': 12,
                    'booking_link': f'https://www.united.com/rebooking?from={dep_airport}&to={arr_airport}'
                },
                {
                    'flight_number': 'AA1234',
                    'airline': 'American Airlines',
                    'departure_time': '16:00',
                    'arrival_time': '20:15',
                    'price_estimate': '+$75',
                    'available_seats': 8,
                    'booking_link': f'https://www.aa.com/booking?from={dep_airport}&to={arr_airport}'
                },
                {
                    'flight_number': 'DL5678',
                    'airline': 'Delta Airlines',
                    'departure_time': '17:30',
                    'arrival_time': '21:45',
                    'price_estimate': '+$0',
                    'available_seats': 15,
                    'booking_link': f'https://www.delta.com/booking?from={dep_airport}&to={arr_airport}'
                }
            ]
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error finding alternative flights: {e}")
            return []
    
    def generate_rebooking_recommendation(self, original_flight: Dict,
                                         alternatives: List[Dict]) -> Dict:
        """
        生成改签建议
        
        考虑因素:
        - 起飞时间(越接近原航班越好)
        - 价格(越便宜越好)
        - 同航空公司优先
        - 座位可用性
        """
        if not alternatives:
            return {
                'recommended': None,
                'reason': 'No alternative flights available',
                'all_options': []
            }
        
        # 评分系统
        scored_alternatives = []
        
        for alt in alternatives:
            score = 100
            
            # 价格评分(价格越低越好)
            price_str = alt.get('price_estimate', '+$0')
            price_increase = int(price_str.replace('+$', '').replace('$', ''))
            score -= min(price_increase / 10, 30)  # 最多扣30分
            
            # 座位评分(座位越多越好)
            seats = alt.get('available_seats', 0)
            if seats > 10:
                score += 10
            elif seats < 5:
                score -= 10
            
            # 同航空公司加分
            if self.rebooking_rules['same_airline_priority']:
                if alt.get('airline') == original_flight.get('airline'):
                    score += 20
            
            # 时间评分(这里简化处理)
            score += 5  # 基础分
            
            alt['recommendation_score'] = score
            scored_alternatives.append(alt)
        
        # 排序
        scored_alternatives.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        best_option = scored_alternatives[0]
        
        return {
            'recommended': best_option,
            'reason': f"Best balance of price ({best_option['price_estimate']}) and timing",
            'all_options': scored_alternatives
        }
    
    def auto_rebook(self, original_booking: Dict, new_flight: Dict,
                   user_email: str) -> Dict:
        """
        自动改签(需要航空公司API支持)
        
        实际实现需要:
        1. 航空公司API访问权限
        2. 用户授权
        3. 支付处理
        
        当前实现: 生成改签指令并发送邮件
        """
        rebooking_info = {
            'status': 'manual_action_required',
            'original_flight': original_booking.get('flight_number'),
            'new_flight': new_flight.get('flight_number'),
            'price_difference': new_flight.get('price_estimate'),
            'action_required': [
                f"1. 访问: {new_flight.get('booking_link')}",
                "2. 输入原订票号",
                "3. 选择新航班并确认",
                "4. 支付差价(如有)"
            ],
            'deadline': (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        # 发送改签通知邮件
        if self.email_service:
            self._send_rebooking_email(user_email, original_booking, 
                                      new_flight, rebooking_info)
        
        return rebooking_info
    
    def _send_rebooking_email(self, user_email: str, original: Dict,
                             new_flight: Dict, rebooking_info: Dict):
        """发送改签通知邮件"""
        subject = f"🔄 改签建议: {original.get('flight_number')} → {new_flight.get('flight_number')}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 10px; }}
        .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .flight-card {{ background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; }}
        .button {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; 
                   border-radius: 5px; display: inline-block; margin: 10px 0; }}
        .price {{ font-size: 1.5em; font-weight: bold; color: #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 航班改签建议</h1>
            <p>我们为您找到了更好的替代航班</p>
        </div>
        
        <div class="alert">
            <strong>⚠️ 原航班状态:</strong> {original.get('status', '延误/取消')}<br>
            需要在 {rebooking_info.get('deadline', '2小时内')} 前采取行动
        </div>
        
        <h2>📍 原航班信息</h2>
        <div class="flight-card">
            <strong>航班号:</strong> {original.get('flight_number')}<br>
            <strong>航空公司:</strong> {original.get('airline')}<br>
            <strong>状态:</strong> ❌ {original.get('status')}
        </div>
        
        <h2>✅ 推荐替代航班</h2>
        <div class="flight-card" style="border-left: 4px solid #28a745;">
            <strong>航班号:</strong> {new_flight.get('flight_number')}<br>
            <strong>航空公司:</strong> {new_flight.get('airline')}<br>
            <strong>起飞时间:</strong> {new_flight.get('departure_time')}<br>
            <strong>到达时间:</strong> {new_flight.get('arrival_time')}<br>
            <strong>可用座位:</strong> {new_flight.get('available_seats')} 个<br>
            <div class="price">差价: {new_flight.get('price_estimate')}</div>
        </div>
        
        <h3>📋 改签步骤:</h3>
        <ol>
            {' '.join([f'<li>{step}</li>' for step in rebooking_info.get('action_required', [])])}
        </ol>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{new_flight.get('booking_link')}" class="button">立即改签 →</a>
        </div>
        
        <p style="color: #666; font-size: 0.9em;">
            💡 提示: 改签通常免费,只需支付差价。建议尽快操作以确保座位。
        </p>
    </div>
</body>
</html>
"""
        
        try:
            self.email_service.send_email(user_email, subject, html_body)
            logger.info(f"Rebooking email sent to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send rebooking email: {e}")


class RideHailingIntegration:
    """
    打车服务集成
    Ride-Hailing Integration (Uber, Lyft, 滴滴)
    
    功能:
    - 价格比较(多平台)
    - 自动预约
    - 实时追踪
    - 支付处理
    """
    
    def __init__(self):
        self.platforms = {
            'uber': {
                'name': 'Uber',
                'api_available': False,  # 需要Uber API密钥
                'booking_link': 'https://m.uber.com/ul/',
                'supported_regions': ['US', 'Global']
            },
            'lyft': {
                'name': 'Lyft',
                'api_available': False,  # 需要Lyft API密钥
                'booking_link': 'https://www.lyft.com/ride',
                'supported_regions': ['US', 'Canada']
            },
            'didi': {
                'name': '滴滴出行',
                'api_available': False,
                'booking_link': 'https://page.didiglobal.com/',
                'supported_regions': ['China', 'Asia']
            }
        }
    
    def estimate_ride_price(self, pickup: Dict, dropoff: Dict,
                           region: str = 'US') -> List[Dict]:
        """
        估算打车价格(多平台比较)
        
        Args:
            pickup: {'address': str, 'lat': float, 'lon': float}
            dropoff: {'address': str, 'lat': float, 'lon': float}
            region: 地区代码
            
        Returns:
            各平台价格估算列表
        """
        # 计算距离(简化)
        distance_km = self._calculate_distance(pickup, dropoff)
        
        estimates = []
        
        # Uber估算
        if region in ['US', 'Global']:
            uber_estimate = self._estimate_uber_price(distance_km)
            estimates.append(uber_estimate)
        
        # Lyft估算
        if region in ['US', 'Canada']:
            lyft_estimate = self._estimate_lyft_price(distance_km)
            estimates.append(lyft_estimate)
        
        # 滴滴估算
        if region in ['China', 'Asia']:
            didi_estimate = self._estimate_didi_price(distance_km)
            estimates.append(didi_estimate)
        
        # 按价格排序
        estimates.sort(key=lambda x: x['price_min'])
        
        return estimates
    
    def _calculate_distance(self, pickup: Dict, dropoff: Dict) -> float:
        """计算两点间距离(公里)"""
        from math import radians, cos, sin, asin, sqrt
        
        # 如果有经纬度,使用Haversine公式
        if 'lat' in pickup and 'lat' in dropoff:
            lat1, lon1 = radians(pickup['lat']), radians(pickup['lon'])
            lat2, lon2 = radians(dropoff['lat']), radians(dropoff['lon'])
            
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            
            # 地球半径(公里)
            r = 6371
            
            return c * r
        
        # 否则返回估算值
        return 15.0  # 默认15公里
    
    def _estimate_uber_price(self, distance_km: float) -> Dict:
        """Uber价格估算"""
        # 简化的价格模型
        base_fare = 2.50
        per_km = 1.75
        per_minute = 0.35
        estimated_time = distance_km * 3  # 假设20km/h平均速度
        
        price_min = base_fare + (distance_km * per_km) + (estimated_time * per_minute)
        price_max = price_min * 1.3  # 考虑高峰时段
        
        return {
            'platform': 'Uber',
            'service_type': 'UberX',
            'price_min': round(price_min, 2),
            'price_max': round(price_max, 2),
            'currency': 'USD',
            'estimated_time': f"{int(estimated_time)} min",
            'distance': f"{distance_km:.1f} km",
            'booking_link': self.platforms['uber']['booking_link']
        }
    
    def _estimate_lyft_price(self, distance_km: float) -> Dict:
        """Lyft价格估算"""
        # Lyft通常比Uber便宜5-10%
        uber_estimate = self._estimate_uber_price(distance_km)
        
        price_min = uber_estimate['price_min'] * 0.95
        price_max = uber_estimate['price_max'] * 0.95
        
        return {
            'platform': 'Lyft',
            'service_type': 'Lyft',
            'price_min': round(price_min, 2),
            'price_max': round(price_max, 2),
            'currency': 'USD',
            'estimated_time': uber_estimate['estimated_time'],
            'distance': uber_estimate['distance'],
            'booking_link': self.platforms['lyft']['booking_link']
        }
    
    def _estimate_didi_price(self, distance_km: float) -> Dict:
        """滴滴价格估算(人民币)"""
        base_fare = 13.0  # 起步价
        per_km = 2.3
        per_minute = 0.8
        estimated_time = distance_km * 3
        
        price_min = base_fare + (distance_km * per_km) + (estimated_time * per_minute)
        price_max = price_min * 1.2
        
        return {
            'platform': '滴滴出行',
            'service_type': '快车',
            'price_min': round(price_min, 2),
            'price_max': round(price_max, 2),
            'currency': 'CNY',
            'estimated_time': f"{int(estimated_time)} 分钟",
            'distance': f"{distance_km:.1f} 公里",
            'booking_link': self.platforms['didi']['booking_link']
        }
    
    def generate_booking_link(self, platform: str, pickup: Dict, 
                             dropoff: Dict) -> str:
        """
        生成深度链接(Deep Link)直接打开APP
        
        支持的格式:
        - Uber: uber://?action=setPickup&pickup=...
        - Lyft: lyft://ridetype?...
        """
        if platform.lower() == 'uber':
            pickup_addr = pickup.get('address', '').replace(' ', '+')
            dropoff_addr = dropoff.get('address', '').replace(' ', '+')
            
            # Uber深度链接
            link = f"uber://?action=setPickup&pickup[latitude]={pickup.get('lat', 0)}"
            link += f"&pickup[longitude]={pickup.get('lon', 0)}"
            link += f"&dropoff[latitude]={dropoff.get('lat', 0)}"
            link += f"&dropoff[longitude]={dropoff.get('lon', 0)}"
            
            # Web fallback
            web_link = f"https://m.uber.com/ul/?action=setPickup&pickup[formatted_address]={pickup_addr}"
            web_link += f"&dropoff[formatted_address]={dropoff_addr}"
            
            return {
                'app_link': link,
                'web_link': web_link
            }
        
        elif platform.lower() == 'lyft':
            # Lyft深度链接
            link = f"lyft://ridetype?id=lyft"
            link += f"&pickup[latitude]={pickup.get('lat', 0)}"
            link += f"&pickup[longitude]={pickup.get('lon', 0)}"
            link += f"&destination[latitude]={dropoff.get('lat', 0)}"
            link += f"&destination[longitude]={dropoff.get('lon', 0)}"
            
            return {
                'app_link': link,
                'web_link': self.platforms['lyft']['booking_link']
            }
        
        return {
            'app_link': None,
            'web_link': self.platforms.get(platform.lower(), {}).get('booking_link', '#')
        }
    
    def auto_schedule_ride(self, trip_info: Dict, ride_type: str = 'airport') -> Dict:
        """
        自动安排行程打车
        
        Args:
            trip_info: 行程信息
            ride_type: 'airport' | 'hotel' | 'attraction'
            
        Returns:
            打车预约信息
        """
        schedules = []
        
        if ride_type == 'airport':
            # 去机场: 出发前3小时预约
            departure_time = datetime.fromisoformat(trip_info.get('departure_time'))
            pickup_time = departure_time - timedelta(hours=3)
            
            schedules.append({
                'type': 'to_airport',
                'pickup_time': pickup_time.isoformat(),
                'pickup_location': trip_info.get('home_address'),
                'dropoff_location': trip_info.get('departure_airport'),
                'note': '请提前3小时到达机场'
            })
            
            # 从机场回来: 落地后30分钟
            arrival_time = datetime.fromisoformat(trip_info.get('arrival_time'))
            dropoff_time = arrival_time + timedelta(minutes=30)
            
            schedules.append({
                'type': 'from_airport',
                'pickup_time': dropoff_time.isoformat(),
                'pickup_location': trip_info.get('arrival_airport'),
                'dropoff_location': trip_info.get('hotel_address'),
                'note': '落地后前往酒店'
            })
        
        return {
            'schedules': schedules,
            'auto_booking_available': False,  # 需要API集成
            'manual_booking_required': True
        }


# 使用示例和测试
if __name__ == "__main__":
    print("="*60)
    print("自动改签和打车系统测试")
    print("="*60)
    
    # 测试1: 航班改签
    print("\n📍 测试航班改签...")
    rebooking_agent = FlightRebookingAgent()
    
    original_flight = {
        'flight_number': 'UA123',
        'airline': 'United Airlines',
        'status': 'delayed',
        'delay_minutes': 150,
        'departure_airport': 'EWR',
        'arrival_airport': 'LAX'
    }
    
    # 查找替代航班
    alternatives = rebooking_agent.find_alternative_flights(
        original_flight,
        '2025-02-15'
    )
    
    print(f"找到 {len(alternatives)} 个替代航班:")
    for alt in alternatives:
        print(f"  - {alt['flight_number']}: {alt['departure_time']} ({alt['price_estimate']})")
    
    # 生成建议
    recommendation = rebooking_agent.generate_rebooking_recommendation(
        original_flight,
        alternatives
    )
    
    if recommendation['recommended']:
        rec = recommendation['recommended']
        print(f"\n✅ 推荐航班: {rec['flight_number']}")
        print(f"   评分: {rec['recommendation_score']:.1f}/100")
        print(f"   原因: {recommendation['reason']}")
    
    # 测试2: 打车价格比较
    print("\n📍 测试打车价格比较...")
    ride_service = RideHailingIntegration()
    
    pickup = {
        'address': 'Piscataway, NJ',
        'lat': 40.5548,
        'lon': -74.4605
    }
    
    dropoff = {
        'address': 'Newark Airport (EWR)',
        'lat': 40.6895,
        'lon': -74.1745
    }
    
    estimates = ride_service.estimate_ride_price(pickup, dropoff, region='US')
    
    print(f"\n找到 {len(estimates)} 个打车选项:")
    for est in estimates:
        print(f"\n  {est['platform']} - {est['service_type']}")
        print(f"  价格范围: ${est['price_min']:.2f} - ${est['price_max']:.2f}")
        print(f"  预计时间: {est['estimated_time']}")
        print(f"  距离: {est['distance']}")
    
    # 生成预订链接
    print("\n📍 生成Uber预订链接...")
    links = ride_service.generate_booking_link('uber', pickup, dropoff)
    print(f"  App链接: {links['app_link'][:60]}...")
    print(f"  Web链接: {links['web_link'][:60]}...")
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
