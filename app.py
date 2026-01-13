import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox 
import math
from bs4 import BeautifulSoup
import os 
import base64  # 🌟 [필수] 이미지를 코드로 변환하기 위해 추가
import time 

# 🌟 로티 애니메이션 라이브러리 (없으면 에러 방지)
try:
    from streamlit_lottie import st_lottie
except ImportError:
    st.error("🚨 'streamlit-lottie' 라이브러리가 필요합니다. 터미널에 'pip install streamlit-lottie'를 입력해서 설치해주세요!")
    st.stop()

# --- 🔑 보안: API 키 설정 ---
try:
    KAKAO_REST_API_KEY = st.secrets["general"]["kakao_api_key"].strip()
except Exception:
    st.error("🚨 API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요!")
    st.stop()

# --- 🛠️ [핵심] 이미지 Base64 변환 함수 ---
def get_img_as_base64(file_path):
    """이미지 파일을 읽어서 HTML에서 쓸 수 있는 문자열로 변환합니다."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# --- 🎬 로티 애니메이션 설정 ---
@st.cache_data(show_spinner=False)
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# 🌟 지도 탐색 애니메이션 URL
LOTTIE_SEARCH_URL = "https://lottie.host/62371366-d480-4643-9047-80f215dc1cb3/0g2kX9Yd5S.json"
lottie_search_anim = load_lottieurl(LOTTIE_SEARCH_URL)


# --- 📍 전국 주요 핫플레이스 DB ---
NATIONWIDE_HOTSPOTS = {
    "서울 강남역": { "coords": (37.498095, 127.027610), "desc": "신분당선과 2호선이 만나는 교통 요지이자 맛집/쇼핑의 메카." },
    "서울 홍대입구": { "coords": (37.557527, 126.9244669), "desc": "버스킹, 클럽, 맛집이 모인 젊음의 거리이자 공항철도 접근성 최강." },
    "서울 건대입구역": { "coords": (37.540458, 127.069320), "desc": "건국대와 커먼그라운드를 중심으로 맛집, 술집, 쇼핑이 가득한 활기찬 젊음의 거리." },
    "서울 용산역": { "coords": (37.529886, 126.964801), "desc": "KTX 호남선의 중심이자 아이파크몰, 이태원 접근성이 뛰어난 곳." },
    "서울 종로3가": { "coords": (37.570415, 126.992161), "desc": "익선동 한옥거리와 포장마차, 서울의 중심에서 느끼는 레트로 감성." },
    "서울 잠실역": { "coords": (37.513261, 127.100133), "desc": "롯데월드몰과 석촌호수가 있어 쇼핑과 산책을 동시에 즐기는 데이트 성지." },
    "서울 사당역": { "coords": (37.476553, 126.981550), "desc": "경기 남부와 서울을 잇는 관문, 수많은 광역버스와 맛집이 모인 장소." },
    "서울 명동": { "coords": (37.560997, 126.986175), "desc": "외국인 관광객과 쇼핑의 중심지, 남산 타워가 보이는 서울의 랜드마크." },
    "서울 성수동": { "coords": (37.544579, 127.055967), "desc": "공장을 개조한 힙한 카페와 팝업스토어가 매일 열리는 트렌드 1번지." },
    "서울 왕십리역": { "coords": (37.561268, 127.037103), "desc": "4개 노선(2/5/중앙/분당)이 교차하는 환승 끝판왕, 엔터식스와 이마트까지." },
    "서울 광화문역": { "coords": (37.571648, 126.976372), "desc": "광화문 광장과 세종문화회관이 있는 강북의 상징이자 문화와 역사의 중심." },
    "서울 여의도역": { "coords": (37.521715, 126.924290), "desc": "더현대 서울, IFC몰, 한강공원이 어우러진 금융과 힐링의 핫플레이스." },
    "서울 을지로3가": { "coords": (37.566383, 126.992604), "desc": "낡은 골목 사이 숨겨진 힙한 바와 노가리 골목이 공존하는 뉴트로 성지." },
    "판교역 (아브뉴프랑)": { "coords": (37.394761, 127.111194), "desc": "현대백화점과 아브뉴프랑, IT 직장인들의 세련된 회식과 모임 장소." },
    "수원역 (로데오)": { "coords": (37.265679, 127.000047), "desc": "KTX와 1호선, 수인분당선이 만나는 경기 남부 최대의 교통 및 상권 중심." },
    "인천 부평역": { "coords": (37.489493, 126.724068), "desc": "거대 지하상가와 문화의 거리가 있는 인천의 핵심 요지." },
    "대전 둔산동": { "coords": (36.350412, 127.384548), "desc": "대전의 강남, 갤러리아 백화점과 핫한 술집이 모인 충청권 최대 번화가." },
    "대전역": { "coords": (36.332516, 127.434156), "desc": "전국 어디서나 오기 편한 KTX의 심장, 성심당 빵지순례의 필수 코스." },
    "천안 터미널": { "coords": (36.819830, 127.155822), "desc": "백화점, 터미널, 먹자골목이 하나로 합쳐진 천안의 명동." },
    "청주 터미널": { "coords": (36.626490, 127.432657), "desc": "청주 교통의 관문이자 NC백화점 등 쇼핑 인프라가 갖춰진 만남의 광장." },
    "강릉역": { "coords": (37.763740, 128.899484), "desc": "KTX 내리면 바로 바다 여행 시작, 중앙시장과 커피거리가 가까운 곳." },
    "원주 터미널": { "coords": (37.344463, 127.930492), "desc": "강원 영서 지방 최대 유흥가이자 교통의 허브." },
    "춘천 명동": { "coords": (37.880628, 127.727506), "desc": "닭갈비 골목과 지하상가, 춘천 낭만 여행의 시작점." },
    "부산 서면역": { "coords": (35.157816, 129.060033), "desc": "부산의 정중앙, 백화점과 맛집이 끝없이 펼쳐지는 부산 최대 핫플." },
    "부산역": { "coords": (35.115225, 129.042243), "desc": "대한민국 제2의 관문, 차이나타운과 탁 트인 광장이 반겨주는 곳." },
    "부산 해운대": { "coords": (35.163113, 129.163550), "desc": "대한민국 대표 해수욕장, 럭셔리한 맛집과 카페의 거리." },
    "대구 동성로": { "coords": (35.869666, 128.594038), "desc": "대구의 패션과 문화가 시작되는 곳, 거대한 상권이 밀집된 대구의 심장." },
    "동대구역": { "coords": (35.871435, 128.624925), "desc": "KTX와 신세계백화점이 결합된 복합환승센터, 영남권 교통의 허브." },
    "울산 삼산동": { "coords": (35.539622, 129.335967), "desc": "백화점과 관람차, 고속버스터미널이 모여 있는 울산 최고의 번화가." },
    "광주 충장로": { "coords": (35.148154, 126.915598), "desc": "광주의 명동, 패션 거리와 국립아시아문화전당이 있는 문화 중심지." },
    "광주 유스퀘어": { "coords": (35.160167, 126.879307), "desc": "아시아 최대 규모 버스터미널, 영화/쇼핑/외식을 한 번에 해결하는 복합공간." },
    "전주 한옥마을": { "coords": (35.814708, 127.152632), "desc": "고즈넉한 한옥과 길거리 음식이 가득한 대한민국 대표 관광 명소." }
}

# --- 🛠️ 함수 정의 ---
@st.cache_data(show_spinner=False)
def get_place_image(place_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(place_url, headers=headers, timeout=1.5)
        soup = BeautifulSoup(res.text, 'html.parser')
        img_tag = soup.find("meta", property="og:image")
        return img_tag["content"] if img_tag else None
    except:
        return None

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
    
    /* 이미지 크기 축소 */
    .place-img {
        width: 85px; height: 85px; object-fit: cover; 
        border-radius: 10px; border: 2px solid #000; margin-right: 15px;
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
        # 🌟 이미지를 Base64 코드로 변환해서 강제 출력
        icon_base64 = get_img_as_base64("favicon.png")
        
        if icon_base64:
            st.markdown(f"""
                <h1 style='display: flex; align-items: center;'>
                    <img src="data:image/png;base64,{icon_base64}" width='55' style='margin-right: 15px; margin-top: 5px;'>
                    MIDMEET
                </h1>
                """, unsafe_allow_html=True)
        else:
            # 이미지가 없으면 기본 타이틀 출력
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
            # 🌟 로딩 애니메이션
            if lottie_search_anim:
                loading_ph = st.empty()
                with loading_ph.container():
                    st.markdown("### 🏃‍♀️ 친구들 위치를 기반으로 열심히 찾고 있어요!")
                    st_lottie(lottie_search_anim, height=250, key="loading_main")
                time.sleep(1.5) 
                loading_ph.empty()

            st.session_state.step = "result"
            st.rerun()


# ==========================================
# 📺 화면 2: 결과 보기 (지도 + 추천)
# ==========================================
elif st.session_state.step == "result":
    
    col_back, col_res_title, col_vibe_change = st.columns([0.15, 0.45, 0.4])
    
    with col_back:
        if st.button("⬅️ 처음으로 돌아가기"):
            st.session_state.step = "input"
            for key in list(st.session_state.keys()):
                if key.startswith("view_mode_tab_"):
                    del st.session_state[key]
            st.rerun()
            
    with col_res_title:
        st.markdown("## 🎉 추천 결과")
        
    with col_vibe_change:
        st.session_state.vibe = st.selectbox(
            "목적 변경", 
            vibe_options,
            index=vibe_options.index(st.session_state.vibe),
            label_visibility="collapsed"
        )

    st.divider()

    is_any_detail_open = False
    for key in st.session_state:
        if key.startswith("view_mode_tab_") and st.session_state[key].startswith("detail_"):
            is_any_detail_open = True
            break

    if not is_any_detail_open:
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
        if not is_any_detail_open:
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
        if not is_any_detail_open:
            st.success(f"🔥 **{hotplaces[0]['place_name']}** 가 가장 합리적인 장소입니다!")

    if not hotplaces:
        st.warning("주변에 추천할만한 장소가 없네요 ㅠㅠ")
    else:
        tab_titles = [f"{i+1}위: {p['place_name']}" for i, p in enumerate(hotplaces)]
        tabs = st.tabs(tab_titles)

        for i, tab in enumerate(tabs):
            place = hotplaces[i]
            p_lat, p_lon = float(place['y']), float(place['x'])
            p_name = place['place_name']
            p_desc = place.get('desc', "") 
            
            view_state_key = f"view_mode_tab_{i}"
            if view_state_key not in st.session_state: st.session_state[view_state_key] = "list" 

            with tab:
                current_view = st.session_state[view_state_key]

                # --- [상세 지도 화면] ---
                if current_view.startswith("detail_"):
                    c_b, c_t = st.columns([0.2, 0.8])
                    with c_b:
                        if st.button("🔙 목록으로", key=f"back_{i}"):
                            st.session_state[view_state_key] = "list"
                            st.rerun()
                    
                    if current_view == "detail_play":
                        code = "AT4"; label="놀거리" 
                        details = get_nearby_details(p_lat, p_lon, "AT4") + get_nearby_details(p_lat, p_lon, "CT1")
                    elif current_view == "detail_food":
                        code = "FD6"; label="맛집"
                        details = get_nearby_details(p_lat, p_lon, code)
                        if st.session_state.vibe == "🍻 술/회식":
                            details.sort(key=lambda x: any(k in x['category_name'] or k in x['place_name'] for k in alcohol_kws), reverse=True)
                    else:
                        code = "CE7"; label="카페"
                        details = get_nearby_details(p_lat, p_lon, code)
                        if st.session_state.vibe == "📚 스터디/조용함":
                            details = [d for d in details if not ("보드" in d['place_name'] or "보드" in d['category_name'])]

                    st.markdown(f"### 🗺️ {p_name} 주변 {label}")
                    
                    m_detail = folium.Map(location=[p_lat, p_lon], zoom_start=15, tiles="cartodbpositron")
                    folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='star')).add_to(m_detail)
                    for item in details[:15]:
                        folium.Marker([float(item['y']), float(item['x'])], tooltip=item['place_name'], icon=folium.Icon(color='blue', icon='info-sign')).add_to(m_detail)
                    st_folium(m_detail, width="100%", height=400, key=f"map_d_{i}", returned_objects=[])
                    
                    st.write("---")
                    for x in details[:10]:
                        img_url = get_place_image(x['place_url'])
                        img_html = f'<img src="{img_url}" class="place-img">' if img_url else '<div class="place-img" style="background:#eee; display:flex; align-items:center; justify-content:center; color:#888;">No Img</div>'
                        st.markdown(f"""
                        <div class="place-container">
                            {img_html}
                            <div style="flex:1;">
                                <div style="font-weight:bold; font-size:1.15rem; margin-bottom:3px;">{x['place_name']}</div>
                                <div style="color:#666; font-size:0.9rem;">{x['category_name'].split(' > ')[-1]}</div>
                                <a href="{x['place_url']}" target="_blank" style="font-weight:bold; color:blue; font-size:0.9rem;">📍 카카오맵 보기</a>
                            </div>
                        </div>""", unsafe_allow_html=True)

                # --- [기본 결과 화면] ---
                else:
                    if p_desc: st.info(f"💡 {p_desc}")
                    
                    # 🌟 [영역 맞춤 지도] 친구들 + 중간지점 모두 포함
                    all_points = [[p_lat, p_lon]]
                    for c in coords.values():
                        all_points.append([c[0], c[1]])
                    
                    m = folium.Map(location=[p_lat, p_lon], tiles="cartodbpositron")
                    
                    folium.Marker([p_lat, p_lon], icon=folium.Icon(color='red', icon='star'), tooltip="중간지점").add_to(m)
                    
                    for idx, coord in coords.items():
                        fname = st.session_state.names.get(idx, f"친구 {idx+1}")
                        if idx < 4 and os.path.exists(friend_chars[idx]):
                            icon = folium.CustomIcon(friend_chars[idx], icon_size=(90, 90))
                            folium.Marker(coord, icon=icon, tooltip=fname).add_to(m)
                        else:
                            folium.Marker(coord, tooltip=fname).add_to(m)

                    # 🌟 여기가 핵심: 지도 자동 줌 조절
                    m.fit_bounds(all_points)

                    st_folium(m, width="100%", height=350, key=f"map_res_{i}", returned_objects=[])

                    c1, c2, c3 = st.columns(3)
                    
                    with c1: 
                        if st.button("🍴 맛집 보기", key=f"b_fd_{i}"):
                            # 🌟 로딩 애니메이션
                            if lottie_search_anim:
                                loading_ph = st.empty()
                                with loading_ph.container():
                                    st_lottie(lottie_search_anim, height=150, key=f"load_fd_{i}")
                                time.sleep(1.0)
                                loading_ph.empty()
                            st.session_state[view_state_key]="detail_food"; st.rerun()
                        foods = get_nearby_details(p_lat, p_lon, "FD6")
                        if st.session_state.vibe == "🍻 술/회식":
                            foods.sort(key=lambda x: any(k in x['category_name'] or k in x['place_name'] for k in alcohol_kws), reverse=True)
                        txt = ""
                        for x in foods[:5]:
                            txt += f"- {x['place_name']}\n"
                        st.markdown(txt)

                    with c2: 
                        if st.button("☕ 카페 보기", key=f"b_cf_{i}"): 
                            # 🌟 로딩 애니메이션
                            if lottie_search_anim:
                                loading_ph = st.empty()
                                with loading_ph.container():
                                    st_lottie(lottie_search_anim, height=150, key=f"load_cf_{i}")
                                time.sleep(1.0)
                                loading_ph.empty()
                            st.session_state[view_state_key]="detail_cafe"; st.rerun()
                        cafes = get_nearby_details(p_lat, p_lon, "CE7")
                        if st.session_state.vibe == "📚 스터디/조용함":
                            cafes = [d for d in cafes if not ("보드" in d['place_name'] or "보드" in d['category_name'])]
                        txt = ""
                        for x in cafes[:5]:
                            txt += f"- {x['place_name']}\n"
                        st.markdown(txt)

                    with c3: 
                        if st.button("🎡 놀거리 보기", key=f"b_pl_{i}"): 
                            # 🌟 로딩 애니메이션
                            if lottie_search_anim:
                                loading_ph = st.empty()
                                with loading_ph.container():
                                    st_lottie(lottie_search_anim, height=150, key=f"load_pl_{i}")
                                time.sleep(1.0)
                                loading_ph.empty()
                            st.session_state[view_state_key]="detail_play"; st.rerun()
                        plays = get_nearby_details(p_lat, p_lon, "AT4") + get_nearby_details(p_lat, p_lon, "CT1")
                        txt = ""
                        for x in plays[:5]:
                            txt += f"- {x['place_name']}\n"
                        st.markdown(txt)