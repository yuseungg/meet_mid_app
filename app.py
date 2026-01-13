import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox 
import math
import os 
import base64 

# --- 🔑 보안: API 키 설정 ---
try:
    KAKAO_REST_API_KEY = st.secrets["general"]["kakao_api_key"].strip()
except Exception:
    st.error("🚨 API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요!")
    st.stop()

# --- 🛠️ [유지] 이미지 Base64 변환 함수 (로고용) ---
def get_img_as_base64(file_path):
    """이미지 파일을 읽어서 HTML에서 쓸 수 있는 문자열로 변환합니다."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# --- 📍 전국 주요 핫플레이스 DB ---
NATIONWIDE_HOTSPOTS = {
    "서울 강남역": { "coords": (37.498095, 127.027610), "desc": "교통 요지이자 맛집/쇼핑의 메카" },
    "서울 홍대입구": { "coords": (37.557527, 126.9244669), "desc": "버스킹, 클럽, 맛집이 모인 젊음의 거리" },
    "서울 건대입구": { "coords": (37.540458, 127.069320), "desc": "맛집, 술집, 쇼핑이 가득한 거리" },
    "서울 용산역": { "coords": (37.529886, 126.964801), "desc": "아이파크몰, 이태원 접근성 우수" },
    "서울 종로3가": { "coords": (37.570415, 126.992161), "desc": "익선동 한옥거리와 포장마차 감성" },
    "서울 잠실역": { "coords": (37.513261, 127.100133), "desc": "롯데월드몰과 석촌호수 산책" },
    "서울 사당역": { "coords": (37.476553, 126.981550), "desc": "경기 남부와 서울을 잇는 관문" },
    "서울 명동": { "coords": (37.560997, 126.986175), "desc": "외국인 관광객과 쇼핑의 중심지" },
    "서울 성수동": { "coords": (37.544579, 127.055967), "desc": "힙한 카페와 팝업스토어 성지" },
    "판교역": { "coords": (37.394761, 127.111194), "desc": "현대백화점과 아브뉴프랑" },
    "수원역": { "coords": (37.265679, 127.000047), "desc": "AK플라자, 롯데몰 등 거대 상권" },
    "인천 부평": { "coords": (37.489493, 126.724068), "desc": "거대 지하상가와 문화의 거리" },
    "대전 둔산동": { "coords": (36.350412, 127.384548), "desc": "대전의 핫플레이스, 갤러리아 인근" },
    "대전역": { "coords": (36.332516, 127.434156), "desc": "성심당 본점과 가까운 KTX 허브" },
    "천안 터미널": { "coords": (36.819830, 127.155822), "desc": "백화점과 먹자골목이 모인 천안 중심" },
    "청주 터미널": { "coords": (36.626490, 127.432657), "desc": "청주 교통과 쇼핑의 중심" },
    "강릉역": { "coords": (37.763740, 128.899484), "desc": "KTX 내리면 바로 바다 여행" },
    "원주 터미널": { "coords": (37.344463, 127.930492), "desc": "강원 영서 최대 번화가" },
    "춘천 명동": { "coords": (37.880628, 127.727506), "desc": "닭갈비 골목과 낭만 여행" },
    "부산 서면": { "coords": (35.157816, 129.060033), "desc": "부산 쇼핑과 맛집의 정중앙" },
    "부산역": { "coords": (35.115225, 129.042243), "desc": "차이나타운과 부산 여행의 시작" },
    "부산 해운대": { "coords": (35.163113, 129.163550), "desc": "바다와 럭셔리한 맛집들" },
    "대구 동성로": { "coords": (35.869666, 128.594038), "desc": "대구 최대 번화가, 젊음의 거리" },
    "동대구역": { "coords": (35.871435, 128.624925), "desc": "신세계백화점과 복합환승센터" },
    "울산 삼산동": { "coords": (35.539622, 129.335967), "desc": "백화점과 관람차가 있는 울산 중심" },
    "광주 충장로": { "coords": (35.148154, 126.915598), "desc": "광주의 명동, 패션과 문화의 거리" },
    "광주 유스퀘어": { "coords": (35.160167, 126.879307), "desc": "아시아 최대 터미널과 복합문화공간" },
    "전주 한옥마을": { "coords": (35.814708, 127.152632), "desc": "먹거리와 한옥이 어우러진 관광 명소" }
}

# --- 🛠️ 함수 정의 ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def search_kakao_for_box(searchterm: str):
    if not searchterm: return []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    try:
        res = requests.get(url, headers=headers, params={"query": searchterm, "size": 15})
        data = res.json().get('documents', [])
        return [(f"{item['place_name']} ({item['address_name']})", item) for item in data]
    except: return []

@st.cache_data(show_spinner=False)
def get_hotplace_nearby(lat, lon, radius=5000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"category_group_code": "SW8", "x": str(lon), "y": str(lat), "radius": radius, "sort": "distance", "size": 15}
    try:
        res = requests.get(url, headers=headers, params=params).json()
        documents = res.get('documents', [])
        if not documents:
            params['category_group_code'] = "CT1"
            url_k = "https://dapi.kakao.com/v2/local/search/keyword.json"
            params_k = {"query": "터미널", "x": str(lon), "y": str(lat), "radius": radius, "sort": "distance"}
            res_k = requests.get(url_k, headers=headers, params=params_k).json()
            documents = res_k.get('documents', [])
        return documents[:3]
    except: return []

@st.cache_data(show_spinner=False)
def get_nearby_details(lat, lon, category_code):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"category_group_code": category_code, "x": str(lon), "y": str(lat), "radius": 1500, "sort": "accuracy"}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get('documents', []) if res.status_code == 200 else []
    except: return []

# --- 🎨 UI 디자인 ---
st.set_page_config(page_title="MIDMEET", page_icon="favicon.png", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');

    .stApp { 
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        font-family: 'Gamja Flower', cursive !important;
        font-size: 22px !important;
    }
    
    h1, h2, h3 { color: #000 !important; }
    
    /* 헤더 숨기기 */
    header {visibility: hidden !important;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}

    /* 입력창 사이즈 */
    div[data-testid="stSearchbox"] > div, .stSelectbox > div > div {
        min-height: 50px !important; 
        display: flex !important;
        align-items: center !important;
        border: 3px solid #000 !important; 
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px !important; 
        font-size: 1.5rem !important;
        padding: 5px 15px !important;
    }
    
    /* 버튼 스타일 */
    div.stButton > button {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        border: 3px solid #000 !important;
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
        box-shadow: 4px 5px 0px #000 !important;
        padding: 15px 30px !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #FFF9C4 !important; 
        transform: scale(1.02);
    }

    /* 박스 크기 슬림하게 조정 */
    .place-container {
        display: flex; align-items: center; 
        background-color: #FFFFFF; 
        padding: 12px; margin-bottom: 15px;
        border: 2px solid #000;
        border-radius: 15px 255px 15px 25px / 255px 15px 225px 15px; 
        box-shadow: 3px 3px 0px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 상태 관리 ---
if "step" not in st.session_state: st.session_state.step = "input"
if "num_friends" not in st.session_state: st.session_state.num_friends = 3
if "coords" not in st.session_state: st.session_state.coords = {}
if "names" not in st.session_state: st.session_state.names = {}
if "vibe" not in st.session_state: st.session_state.vibe = "🍚 맛집 투어"
if "saved_algo_option" not in st.session_state: st.session_state.saved_algo_option = "거리 우선 추천" 

# --- 🌟 캐릭터 이미지 파일명 ---
friend_chars = ["friend1.png", "friend2.png", "friend3.png", "friend4.png"]
vibe_options = ["🍚 맛집 투어", "🍻 술/회식", "☕ 카페/수다", "📚 스터디/조용함"]
alcohol_kws = ["고기", "곱창", "막창", "갈비", "삼겹살", "구이", "포차", "주점", "호프", "맥주", "이자카야", "술집"]


# ==========================================
# 📺 화면 1: 만남 설정 (입력 화면)
# ==========================================
if st.session_state.step == "input":
    
    col_title_main, col_logo = st.columns([0.8, 0.2])
    with col_title_main:
        icon_base64 = get_img_as_base64("favicon.png")
        if icon_base64:
            st.markdown(f"""
                <h1 style='display: flex; align-items: center;'>
                    <img src="data:image/png;base64,{icon_base64}" width='55' style='margin-right: 15px; margin-top: 5px;'>
                    MIDMEET
                </h1>
                """, unsafe_allow_html=True)
        else:
            st.title("✏️ MIDMEET")
            
        st.caption("친구들과의 완벽한 중간 지점 (Hand-drawn Ver.)")
    
    st.divider()

    st.markdown("### 1️⃣ 오늘의 만남 목적은?")
    st.session_state.vibe = st.selectbox(
        "목적 선택", 
        vibe_options,
        index=vibe_options.index(st.session_state.vibe),
        label_visibility="collapsed"
    )
    
    st.divider()

    st.markdown("### 2️⃣ 누가 어디서 오나요?")
    c_btn1, c_btn2, c_void = st.columns([0.2, 0.2, 0.6])
    with c_btn1:
        if st.button("➕ 인원 추가"):
            st.session_state.num_friends += 1
            st.rerun()
    with c_btn2:
        if st.button("➖ 인원 삭제") and st.session_state.num_friends > 2:
            idx = st.session_state.num_friends - 1
            st.session_state.coords.pop(idx, None)
            st.session_state.names.pop(idx, None)
            st.session_state.num_friends -= 1
            st.rerun()

    for i in range(st.session_state.num_friends):
        st.write("") 
        
        col_char, col_search = st.columns([0.35, 0.65])
        
        with col_char:
            st.markdown(f"**친구 {i+1}**")
            if i < 4 and os.path.exists(friend_chars[i]):
                st.image(friend_chars[i], width=250)
            else:
                st.write("😐")
        
        with col_search:
            st.write("") 
            st.write("")
            
            sb_key = f"search_stable_{i}"
            selected_place = st_searchbox(
                search_kakao_for_box, 
                key=sb_key, 
                placeholder=f"친구 {i+1} 출발지 (예: 강남역)",
                clear_on_submit=False
            )
            
            if selected_place:
                current_val = st.session_state.coords.get(i)
                new_val = (float(selected_place['y']), float(selected_place['x']))
                
                if current_val != new_val:
                    st.session_state.coords[i] = new_val
                    st.session_state.names[i] = selected_place['place_name']
                    st.rerun() 
            
            if i in st.session_state.names:
                st.success(f"📍 확정: **{st.session_state.names[i]}**")
            else:
                st.info("👈 위 검색창에서 장소를 선택해주세요")

    st.divider()
    
    if st.button("🚀 중간 지점 찾기 (Click!)", type="primary"):
        missing_friends = []
        for i in range(st.session_state.num_friends):
            if i not in st.session_state.coords:
                missing_friends.append(str(i+1))
        
        if missing_friends:
             st.error(f"⚠️ 친구 {', '.join(missing_friends)}번의 장소가 확정되지 않았습니다. 검색 후 클릭해주세요!")
        else:
            st.session_state.step = "result"
            st.rerun()


# ==========================================
# 📺 화면 2: 결과 보기
# ==========================================
elif st.session_state.step == "result":
    
    col_back, col_res_title, col_vibe_change = st.columns([0.15, 0.45, 0.4])
    
    # 현재 상세화면(Detail) 상태인지 확인
    active_detail_idx = -1
    for key in st.session_state:
        if key.startswith("view_mode_tab_") and st.session_state[key].startswith("detail_"):
            active_detail_idx = int(key.split("_")[-1])
            break

    # 뒤로가기 버튼 로직
    with col_back:
        if active_detail_idx != -1:
            if st.button("⬅️ 뒤로"):
                st.session_state[f"view_mode_tab_{active_detail_idx}"] = "list"
                st.rerun()
        else:
            if st.button("⬅️ 처음"):
                st.session_state.step = "input"
                for key in list(st.session_state.keys()):
                    if key.startswith("view_mode_tab_"): del st.session_state[key]
                st.rerun()
            
    with col_res_title:
        st.markdown("## 🎉 추천 결과")
        
    # 목적 변경 (상세 화면 아닐 때만 노출)
    if active_detail_idx == -1:
        with col_vibe_change:
            st.session_state.vibe = st.selectbox(
                "목적 변경", 
                vibe_options,
                index=vibe_options.index(st.session_state.vibe),
                label_visibility="collapsed"
            )

    st.divider()

    # 알고리즘 선택 (상세 화면 아닐 때만)
    if active_detail_idx == -1:
        algo_option = st.radio(
            "기준 선택",
            ["거리 우선 추천", "놀거리 우선 추천 (전국 주요 번화가 중 최적)"], 
            horizontal=True,
            key="algo_selector"
        )
        st.session_state.saved_algo_option = algo_option
    else:
        algo_option = st.session_state.saved_algo_option

    coords = st.session_state.coords
    hotplaces = [] 

    if algo_option == "거리 우선 추천":
        mid_lat = sum(c[0] for c in coords.values()) / len(coords)
        mid_lon = sum(c[1] for c in coords.values()) / len(coords)
        if active_detail_idx == -1:
            st.info(f"📍 **중간 지점**: 위도 {mid_lat:.4f}, 경도 {mid_lon:.4f} 주변")
        hotplaces = get_hotplace_nearby(mid_lat, mid_lon, radius=5000)
    else:
        candidates = []
        for name, data in NATIONWIDE_HOTSPOTS.items():
            h_lat, h_lon = data["coords"]
            h_desc = data["desc"]
            total_dist = sum(calculate_distance(c[0], c[1], h_lat, h_lon) for c in coords.values())
            candidates.append({"place_name": name, "y": str(h_lat), "x": str(h_lon), "desc": h_desc, "total_dist": total_dist})
        candidates.sort(key=lambda x: x["total_dist"])
        hotplaces = candidates[:3]
        if active_detail_idx == -1:
            st.success(f"🔥 **{hotplaces[0]['place_name']}** 가 가장 합리적인 장소입니다!")

    if not hotplaces:
        st.warning("주변에 추천할만한 장소가 없네요 ㅠㅠ")
    else:
        # ====================================================
        # [A] 상세 보기 모드 (지도 + 상세 리스트)
        # ====================================================
        if active_detail_idx != -1:
            p = hotplaces[active_detail_idx]
            p_lat, p_lon = float(p['y']), float(p['x'])
            current_mode = st.session_state[f"view_mode_tab_{active_detail_idx}"]
            
            if current_mode == "detail_play":
                label="놀거리" 
                details = get_nearby_details(p_lat, p_lon, "AT4") + get_nearby_details(p_lat, p_lon, "CT1")
            elif current_mode == "detail_food":
                label="맛집"
                details = get_nearby_details(p_lat, p_lon, "FD6")
                if st.session_state.vibe == "🍻 술/회식":
                    details.sort(key=lambda x: any(k in x['category_name'] or k in x['place_name'] for k in alcohol_kws), reverse=True)
            else:
                label="카페"
                details = get_nearby_details(p_lat, p_lon, "CE7")
                if st.session_state.vibe == "📚 스터디/조용함":
                    details = [d for d in details if not ("보드" in d['place_name'] or "보드" in d['category_name'])]

            # 🌟 [수정] 색상을 파란색(blue)으로 변경
            kakao_map_search_url = f"https://map.kakao.com/link/search/{p['place_name']} {label}"
            st.markdown(f"### 🗺️ {p['place_name']} 주변 {label} <a href='{kakao_map_search_url}' target='_blank' style='font-size:14px; color:blue; text-decoration:none;'>[ 카카오맵으로 보기 ]</a>", unsafe_allow_html=True)
            
            m_det = folium.Map(location=[p_lat, p_lon], zoom_start=15, tiles="cartodbpositron")
            folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='star')).add_to(m_det)
            for item in details[:15]:
                folium.Marker([float(item['y']), float(item['x'])], tooltip=item['place_name'], icon=folium.Icon(color='blue', icon='info-sign')).add_to(m_det)
            st_folium(m_det, width="100%", height=400, key="detail_map_view", returned_objects=[])

            st.write("---")
            
            # 🌟 '추천순' 라벨
            st.markdown("#### 🎖️ 추천순 (카카오맵 인기 기준)")
            
            for x in details[:10]:
                st.markdown(f"""
                <div class="place-container">
                    <div style="flex:1;">
                        <div style="font-weight:bold; font-size:1.15rem; margin-bottom:3px;">{x['place_name']}</div>
                        <div style="color:#666; font-size:0.9rem;">{x['category_name'].split(' > ')[-1]}</div>
                        <a href="{x['place_url']}" target="_blank" style="font-weight:bold; color:blue; font-size:0.9rem;">📍 카카오맵 보기</a>
                    </div>
                </div>""", unsafe_allow_html=True)

        # ====================================================
        # [B] 기본 결과 모드 (버튼 방식 + fit_bounds 적용)
        # ====================================================
        else:
            rank_labels = [f"{i+1}위: {p['place_name']}" for i, p in enumerate(hotplaces)]
            
            st.write("👇 추천 장소를 선택하세요")
            selected_rank_label = st.radio("순위 선택", rank_labels, horizontal=True, label_visibility="collapsed")
            
            i = rank_labels.index(selected_rank_label)
            p = hotplaces[i]
            
            pl, plo = float(p['y']), float(p['x'])
            vk = f"view_mode_tab_{i}"
            if vk not in st.session_state: st.session_state[vk] = "list"

            st.markdown(f"""
            <div style="padding: 10px; border: 2px solid #eee; border-radius: 10px; margin-top: 10px;">
                <h3 style="margin:0;">🥇 {p['place_name']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if p.get('desc'): st.info(f"💡 {p['desc']}")
            
            all_points = [[pl, plo]]
            for c in coords.values(): all_points.append([c[0], c[1]])
            
            m = folium.Map(location=[pl, plo], tiles="cartodbpositron")
            folium.Marker([pl, plo], icon=folium.Icon(color='red', icon='star'), tooltip="중간지점").add_to(m)
            
            for idx, c in coords.items():
                fn = st.session_state.names.get(idx, f"친구 {idx+1}")
                ic = folium.CustomIcon(friend_chars[idx], icon_size=(90, 90)) if idx < 4 and os.path.exists(friend_chars[idx]) else None
                folium.Marker(c, icon=ic, tooltip=fn).add_to(m)
            
            m.fit_bounds(all_points) 
            
            st_folium(m, width="100%", height=350, key=f"main_map_{i}", returned_objects=[])

            st.write("")
            b1, b2, b3 = st.columns(3)
            
            def go_detail(k_suffix, mode_val, label):
                if st.button(label, key=k_suffix, use_container_width=True):
                    with st.spinner(f"{label.split(' ')[1]} 찾는 중..."):
                        st.session_state[vk] = mode_val
                        st.rerun()

            with b1: go_detail(f"bf_{i}", "detail_food", "🍴 맛집 보기")
            with b2: go_detail(f"bc_{i}", "detail_cafe", "☕ 카페 보기")
            with b3: go_detail(f"bp_{i}", "detail_play", "🎡 놀거리 보기")