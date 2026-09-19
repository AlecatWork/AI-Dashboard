

import pandas as pd
import plotly.express as px 
import streamlit as st
import api_client as api




st.set_page_config(page_title="AI Task Dashboard", page_icon="✅", layout="wide")


# session state init
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def logout():
    st.session_state.token = None
    st.session_state.user_email = None
    st.session_state.tasks = []



#  auth gate
def render_login():
    st.title("📈 Ai Task Dashboard")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            with st.spinner("Logging in..."):
                ok, result = api.login(email, password)
            if ok:
                st.session_state.token = result
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error(result)

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_submitted = st.form_submit_button("Create account") 

        if reg_submitted:
            with st.spinner("Creating account..."):
                ok, result = api.register(name, reg_email, reg_password)
            if ok:
                st.success("Account created - log in on the other tab.")
            else:
                st.error(result)



if not st.session_state.token:
    render_login()
    st.stop()



# sidebar
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state.user_email}**")
    if st.button("Log out"):
        logout()
        st.rerun()

    st.divider()
    st.subheader("Filters")
    filter_completed = st.selectbox("Status", ["All", "Completed", "Pending"])
    filter_priority = st.selectbox("Priority", ["All", "low", "medium", "high"])



def load_tasks():
    completed_param = None
    if filter_completed == "Completed":
        completed_param = True
    elif filter_completed == "Pending":
        completed_param = False
    priority_param = None if filter_priority == "All" else filter_priority

    with st.spinner("Loading tasks..."):
        ok, result = api.get_tasks(
            st.session_state.token, completed=completed_param, priority=priority_param
        )
    if not ok:
        if "401" in str(result) or "auth" in str(result).lower():
            st.error("Session expired — please log in again.")
            logout()
            st.rerun()
        st.error(f"Couldn't load tasks: {result}")
        return []
    return result

st.session_state.tasks = load_tasks()
tasks = st.session_state.tasks
df = pd.DataFrame(tasks)


# main layout
st.title("AI Task Dashboard")

tab_dashboard, tab_tasks, tab_ai = st.tabs(["📊 Dashboard", "📝 Tasks", "🤖 AI Assistant"])


# dashboard tab
with tab_dashboard:
    total = len(df)
    done = int(df["completed"].sum()) if total and "completed" in df else 0
    pending = total - done

    col1, col2, col3 = st.columns(3)
    col1.metric("Total tasks", total)
    col2.metric("Completed", done)
    col3.metric("Pending", pending)

    if total:
        st.subheader("Tasks by priority")
        if "priority" in df.columns:
            priority_counts = df["priority"].value_counts().reset_index()
            priority_counts.columns = ["priority", "count"]
            fig = px.bar(priority_counts, x="priority", y="count")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("All tasks")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tasks yet - add one on the Tasks tab.")


# tasks tab
with tab_tasks:
    st.subheader("Add a task")
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description", height=80)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        create_submitted = st.form_submit_button("➕ Add task")


    if create_submitted:
        if not title.strip():
            st.warning("Title is required.")
        else:
            with st.spinner("Creating task..."):
                ok, result = api.create_task(
                    st.session_state.token, title, description, priority
                )
            if ok:
                st.success("Task created.")
                st.rerun()
            else:
                st.error(f"Couldn't create task: {result}")


    st.divider()
    st.subheader("Existing tasks")

    if not tasks:
        st.info("Nothing to show yet.")
    for t in tasks:
        c1, c2, c3 = st.columns([5, 1, 1])
        c1.write(f"**{t.get('title')}** - {t.get('priority', 'n/a')}")
        if c2.button("✅" if not t.get("completed") else "↩️", key=f"toggle_{t['id']}"):
            ok, result = api.updated_task(
                st.session_state.token, t["id"], completed=not t.get("completed")
            )
            if ok:
                st.rerun()
            else:
                st.error(f"Couldn't update task: {result}")
        if c3.button("🗑️", key=f"delete_{t['id']}"):
            ok, result = api.delete_task(st.session_state.token, t["id"])
            if ok:
                st.rerun()
            else:
                st.error(f"Couldn't delete task: {result}")



# ai assistant 

with tab_ai:
    st.subheader("Chat about your tasks")
    st.caption("The assistant can see your current task list.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask something about your tasks..."):
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            response_text = st.write_stream(
                api.stream_chat_response(st.session_state.chat_history + [{"role": "user", "content": user_input}], tasks=tasks)
            )
        
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
      
