import streamlit as st
import json
import os
import google.generativeai as genai

# 파일 저장 경로 설정
DATA_FILE = "tasks.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_data()
if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

# 🌟 구형/신형 API 키 모두 호환되는 안정적인 모델로 변경 완료
def ask_gemini_priority(selected_tasks, current_energy, api_key):
    try:
        # API 키 설정
        genai.configure(api_key=api_key)
        
        # 🛠️ 에러가 나던 gemini-1.5-flash 대신 가장 호환성이 높은 gemini-pro 모델로 전면 교체
        model = genai.GenerativeModel('gemini-pro')
        
        # AI에게 줄 미션(프롬프트) 작성
        tasks_str = "\n".join([f"- {t['title']} (중요도: {t['importance']}, 마감일: {t['due_date']})" for t in selected_tasks])
        
        prompt = f"""
        당신은 최고의 시간 관리 전문가 AI입니다. 
        사용자가 요청한 할 일 목록을 분석하여, 현재 사용자의 에너지 상태에 가장 적합한 우선순위로 다시 정렬해 주세요.
        
        [현재 사용자의 에너지 상태]: {current_energy}
        
        [할 일 목록]:
        {tasks_str}
        
        [요구사항]:
        1. 에너지 상태가 '하'라면 중요도가 높더라도 당장 큰 에너지가 들지 않는 일이나 마감이 급한 것 위주로 배치해 주세요.
        2. 에너지 상태가 '상'이라면 집중력이 필요하고 중요한 일을 먼저 처리하도록 배치해 주세요.
        3. 정렬된 순서대로 번호를 매겨주고, 왜 이 순서로 추천했는지 친절하고 설득력 있는 '추천 사유'를 각 항목마다 간단히 적어주세요.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}\nAPI 키가 올바른지 확인해 주세요."

# 앱 타이틀
st.title("📝 진짜 AI 기반 스마트 To-Do 플래너")

# 사이드바에 Gemini API 키 입력창 배치
st.sidebar.header("🔑 AI 설정")
api_key_input = st.sidebar.text_input("Google AI Studio API Key 입력", type="password")
st.sidebar.markdown("[무료 API Key 발급받기](https://aistudio.google.com/)")

# 와이어프레임 탭 생성
tab_star, tab_list, tab_ai = st.tabs(["⭐ 별표표시됨", "📋 내 할 일 목록", "🤖 AI 추천"])

def update_tasks():
    save_data(st.session_state.tasks)

# ==========================================
# 1. 내 할 일 목록 탭
# ==========================================
with tab_list:
    st.subheader("내 할 일 목록")
    sort_option = st.radio("정렬 순서", ["입력순", "이름순"], horizontal=True)
    
    incomplete_tasks = [t for t in st.session_state.tasks if not t["completed"]]
    if sort_option == "이름순":
        incomplete_tasks = sorted(incomplete_tasks, key=lambda x: x["title"])
    else:
        incomplete_tasks = incomplete_tasks[::-1]
        
    for idx, task in enumerate(incomplete_tasks):
        orig_idx = st.session_state.tasks.index(task)
        col_chk, col_txt, col_star, col_edit = st.columns([1, 5, 1, 1])
        
        with col_chk:
            task["selected"] = st.checkbox("", value=task.get("selected", False), key=f"chk_{orig_idx}", on_change=update_tasks)
        with col_txt:
            st.markdown(f"**{task['title']}** \n_⏳ {task['due_date']} | 중요도: {task['importance']}_")
        with col_star:
            star_icon = "⭐" if task["starred"] else "☆"
            if st.button(star_icon, key=f"star_{orig_idx}"):
                st.session_state.tasks[orig_idx]["starred"] = not task["starred"]
                update_tasks()
                st.rerun()
        with col_edit:
            if st.button("⚙️", key=f"edit_{orig_idx}"):
                st.session_state[f"edit_mode_{orig_idx}"] = True

        if st.session_state.get(f"edit_mode_{orig_idx}", False):
            with st.container(border=True):
                st.write("🔧 할 일 수정 및 취소")
                new_title = st.text_input("할 일 이름 변경", value=task["title"], key=f"new_title_{orig_idx}")
                new_due = st.text_input("마감일 변경", value=task["due_date"], key=f"new_due_{orig_idx}")
                new_imp = st.selectbox("중요도 변경", ["상", "중", "하"], index=["상", "중", "하"].index(task["importance"]), key=f"new_imp_{orig_idx}")
                
                c1, c2, c3 = st.columns(3)
                if c1.button("완료로 변경", key=f"comp_btn_{orig_idx}"):
                    st.session_state.tasks[orig_idx]["completed"] = True
                    st.session_state[f"edit_mode_{orig_idx}"] = False
                    update_tasks()
                    st.rerun()
                if c2.button("삭제(취소)", key=f"del_btn_{orig_idx}"):
                    st.session_state.tasks.pop(orig_idx)
                    st.session_state[f"edit_mode_{orig_idx}"] = False
                    update_tasks()
                    st.rerun()
                if c3.button("닫기", key=f"close_btn_{orig_idx}"):
                    st.session_state.tasks[orig_idx]["title"] = new_title
                    st.session_state.tasks[orig_idx]["due_date"] = new_due
                    st.session_state.tasks[orig_idx]["importance"] = new_imp
                    st.session_state[f"edit_mode_{orig_idx}"] = False
                    update_tasks()
                    st.rerun()

    st.write("---")
    completed_tasks = [t for t in st.session_state.tasks if t["completed"]]
    with st.expander(f"✔️ 완료됨 ({len(completed_tasks)}개)", expanded=False):
        for task in completed_tasks:
            orig_idx = st.session_state.tasks.index(task)
            cc1, cc2 = st.columns([6, 1])
            cc1.write(f"~~{task['title']}~~")
            if cc2.button("되돌리기", key=f"rev_{orig_idx}"):
                st.session_state.tasks[orig_idx]["completed"] = False
                update_tasks()
                st.rerun()

    with st.expander("➕ 새 할 일 추가하기", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            title_input = st.text_input("할 일 이름")
            col_d1, col_d2 = st.columns([3, 1])
            due_input_text = col_d1.text_input("마감일 입력 (예: 2026-06-07 18:00 또는 오늘 20시)")
            no_due = col_d2.checkbox("마감일 없음")
            importance_input = st.selectbox("중요도", ["상", "중", "하"])
            
            if st.form_submit_button("추가하기") and title_input:
                final_due = "마감일 없음" if no_due or not due_input_text else due_input_text
                st.session_state.tasks.append({
                    "title": title_input, "due_date": final_due, "importance": importance_input,
                    "starred": False, "completed": False, "selected": False
                })
                update_tasks()
                st.rerun()

# ==========================================
# 2. 별표표시됨 탭
# ==========================================
with tab_star:
    st.subheader("⭐ 별표 표시된 할 일")
    starred_tasks = [t for t in st.session_state.tasks if t["starred"] and not t["completed"]]
    if not starred_tasks:
        st.info("별표 표시된 할 일이 없습니다.")
    else:
        for task in starred_tasks:
            st.write(f"★ **{task['title']}** ({task['due_date']})")

# ==========================================
# 3. AI 추천 탭
# ==========================================
with tab_ai:
    st.subheader("🤖 AI 맞춤 우선순위 추천")
    selected_tasks = [t for t in st.session_state.tasks if t.get("selected", False) and not t["completed"]]
    
    if not selected_tasks:
        st.warning("분석할 할 일을 '내 할 일 목록' 탭에서 체크박스로 선택해 주세요.")
    else:
        st.write(f"분석 대상: **{len(selected_tasks)}개**")
        energy_level = st.radio("⚡ 지금 내 에너지 상태", ["상 (집중력 최고)", "중 (보통 상태)", "하 (지치고 힘듦)"], horizontal=True)
        
        if st.button("🚀 Gemini AI에게 추천받기"):
            if not api_key_input:
                st.error("사이드바에 Google Gemini API Key를 입력해야 진짜 AI가 작동합니다!")
            else:
                with st.spinner("Gemini AI가 할 일 목록과 남은 시간, 에너지를 분석 중입니다..."):
                    result = ask_gemini_priority(selected_tasks, energy_level, api_key_input)
                    st.session_state.ai_analysis_result = result
                    
        if st.session_state.ai_analysis_result:
            st.success("🎯 AI 전문가의 컨설팅 결과")
            st.info(st.session_state.ai_analysis_result)
