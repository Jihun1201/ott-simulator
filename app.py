import streamlit as st
import json
import heapq

# --- 기본 설정 ---
GENRE_MAP = {
    28: "액션", 12: "모험", 16: "애니메이션", 35: "코미디", 80: "범죄", 
    18: "드라마", 10751: "가족", 14: "판타지", 36: "역사", 
    27: "공포", 10402: "음악", 9648: "미스터리", 10749: "로맨스", 878: "SF", 
    10770: "TV 영화", 53: "스릴러", 10752: "전쟁", 37: "서부",
    10759: "액션/어드벤처", 10762: "아동", 10763: "뉴스", 10764: "리얼리티", 
    10765: "SF/판타지", 10766: "소프", 10767: "토크", 10768: "전쟁/정치"
}

if 'users' not in st.session_state:
    st.session_state.users = {
        "User A (액션 매니아)": {"history": [], "genre_weights": {}},
        "User B (드라마/예능 러버)": {"history": [], "genre_weights": {}},
        "User C (다양성 탐험가)": {"history": [], "genre_weights": {}}
    }
if 'genre_choice' not in st.session_state:
    st.session_state.genre_choice = "전체"

@st.cache_data
def load_data():
    try:
        with open("ultimate_ott_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            categorized = {}
            for item in data:
                cat = item.get("category_type", "기타")
                if cat not in categorized: categorized[cat] = []
                categorized[cat].append(item)
            return data, categorized
    except FileNotFoundError:
        return [], {}

movies, categorized_movies = load_data()

# --- 상세 정보 팝업 ---
@st.dialog("📋 콘텐츠 상세 정보", width="large")
def show_details(movie):
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if movie.get('poster_path'):
            st.image(movie['poster_path'], width='stretch')
    with col_info:
        st.header(movie['title'])
        st.write(f"**카테고리:** {movie.get('category_type', '미분류')}")
        st.write(f"**평점:** ⭐ {movie.get('vote_average', 0)}")
        st.divider()
        st.subheader("줄거리")
        st.write(movie.get('overview', '상세 줄거리 정보가 없습니다.'))
    if st.button("닫기", width='stretch'):
        st.rerun()

# --- 로직 함수 ---
def watch_content(movie, user_data):
    # 최신순 정렬 (기존 것 삭제 후 맨 앞 삽입)
    user_data['history'] = [m for m in user_data['history'] if m['title'] != movie['title']]
    user_data['history'].insert(0, movie) 
    for genre_id in movie.get('genre_ids', []):
        genre_name = GENRE_MAP.get(genre_id, "기타")
        user_data['genre_weights'][genre_name] = user_data['genre_weights'].get(genre_name, 0) + 10
    st.toast(f"✅ 시청 완료: {movie['title']}")

def remove_history(movie_title, user_data):
    for i, m in enumerate(user_data['history']):
        if m['title'] == movie_title:
            for genre_id in m.get('genre_ids', []):
                genre_name = GENRE_MAP.get(genre_id, "기타")
                if genre_name in user_data['genre_weights']:
                    user_data['genre_weights'][genre_name] -= 10
                    if user_data['genre_weights'][genre_name] <= 0:
                        del user_data['genre_weights'][genre_name]
            user_data['history'].pop(i)
            break
    st.rerun()

def get_pq(user_data):
    pq = []
    watched_titles = [m['title'] for m in user_data['history']]
    for idx, movie in enumerate(movies):
        if movie['title'] in watched_titles: continue
        score = sum(user_data['genre_weights'].get(GENRE_MAP.get(gid, "기타"), 0) for gid in movie.get('genre_ids', []))
        if score > 0: heapq.heappush(pq, (-score, idx, movie))
    return pq

# --- 레이아웃 ---
st.set_page_config(layout="wide", page_title="OTT Simulator")

# 사이드바 (정렬 보정 완료)
st.sidebar.title("🎬 설정")
selected_user = st.sidebar.selectbox("👤 사용자", list(st.session_state.users.keys()))
user_data = st.session_state.users[selected_user]
zoom_mode = st.sidebar.checkbox("🔍 분석 모드 크게 보기")

st.sidebar.divider()
st.sidebar.subheader("🕒 시청 기록 (최신순)")
if user_data['history']:
    if st.sidebar.button("♻️ 전체 초기화", width='stretch'):
        user_data['history'] = []
        user_data['genre_weights'] = {}
        st.rerun()

if not user_data['history']:
    st.sidebar.info("기록 없음")
else:
    for m in user_data['history']:
        # [핵심] vertical_alignment="center" 추가하여 한 줄 정렬
        c_n, c_b = st.sidebar.columns([0.75, 0.25], vertical_alignment="center")
        with c_n:
            if st.button(f"• {m['title']}", key=f"h_{m['title']}", width='stretch'):
                show_details(m)
        with c_b:
            if st.button("❌", key=f"d_{m['title']}", width='stretch'):
                remove_history(m['title'], user_data)

# --- 메인 화면 로직 (스크롤 상단 이동 및 정렬 반영) ---
if zoom_mode:
    st.header("📊 알고리즘 심층 분석")
    col_t, col_q = st.columns(2)
else:
    col_movies, col_dash = st.columns([6, 4])

with (col_dash if not zoom_mode else st.container()):
    if not zoom_mode:
        st.subheader("🔥 맞춤 추천 TOP 5")
        pq = get_pq(user_data)
        if pq:
            top_5 = [pq[i][2] for i in range(min(5, len(pq)))]
            t_cols = st.columns(5)
            for i, m in enumerate(top_5):
                with t_cols[i]: st.markdown(f"<div style='height: 160px;'><img src='{m['poster_path']}' style='width:100%; height:100%; object-fit:cover; border-radius:5px;'></div>", unsafe_allow_html=True)
            for i, m in enumerate(top_5):
                with t_cols[i]:
                    st.markdown("<div style='height: 80px; margin-top: 5px;'>", unsafe_allow_html=True)
                    if st.button(m['title'], key=f"top_t_{i}", width='stretch'): show_details(m)
                    st.markdown("</div>", unsafe_allow_html=True)
            for i, m in enumerate(top_5):
                with t_cols[i]:
                    if st.button("시청", key=f"top_w_{i}", type="primary", width='stretch'):
                        watch_content(m, user_data)
                        st.rerun()
        st.divider()

    c1, c2 = (col_t, col_q) if zoom_mode else (st.container(), st.container())
    with c1:
        st.subheader("🌳 선호도 트리")
        if user_data['genre_weights']:
            dot = 'digraph T { node [shape=box, style=filled]; Root [label="사용자 취향"];'
            for g, w in user_data['genre_weights'].items():
                dot += f'"{g}" [label="{g}\\n({w}점)", fillcolor="#d4efdf"]; Root -> "{g}" [penwidth={max(1, w/10)}];'
            dot += '}'
            st.graphviz_chart(dot, width='stretch')
    with c2:
        st.subheader("⚡ 우선순위 큐")
        pq = get_pq(user_data)
        if pq:
            dot_q = 'digraph Q { node [shape=ellipse, style=filled, fillcolor="#d6eaf8"];'
            for i in range(min(15, len(pq))):
                s, _, m = pq[i]
                title = m['title'][:8] + ".." if len(m['title']) > 8 else m['title']
                dot_q += f'{i} [label="{-s}점\\n{title}"];'
                if i > 0: dot_q += f'{(i-1)//2} -> {i};'
            dot_q += '}'
            st.graphviz_chart(dot_q, width='stretch')

if not zoom_mode:
    with col_movies:
        st.header("📺 콘텐츠 브라우저")
        cat_list = (["전체"] + list(categorized_movies.keys()))
        new_choice = st.selectbox("📂 카테고리 필터", cat_list, index=cat_list.index(st.session_state.genre_choice))
        
        if new_choice != st.session_state.genre_choice:
            st.session_state.genre_choice = new_choice
            st.rerun()

        display_list = movies if st.session_state.genre_choice == "전체" else categorized_movies.get(st.session_state.genre_choice, [])

        with st.container(height=800, border=True, key=f"cont_{st.session_state.genre_choice}"):
            rows = (len(display_list) // 3) + 1
            for r in range(rows):
                batch = display_list[r*3 : r*3+3]
                if not batch: continue
                cols = st.columns(3)
                for i, m in enumerate(batch):
                    with cols[i]: st.markdown(f"<div style='height: 320px;'><img src='{m['poster_path']}' style='width:100%; height:100%; object-fit:cover; border-radius:5px;'></div>", unsafe_allow_html=True)
                for i, m in enumerate(batch):
                    with cols[i]:
                        st.markdown("<div style='height: 75px; margin-top: 10px;'>", unsafe_allow_html=True)
                        if st.button(m['title'], key=f"t_{st.session_state.genre_choice}_{r}_{i}", width='stretch'): show_details(m)
                        st.markdown("</div>", unsafe_allow_html=True)
                for i, m in enumerate(batch):
                    with cols[i]:
                        if st.button("▶️ 시청하기", key=f"w_{st.session_state.genre_choice}_{r}_{i}", type="primary", width='stretch'):
                            watch_content(m, user_data)
                            st.rerun()
                st.divider()