import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- 🔑 보안: API 키 설정 ---
try:
    KAKAO_REST_API_KEY = st.secrets["general"]["kakao_api_key"].strip()
except Exception:
    KAKAO_REST_API_KEY = "69ca848b846d4e0208c59631c6c24845"

# --- 🛠️ 함수 정의 ---

def search_address(query):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    if not query or not query.strip(): return []
    try:
        res = requests.get(url, headers=headers, params={"query": query.strip(), "size": 10})
        return res.json().get('documents', []) if res.status_code == 200 else []
    except: return []

def get_hotplace_nearby(lat, lon):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": "지하철역", "x": str(lon), "y": str(lat), "radius": 2000, "sort": "distance", "size": 10}
    try:
        res = requests.get(url, headers=headers, params=params).json()
        stations = res.get('documents', [])
        return stations[:3] if stations else []
    except: return []

def get_nearby_details(lat, lon, category_code):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"category_group_code": category_code, "x": str(lon), "y": str(lat), "radius": 1500, "sort": "accuracy"}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('documents', []) if res.status_code == 200 else []
    except: return []

# --- 💻 UI 설정 ---
st.set_page_config(page_title="MeetMid", layout="wide")
st.title("🚇 MeetMid: 스마트 장소 추천")

if "coords" not in st.session_state: st.session_state.coords = [None, None, None]
if "names" not in st.session_state: st.session_state.names = [None, None, None]
if "calculated" not in st.session_state: st.session_state.calculated = False

with st.sidebar:
    st.header("📍 출발지 설정")
    for i in range(3):
        st.subheader(f"친구 {i+1}")
        query = st.text_input(f"장소 검색", key=f"q_{i}", placeholder="예: 강남역")
        if query:
            results = search_address(query)
            if results:
                options = [f"{d['place_name']} ({d['address_name']})" for d in results]
                selected_opt = st.selectbox(f"결과 선택 ({i+1})", ["-- 선택 --"] + options, key=f"sel_{i}")
                if selected_opt != "-- 선택 --":
                    idx = options.index(selected_opt)
                    res = results[idx]
                    st.session_state.coords[i] = (float(res['y']), float(res['x']))
                    st.session_state.names[i] = res['place_name']

    st.divider()
    if st.button("🚀 추천 시작", type="primary"):
        if None not in st.session_state.coords: st.session_state.calculated = True
        else: st.error("3명의 위치를 모두 선택해주세요.")

# --- 메인 결과 화면 ---
if st.session_state.calculated:
    c = st.session_state.coords
    mid_lat, mid_lon = sum(coord[0] for coord in c)/3, sum(coord[1] for coord in c)/3
    hotplaces = get_hotplace_nearby(mid_lat, mid_lon)
    
    if not hotplaces:
        st.warning("주변에 지하철역을 찾을 수 없습니다.")
    else:
        tab_titles = [f"🏆 {i+1}순위: {p['place_name']}" for i, p in enumerate(hotplaces[:3])]
        tabs = st.tabs(tab_titles)

        for i, tab in enumerate(tabs):
            place = hotplaces[i]
            p_lat, p_lon = float(place['y']), float(place['x'])

            with tab:
                # 범례
                st.markdown("""
                    <div style="display: flex; gap: 15px; margin-bottom: 10px; font-size: 0.9rem;">
                        <span style="color: orange;">● 식당</span>
                        <span style="color: blue;">● 카페</span>
                        <span style="color: green;">● 놀거리</span>
                    </div>
                """, unsafe_allow_html=True)

                foods = get_nearby_details(p_lat, p_lon, "FD6")
                cafes = get_nearby_details(p_lat, p_lon, "CE7")
                plays = get_nearby_details(p_lat, p_lon, "CT1")

                # 지도 초기화 (재렌더링 시 깜빡임 방지를 위해 고유 키 부여)
                m = folium.Map(location=[p_lat, p_lon], zoom_start=15, tiles="OpenStreetMap")
                
                # 마커 스타일을 위한 CSS 추가 (글자 크기 및 가로 정렬)
                tooltip_style = "font-size: 10px; white-space: nowrap; font-weight: normal;"

                # 1. 추천 장소 본체
                folium.Marker([p_lat, p_lon], tooltip=folium.Tooltip(place['place_name'], permanent=True),
                              icon=folium.Icon(color='red', icon='star')).add_to(m)

                # 2. 카테고리별 마커 (마우스 호버 시 이름 노출)
                def add_custom_markers(items, color):
                    for item in items[:8]:
                        # CircleMarker 사용 및 툴팁 설정
                        folium.CircleMarker(
                            location=[float(item['y']), float(item['x'])],
                            radius=6, color=color, fill=True, fill_opacity=0.8,
                            tooltip=folium.Tooltip(f"<span style='{tooltip_style}'>{item['place_name']}</span>")
                        ).add_to(m)

                add_custom_markers(foods, 'orange')
                add_custom_markers(cafes, 'blue')
                add_custom_markers(plays, 'green')

                # 3. 친구 위치
                for idx in range(3):
                    folium.Marker(c[idx], icon=folium.Icon(color='lightgray'), tooltip=f"친구{idx+1}").add_to(m)

                # 지도 렌더링
                st_folium(m, width="100%", height=550, key=f"final_map_{i}", returned_objects=[])

                st.markdown('<div style="text-align: right; color: gray; font-size: 0.7rem;">지도 데이터: Kakao Mobility</div>', unsafe_allow_html=True)

                # 상세 리스트
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("🍴 **식당**")
                    for x in foods[:5]: st.caption(f"• {x['place_name']}")
                with col2:
                    st.markdown("☕ **카페**")
                    for x in cafes[:5]: st.caption(f"• {x['place_name']}")
                with col3:
                    st.markdown("🎡 **놀거리**")
                    for x in plays[:5]: st.caption(f"• {x['place_name']}")
else:
    st.info("좌측 사이드바에서 친구들의 출발지를 입력하고 버튼을 눌러주세요!")