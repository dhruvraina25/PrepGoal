import streamlit as st
import time
import base64
import json
import requests
from datetime import time as dt_time, date, datetime
from io import BytesIO
try:
    GEMMA_API_KEY = st.secrets["GEMMA_API_KEY"]
except (KeyError, FileNotFoundError):
    GEMMA_API_KEY = ""

GEMMA_MODEL = "your-working-model-name"
GEMMA_API_KEY = st.secrets["GEMMA_API_KEY"]
GEMMA_MODEL = "gemma-4-26b-a4b-it"

# =============== AI CONFIGURATION ===============

st.set_page_config(
    page_title="PrepGoal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== THEME ====================
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:#080810;color:#f5f3ff;}
.block-container {max-width:1100px;padding-top:2rem;padding-bottom:3rem;}
.logo {font-size:42px;font-weight:850;letter-spacing:-2px;color:white;}
.logo span,.accent {color:#a78bfa;}
.subtitle {color:#a1a1b5;letter-spacing:1.5px;font-size:12px;}
.heading {font-size:34px;font-weight:800;letter-spacing:-1px;color:white;}
.description {color:#a1a1b5;margin:8px 0 24px;}
.panel {background:#11111c;border:1px solid #29263b;border-radius:16px;padding:20px;margin-bottom:14px;}
.metric {background:#11111c;border:1px solid #29263b;border-radius:14px;padding:16px;}
.metric-label {color:#a1a1b5;font-size:13px;}
.metric-value {font-size:27px;font-weight:800;color:#c4b5fd;}
div[data-testid="stForm"] {background:#11111c;border:1px solid #29263b;padding:22px;border-radius:16px;}
label {color:#e5e5f0 !important;}
input,textarea,div[data-baseweb="select"]>div {background:#191927 !important;color:white !important;border-color:#35334a !important;border-radius:9px !important;}
div.stButton>button,div[data-testid="stFormSubmitButton"]>button,div[data-testid="stDownloadButton"]>button {
background:#8b5cf6;color:white;border:0;border-radius:10px;min-height:42px;font-weight:700;
}
div.stButton>button:hover,div[data-testid="stFormSubmitButton"]>button:hover,div[data-testid="stDownloadButton"]>button:hover {background:#7c3aed;color:white;border:0;}
[data-testid="stFileUploader"] {background:#11111c;border-radius:12px;}
hr {border-color:#29263b;}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
defaults = {
    "stage": "welcome",
    "classes": [],
    "num_classes": 3,
    "tests": [],
    "xp": 0,
    "verified_classes": [],
    "verified_tests": [],
    "tasks_completed": 0,
    "streak": 1,
    "messages": [],
    "analysis": None,
    "profile": {},
    "last_xp_event": None,
    "attendance_reviews": {},
    "class_doubts": {},
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==================== SOUND ====================
def play_click_sound():
    """Plays prepgoal_click.wav if the file is beside this script."""
    try:
        with open("prepgoal_click.wav", "rb") as f:
            audio = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f'<audio autoplay><source src="data:audio/wav;base64,{audio}" type="audio/wav"></audio>',
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass

# ==================== GEMMA HELPERS ====================
def call_gemma(GEMMA_API_KEY, prompt, image_bytes=None, mime_type="image/jpeg", model="gemma-3-27b-it"):
    """Call Google's Generative Language API. Image support depends on the selected model."""
    if not GEMMA_API_KEY:
        raise ValueError("Add your Google AI API key in GEMMA_API_KEY near the top of this Python file.")
    parts = [{"text": prompt}]
    if image_bytes is not None:
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        })
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMMA_API_KEY}"
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.65, "topP": 0.9, "maxOutputTokens": 1200}},
        timeout=90
    )
    if not response.ok:
        raise RuntimeError(f"Gemma API error ({response.status_code}): {response.text[:500]}")
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Gemma returned no text. Check the model name and API access.")

def uploaded_mime(uploaded_file):
    return uploaded_file.type or "image/jpeg"

def safe_text(text):
    return str(text).replace("<", "&lt;").replace(">", "&gt;")

# ==================== SCREEN 1: WELCOME ====================
if st.session_state.stage == "welcome":
    st.markdown("""
    <div style="height:75vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;animation:fadein 1.2s ease;">
      <div style="width:85px;height:85px;border-radius:50%;background:#8b5cf6;box-shadow:0 0 70px 25px #6d28d9;margin-bottom:35px;"></div>
      <div class="logo">Prep<span>Goal</span></div>
      <div class="subtitle">YOUR GOALS. YOUR DISCIPLINE. YOUR FUTURE.</div>
    </div>
    <style>@keyframes fadein{from{opacity:0;transform:translateY(15px)}to{opacity:1;transform:translateY(0)}}</style>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.stage = "details"
    st.rerun()

# ==================== SCREEN 2: USER DETAILS ====================
elif st.session_state.stage == "details":
    st.markdown('<div class="heading">Start your <span class="accent">journey.</span></div><div class="description">First, let’s get to know you.</div>', unsafe_allow_html=True)
    with st.form("user_details"):
        name = st.text_input("Your name", placeholder="Enter your name")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Your age", min_value=10, max_value=100, value=None)
        with c2:
            student_class = st.selectbox("Your class / stage", ["Select your class", "Class 9", "Class 10", "Class 11", "Class 12", "Dropper", "College student", "Other"])
        exam = st.selectbox(
            "Which exam are you preparing for?",
            ["Select your exam", "JEE Main", "JEE Advanced", "NEET", "CUET", "Boards", "KCET", "Other"]
        )
        phone = st.text_input("Phone number (optional)", placeholder="Enter your phone number", max_chars=15)
        submitted = st.form_submit_button("Continue →", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Please enter your name.")
            elif age is None:
                st.error("Please enter your age.")
            elif student_class == "Select your class":
                st.error("Please select your class / stage.")
            elif exam == "Select your exam":
                st.error("Please select the exam you're preparing for.")
            else:
                st.session_state.profile = {
                    "name": name.strip(),
                    "age": age,
                    "class": student_class,
                    "exam": exam,
                    "phone": phone.strip()
                }
                st.session_state.stage = "mentor"
                play_click_sound()
                st.rerun()

# ==================== SCREEN 3: MEET NOVA ====================
elif st.session_state.stage == "mentor":
    name = st.session_state.profile.get("name", "there")
    st.markdown(f"""
    <div style="height:65vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;">
      <div style="width:75px;height:75px;border-radius:50%;background:#8b5cf6;box-shadow:0 0 55px 18px #6d28d9;margin-bottom:30px;"></div>
      <div class="subtitle">YOUR PERSONAL STUDY COMPANION</div>
      <div class="heading">Hey, <span class="accent">{safe_text(name)}!</span></div>
      <p style="font-size:21px;color:white;">I’m Gemma, your PrepGoal mentor.</p>
      <p style="color:#a1a1b5;max-width:560px;line-height:1.8;">I’ll help you organise your classes, track your preparation, understand your weak areas and keep moving toward your goals.</p>
      <div class="subtitle">LET’S BUILD YOUR ROUTINE</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.stage = "schedule"
    st.rerun()

# ==================== SCREEN 4: CLASS SCHEDULE ====================
elif st.session_state.stage == "schedule":
    st.markdown('<div class="heading">What are your <span class="accent">classes today?</span></div><div class="description">Add today’s classes and their timings so PrepGoal can help you track attendance and doubts.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ Add Another Class", use_container_width=True):
            st.session_state.num_classes += 1
            play_click_sound()
            st.rerun()
    with c2:
        if st.session_state.num_classes > 1 and st.button("− Remove Last Class", use_container_width=True):
            st.session_state.num_classes -= 1
            play_click_sound()
            st.rerun()
    with st.form("class_schedule"):
        entered = []
        for i in range(1, st.session_state.num_classes + 1):
            st.markdown(f"#### Today’s class {i}")
            subject = st.text_input(f"Subject {i}", placeholder="e.g. Physics", key=f"subject_{i}")
            c1, c2 = st.columns(2)
            with c1:
                start = st.time_input(f"Start time — Class {i}", value=dt_time(16, 0), key=f"start_{i}")
            with c2:
                end = st.time_input(f"End time — Class {i}", value=dt_time(17, 0), key=f"end_{i}")
            entered.append((subject, start, end))
            st.divider()
        if st.form_submit_button("Save My Schedule →", use_container_width=True):
            new_classes, error = [], None
            for subject, start, end in entered:
                if subject.strip():
                    if start >= end:
                        error = f"End time must be after start time for {subject.strip()}."
                        break
                    new_classes.append({"subject": subject.strip(), "start": start.strftime("%I:%M %p"), "end": end.strftime("%I:%M %p"), "id": f"class-{len(new_classes)+1}"})
            if error:
                st.error(error)
            elif not new_classes:
                st.error("Please enter at least one subject.")
            else:
                st.session_state.classes = new_classes
                st.session_state.stage = "dashboard"
                play_click_sound()
                st.rerun()

# ==================== MAIN DASHBOARD ====================
elif st.session_state.stage == "dashboard":
    profile = st.session_state.profile
    name = profile.get("name", "Student")

    with st.sidebar:
        st.markdown("## 🎯 PrepGoal")
        st.caption(f"Hi, {name}!")
        st.markdown("---")
        if st.button("Edit class schedule", use_container_width=True):
            st.session_state.stage = "schedule"
            st.rerun()
        if st.button("Restart onboarding", use_container_width=True):
            for key in ["stage", "profile", "classes", "tests", "xp", "verified_classes", "verified_tests", "tasks_completed", "streak", "messages", "analysis"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown(f'<div class="logo">Prep<span>Goal</span></div><div class="subtitle">YOUR PERSONAL STUDY DASHBOARD</div><br><div class="heading">Welcome back, <span class="accent">{safe_text(name)}</span></div><div class="description">Preparing for {safe_text(profile.get("exam", "your exam"))} · Small consistent steps make big results.</div>', unsafe_allow_html=True)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    metrics = [
        ("TOTAL XP", st.session_state.xp),
        ("CLASSES", len(st.session_state.verified_classes)),
        ("TESTS", len(st.session_state.verified_tests)),
        ("STREAK", f'{st.session_state.streak} day' + ('' if st.session_state.streak == 1 else 's'))
    ]
    for col, (label, value) in zip([m1, m2, m3, m4], metrics):
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    tab_today, tab_tests, tab_report, tab_nova = st.tabs(["📚 Classes & Tasks", "📝 Scheduled Tests", "📊 Performance & Report", "💬 Ask Gemma"])

    # ----- CLASSES / ATTENDANCE -----
    with tab_today:
        st.markdown("### Today’s class checklist")
        st.caption("Upload evidence for a class, then ask Gemma to review it. AI review is an aid, not definitive proof.")
        for idx, item in enumerate(st.session_state.classes):
            class_id = item.get("id", f"class-{idx+1}")
            verified = class_id in st.session_state.verified_classes
            with st.expander(f"{'✅' if verified else '⬜'} {item['subject']} · {item['start']}–{item['end']}", expanded=not verified):
                st.write(f"**Scheduled:** {item['start']} to {item['end']}")
                evidence = st.file_uploader("Upload attendance evidence (screenshot/image)", type=["png", "jpg", "jpeg", "webp"], key=f"attendance_upload_{class_id}")
                note = st.text_input("Optional context", placeholder="e.g. class platform and date", key=f"attendance_note_{class_id}")
                if st.button("Analyse attendance with Gemma", key=f"verify_class_{class_id}", use_container_width=True):
                    if evidence is None:
                        st.warning("Upload an image first.")
                    elif not GEMMA_API_KEY:
                        st.warning("Add your API key to GEMMA_API_KEY near the top of this Python file.")
                    else:
                        with st.spinner("Gemma is reviewing the image…"):
                            try:
                                result = call_gemma(
                                    GEMMA_API_KEY,
                                    "Review this image for possible evidence of attendance at an online class. "
                                    "Read visible class title, date, participant name, and any attendance indicators. "
                                    "User context: " + note + ". Student name: " + name + ". Scheduled subject: " + item["subject"] +
                                    ". Return concise findings, list visible evidence, list uncertainty, and end with exactly one line: "
                                    "RECOMMENDATION: ACCEPT or RECOMMENDATION: REVIEW. Do not claim authenticity or certainty.",
                                    evidence.getvalue(), uploaded_mime(evidence), GEMMA_MODEL)
                                st.session_state.attendance_reviews[class_id] = result
                            except Exception as exc:
                                st.error(str(exc))

                review = st.session_state.attendance_reviews.get(class_id)
                if review and not verified:
                    st.markdown("**Gemma’s attendance review**")
                    st.write(review)
                    if "RECOMMENDATION: ACCEPT" in review.upper():
                        st.warning("Gemma recommends acceptance. Please check the evidence yourself; AI output is not definitive proof.")
                        if st.button("Confirm attendance (+20 XP)", key=f"confirm_class_{class_id}"):
                            if class_id not in st.session_state.verified_classes:
                                st.session_state.verified_classes.append(class_id)
                                st.session_state.xp += 20
                                st.session_state.tasks_completed += 1
                            st.rerun()
                    else:
                        st.info("Gemma recommends reviewing this evidence. Check the screenshot or upload clearer evidence.")

                if verified:
                    st.success("Attendance confirmed · +20 XP")
                    st.markdown("#### 🧠 Class doubt check-in")
                    st.write(f"Did anything from **{item['subject']}** feel confusing today? Gemma can explain it step by step.")
                    doubt_key = f"doubt_text_{class_id}"
                    saved_doubt = st.session_state.class_doubts.get(class_id, {})
                    with st.form(f"doubt_form_{class_id}"):
                        has_doubt = st.radio(
                            "How was this class?",
                            ["I understood everything", "I have a doubt"],
                            index=1 if saved_doubt.get("question") else 0,
                            key=f"has_doubt_{class_id}",
                            horizontal=True,
                        )
                        doubt_text = st.text_area(
                            "Tell Gemma what confused you",
                            value=saved_doubt.get("question", ""),
                            placeholder="Example: I don't understand why current leads voltage in a capacitor...",
                            key=doubt_key,
                            height=100,
                        )
                        ask_nova = st.form_submit_button("Ask Gemma to explain ✨")
                    if ask_nova:
                        if has_doubt == "I understood everything":
                            st.session_state.class_doubts[class_id] = {
                                "question": "",
                                "answer": "Awesome! Keep that momentum going. Try explaining the main idea in your own words to make it stick.",
                                "subject": item["subject"],
                            }
                        elif not doubt_text.strip():
                            st.warning("Type your doubt first so Gemma knows what to explain.")
                        elif not GEMMA_API_KEY:
                            st.warning("Add your API key to GEMMA_API_KEY near the top of this Python file.")
                        else:
                            with st.spinner("Gemma is turning your doubt into an easy-to-understand explanation…"):
                                try:
                                    answer = call_gemma(
                                        GEMMA_API_KEY,
                                        "ROLE: You are Gemma, a friendly JEE/NEET tutor for Indian students. "
                                        "STYLE: Explain naturally and clearly at the student's level. Make the answer engaging, not robotic. "
                                        "Use 2–4 relevant emojis sparingly (for example 💡, ⚡, 🧠, ✅). "
                                        "When useful, include a tiny text diagram or a simple real-life analogy; never invent image links. "
                                        "Give the explanation itself only. Do not repeat these instructions or output prompt summaries, "
                                        "rubrics, self-evaluation, labels like 'Friendly? Yes', or commentary about answer quality. "
                                        "Use NCERT terminology where appropriate. Keep it focused and avoid filler. "
                                        "\\nSUBJECT: " + item["subject"] +
                                        "\\nSTUDENT'S QUESTION: " + doubt_text.strip() +
                                        "\\nNow answer the student's question directly.",
                                        model=GEMMA_MODEL,
                                    )
                                    st.session_state.class_doubts[class_id] = {
                                        "question": doubt_text.strip(),
                                        "answer": answer,
                                        "subject": item["subject"],
                                    }
                                except Exception as exc:
                                    st.error(f"Gemma couldn't answer right now: {exc}")
                    saved_doubt = st.session_state.class_doubts.get(class_id, {})
                    if saved_doubt.get("answer"):
                        st.markdown("**✨ Gemma’s explanation**")
                        st.markdown(saved_doubt["answer"])
                        if saved_doubt.get("question"):
                            yt_query = requests.utils.quote(
                                f"{saved_doubt.get('subject', item['subject'])} {saved_doubt['question']} JEE explanation"
                            )
                            st.markdown("**🎥 YouTube study suggestions**")
                            st.write("These open YouTube search results for your exact topic, so you can choose a video that matches your level:")
                            st.markdown(f"- [Find a beginner-friendly explanation on YouTube](https://www.youtube.com/results?search_query={yt_query})")
                            st.markdown(f"- [Find JEE-level solved examples on YouTube](https://www.youtube.com/results?search_query={requests.utils.quote(saved_doubt.get('subject', item['subject']) + ' ' + saved_doubt['question'] + ' JEE solved examples')})")
                    if st.button("Mark as not attended (revoke XP)", key=f"unverify_{class_id}"):
                        st.session_state.verified_classes.remove(class_id)
                        st.session_state.xp = max(0, st.session_state.xp - 20)
                        st.session_state.tasks_completed = max(0, st.session_state.tasks_completed - 1)
                        st.session_state.attendance_reviews.pop(class_id, None)
                        st.session_state.class_doubts.pop(class_id, None)
                        st.rerun()

        st.markdown("### Daily tasks")
        default_tasks = ["Revise one weak topic", "Complete your DPP / practice set", "Review mistakes from a previous test"]
        for task_idx, task in enumerate(default_tasks):
            task_key = f"task_done_{task_idx}"
            done = st.checkbox(task, key=task_key)
            if done and not st.session_state.get(f"awarded_{task_key}", False):
                st.session_state.xp += 5
                st.session_state.tasks_completed += 1
                st.session_state[f"awarded_{task_key}"] = True
            elif not done and st.session_state.get(f"awarded_{task_key}", False):
                st.session_state.xp = max(0, st.session_state.xp - 5)
                st.session_state.tasks_completed = max(0, st.session_state.tasks_completed - 1)
                st.session_state[f"awarded_{task_key}"] = False

    # ----- TESTS -----
    with tab_tests:
        st.markdown("### Add a scheduled test")
        with st.form("add_test_form", clear_on_submit=True):
            test_name = st.text_input("Test name", placeholder="e.g. Full syllabus mock 04")
            test_date = st.date_input("Test date", value=date.today())
            test_subjects = st.text_input("Subjects included", placeholder="Physics, Chemistry, Mathematics")
            add_test = st.form_submit_button("＋ Add Scheduled Test", use_container_width=True)
            if add_test:
                if not test_name.strip():
                    st.error("Enter a test name.")
                else:
                    st.session_state.tests.append({
                        "id": f"test-{len(st.session_state.tests)+1}",
                        "name": test_name.strip(),
                        "date": test_date.isoformat(),
                        "subjects": test_subjects.strip(),
                        "result": None,
                        "marks": None,
                        "verified": False
                    })
                    st.success("Test added.")
                    st.rerun()

        if not st.session_state.tests:
            st.info("No scheduled tests yet. Add your first test above.")
        for test in st.session_state.tests:
            with st.expander(f"{'✅' if test['verified'] else '📝'} {test['name']} · {test['date']}"):
                st.write(f"**Subjects:** {test['subjects'] or 'Not specified'}")
                result_image = st.file_uploader("Upload test result / marks image", type=["png", "jpg", "jpeg", "webp"], key=f"result_image_{test['id']}")
                if st.button("Read marks with Gemma", key=f"read_marks_{test['id']}", use_container_width=True):
                    if result_image is None:
                        st.warning("Upload a result image first.")
                    elif not GEMMA_API_KEY:
                        st.warning("Add your API key to GEMMA_API_KEY near the top of this Python file.")
                    else:
                        with st.spinner("Gemma is reading the marks…"):
                            try:
                                result = call_gemma(
                                    GEMMA_API_KEY,
                                    "Read this test-result image. Extract the student name if visible and subject-wise marks. "
                                    "Return valid JSON only in this schema: {\"student_name\":\"\", \"subjects\":[{\"subject\":\"Physics\","
                                    "\"marks_obtained\":0,\"maximum_marks\":0,\"weak_topics\":[]}], \"overall_observations\":\"\","
                                    "\"uncertainties\":[]}. Do not invent unreadable values; use null and explain uncertainty. "
                                    "If the image contains no marks, say so.",
                                    result_image.getvalue(), uploaded_mime(result_image), GEMMA_MODEL)
                                st.markdown("**Gemma extraction**")
                                st.code(result, language="json")
                                test["result"] = result
                                try:
                                    cleaned = result.strip()
                                    if cleaned.startswith("```"):
                                        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                                    test["marks"] = json.loads(cleaned)
                                    test["verified"] = True
                                    if test["id"] not in st.session_state.verified_tests:
                                        st.session_state.verified_tests.append(test["id"])
                                        st.session_state.xp += 30
                                        st.session_state.tasks_completed += 1
                                    st.success("Marks extracted. Please review the extracted values before relying on them. +30 XP")
                                except json.JSONDecodeError:
                                    st.warning("Gemma's response wasn't valid JSON. The raw response is saved; try again or review it manually.")
                            except Exception as exc:
                                st.error(str(exc))
                if test.get("marks"):
                    st.markdown("#### Subject-wise scores")
                    subjects_data = test["marks"].get("subjects", [])
                    if subjects_data:
                        st.dataframe(subjects_data, use_container_width=True, hide_index=True)
                        weak = []
                        for sub in subjects_data:
                            obtained = sub.get("marks_obtained")
                            maximum = sub.get("maximum_marks")
                            if isinstance(obtained, (int, float)) and isinstance(maximum, (int, float)) and maximum > 0:
                                pct = obtained / maximum * 100
                                if pct < 60:
                                    weak.append(f"{sub.get('subject', 'Subject')} ({pct:.0f}%)")
                        if weak:
                            st.warning("Priority subjects to revise: " + ", ".join(weak))
                        else:
                            st.success("No subject below the 60% review threshold was detected from the extracted scores.")
                    if st.button("Mark test as not verified (revoke XP)", key=f"unverify_test_{test['id']}"):
                        if test["id"] in st.session_state.verified_tests:
                            st.session_state.verified_tests.remove(test["id"])
                            st.session_state.xp = max(0, st.session_state.xp - 30)
                            st.session_state.tasks_completed = max(0, st.session_state.tasks_completed - 1)
                        test["verified"] = False
                        st.rerun()

    # ----- PERFORMANCE / PDF -----
    with tab_report:
        st.markdown("### Performance overview")
        all_scores = []
        weak_subjects = []
        for test in st.session_state.tests:
            marks = test.get("marks")
            if marks:
                for sub in marks.get("subjects", []):
                    obtained = sub.get("marks_obtained")
                    maximum = sub.get("maximum_marks")
                    if isinstance(obtained, (int, float)) and isinstance(maximum, (int, float)) and maximum > 0:
                        pct = obtained / maximum * 100
                        all_scores.append({"Test": test["name"], "Subject": sub.get("subject", "Subject"), "Marks": f"{obtained:g}/{maximum:g}", "Percentage": round(pct, 1)})
                        if pct < 60:
                            weak_subjects.append(sub.get("subject", "Subject"))
        if all_scores:
            st.dataframe(all_scores, use_container_width=True, hide_index=True)
            unique_weak = sorted(set(weak_subjects))
            if unique_weak:
                st.markdown("#### 🔎 Focus areas")
                for subject in unique_weak:
                    st.markdown(f"- **{safe_text(subject)}** — prioritise concept revision and targeted practice.")
            else:
                st.success("Your extracted scores are all at or above the 60% review threshold.")
        else:
            st.info("Your subject-wise analysis will appear here after you upload a test result and Gemma extracts the marks.")

        remarks = st.text_area("Gemma's report remarks (optional)", placeholder="Add your reflections or next steps...")
        if st.button("Generate PDF progress report", use_container_width=True):
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, title="PrepGoal Progress Report")
                styles = getSampleStyleSheet()
                story = [
                    Paragraph("PrepGoal Progress Report", styles["Title"]),
                    Spacer(1, 12),
                    Paragraph(f"Student: {safe_text(name)}", styles["Normal"]),
                    Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", styles["Normal"]),
                    Spacer(1, 12),
                    Paragraph(f"Credit score (XP): {st.session_state.xp}", styles["Heading2"]),
                    Paragraph(f"Tasks completed: {st.session_state.tasks_completed}", styles["Normal"]),
                    Paragraph(f"Attendance confirmed: {len(st.session_state.verified_classes)} / {len(st.session_state.classes)}", styles["Normal"]),
                    Paragraph(f"Tests with extracted results: {len([t for t in st.session_state.tests if t.get('marks')])}", styles["Normal"]),
                    Paragraph(f"Streak: {st.session_state.streak} day(s) (demo counter)", styles["Normal"]),
                    Spacer(1, 14),
                    Paragraph("Subject-wise scores", styles["Heading2"])
                ]
                table_data = [["Test", "Subject", "Marks", "Percent"]]
                for row in all_scores:
                    table_data.append([row["Test"], row["Subject"], row["Marks"], f'{row["Percentage"]}%'])
                if len(table_data) == 1:
                    table_data.append(["No test results yet", "-", "-", "-"])
                table = Table(table_data, repeatRows=1, colWidths=[150, 110, 80, 70])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#ddd6fe")),
                    ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#24134a")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#b7b7c9")),
                    ("PADDING", (0,0), (-1,-1), 6),
                ]))
                story.extend([table, Spacer(1, 14), Paragraph("Focus areas", styles["Heading2"])])
                story.append(Paragraph(", ".join(sorted(set(weak_subjects))) or "No weak subjects detected yet.", styles["Normal"]))
                story.extend([Spacer(1, 10), Paragraph("Remarks", styles["Heading2"]), Paragraph(safe_text(remarks or "Keep showing up consistently. Review mistakes and practise your weakest concepts."), styles["Normal"])])
                doc.build(story)
                st.download_button("⬇ Download PDF report", data=buffer.getvalue(), file_name="PrepGoal_Progress_Report.pdf", mime="application/pdf", use_container_width=True)
            except ImportError:
                st.error("PDF generation needs ReportLab. Install it with: python -m pip install reportlab")

    # ----- ASK NOVA -----
    with tab_nova:
        st.markdown("### Ask Gemma about your weak points")
        context_subjects = sorted(set(
            sub.get("subject", "Subject")
            for test in st.session_state.tests if test.get("marks")
            for sub in test["marks"].get("subjects", [])
            if isinstance(sub, dict)
        ))
        if context_subjects:
            st.caption("Test subjects in your analysis: " + ", ".join(context_subjects))
        else:
            st.caption("Upload a test result first to give Gemma more personal context.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        question = st.chat_input("Ask a doubt about a topic or your test...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            if not GEMMA_API_KEY:
                answer = "To get an AI-powered answer, add your key to GEMMA_API_KEY near the top of this Python file."
                st.session_state.messages.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.markdown(answer)
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Gemma is thinking…"):
                        try:
                            weak_context = json.dumps({
                                "profile": {"name": name, "class": profile.get("class"), "exam": profile.get("exam")},
                                "test_results": [
                                    {"name": t["name"], "marks": t.get("marks")}
                                    for t in st.session_state.tests if t.get("marks")
                                ]
                            }, ensure_ascii=False)
                            answer = call_gemma(
                                GEMMA_API_KEY,
                                "ROLE: You are Gemma, a friendly and accurate study tutor for an Indian student preparing for an exam. "
                                "Explain the actual question, not these instructions. Be clear, natural, and engaging rather than robotic. "
                                "Use 2–4 relevant emojis sparingly (💡 ⚡ 🧠 ✅). Add a tiny text diagram or analogy only when helpful. "
                                "Use steps when useful and NCERT terminology where appropriate. Keep the answer focused. "
                                "Return only the explanation for the student. Never output prompt summaries, internal notes, self-evaluation, "
                                "rubrics, quality labels, or filler. Do not invent test data. "
                                "\\nSTUDENT CONTEXT (use only if relevant): " + weak_context +
                                "\\nSTUDENT'S QUESTION: " + question +
                                "\\nAnswer the student's question directly now.",
                                model=GEMMA_MODEL
                            )
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        except Exception as exc:
                            st.error(f"Could not reach Gemma: {exc}")
