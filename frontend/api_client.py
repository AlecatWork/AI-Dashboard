""" 
Centralized function for every call the streamlit app makes to the backend.
"""

import json
import time

import requests
import streamlit as st


API = st.secrets.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 10


def _headers(token: str | None = None) -> dict:
    headers ={"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _result(r: requests.Response):
    """Turn a requests.Response into a consistent tuple"""
    try:
        body = r.json()
    except ValueError:
        body = {}
    if r.status_code == 401:
        return False, "Unauthorized - please log in again."
    if 200 <= r.status_code < 300:
        return True, body
    return False, body.get("detail", f"Request failed ({r.status_code})")



# helper functions

def api_get(endpoint, token=None, params=None):
    try:
        r = requests.get(f"{API}{endpoint}", headers=_headers(token), params=params,timeout=TIMEOUT)

    except requests.exceptions.ConnectionError:
        return False, "Can't reach the backend. Is it running?"
    return _result(r)



def api_post(endpoint, token=None, data=None):
    try:
        r = requests.post(f"{API}{endpoint}", headers=_headers(token), json=data,timeout=TIMEOUT)

    except requests.exceptions.ConnectionError:
        return False, "Can't reach the backend. Is it running?"
    return _result(r)



def api_patch(endpoint, token=None, data=None):
    try:
        r = requests.patch(f"{API}{endpoint}", headers=_headers(token), json=data,timeout=TIMEOUT)

    except requests.exceptions.ConnectionError:
        return False, "Can't reach the backend. Is it running?"
    return _result(r)



def api_delete(endpoint, token=None):
    try:
        r = requests.delete(f"{API}{endpoint}", headers=_headers(token), timeout=TIMEOUT)

    except requests.exceptions.ConnectionError:
        return False, "Can't reach the backend. Is it running?"
    if r.status_code == 204:
        return True, {}
    return _result(r)


# auth

def register(name: str, email: str, password: str):
    return api_post("/auth/register", data={"name": name, "email": email, "password": password})


def login(email: str, password: str):
    ok, body = api_post("/auth/login", data={"email": email, "password": password})
    if not ok:
        return False, body
    token = body.get("access_token")
    if not token:
        return False, "Login succeeded but no access_token was returned."
    return True, token


# tasks
def get_tasks(token: str, completed: bool | None = None, priority: str | None = None):
    params = {}
    if completed is not None:
        params["completed"] = completed
    if priority:
        params["priority"] = priority
    return api_get("/tasks", token=token, params=params)


def create_task(token: str, title: str, description: str = "", priority: str = "medium"):
    return api_post(
        "/tasks", token=token, data={"title": title, "description": description, "priority": priority}
    )


def updated_task(token: str, task_id: int, **fields):
    return api_patch(f"/tasks/{task_id}", token=token, data=fields)


def delete_task(token: str, task_id: int):
    return api_delete(f"/tasks/{task_id}", token=token)





# ai chat
_PLACEHOLDER_KEYS = {"", "sk-ant-key-here", "sk-ant-..."}

def stream_chat_response(messages: list[dict], tasks: list[dict] | None = None):
    api_key = (st.secrets.get("OPENAI_API_KEY") or "").strip()
    if api_key in _PLACEHOLDER_KEYS:
        yield from _stream_mock_response(messages, tasks)
        return
    yield from _stream_real_response(messages, tasks, api_key)


def _mock_reply(user_message: str, tasks: list[dict] | None) -> str:
    tasks = tasks or []
    pending = [t for t in tasks if not t.get("completed")]
    done = [t for t in tasks if t.get("completed")]
    high_priority = [t for t in pending if t.get("priority") == "high"]
    msg = user_message.lower()

    if not tasks:
        return (
            "You don't have any tasks yet - add one on the Tasks tab and "
            "I can help you think through what to focus on."
        )
    
    if any(word in msg for word in ("priorit", "focus", "next", "should i")):
        if high_priority:
            names = ", ".join(t.get("title", "untitled") for t in high_priority[:3])
            return f"You have {len(high_priority)} high-priority task(s) open: {names}. I'd start there."
        if pending:
            return (
                f"Nothing's marked high priority right now, but you still have "
                f"{len(pending)} pending task(s). The oldest one is probably worth tackling first."
            )
        return "Everything's marked complete - nothing urgent to focus on. "
    
    if any(word in msg for word in ("how many", "count", "total")):
        return f"You have {len(tasks)} task(s) total: {len(pending)} pending, {len(done)} completed."
    
    if any(word in msg for word in ("done", "complet", "finish")):
        if done:
            names = ", ".join(t.get("title", "untitled") for t in done[:3])
            return f"You've completed {len(done)} task(s), including: {names}."
        return (
            f"(Mock response - no OPENAI_API_KEY set yet.) Right now you have "
            f"{len(pending)} pending task(s) out of {len(tasks)} total."
        )
    return (
        f"You currently have {len(pending)} pending task(s) and {len(done)} completed task(s). "
        "Ask me about priority, completed tasks, or overall counts!"
    )
    

def _stream_mock_response(messages: list[dict], tasks: list[dict] | None):
    user_message = messages[-1]["content"] if messages else ""
    reply = _mock_reply(user_message, tasks)
    for word in reply.split(" "):
        yield word + " "
        time.sleep(0.03)


def _stream_real_response(messages: list[dict], tasks: list[dict] | None, api_key: str):
    system_prompt = (
        "You are a helpful assistant embedded in a personal task manager app."
        "Answer questions about the user's tasks and offer practical suggestions."
    )
    if tasks:
        task_lines = "\n".join(
            f"- [{'x' if t.get('completed') else ' '}] "
            f"({t.get('priority', 'n/a')}) {t.get('title', '')}"
            for t in tasks
        )
        system_prompt += f"\n\nThe user's current tasks:\n{task_lines}"

    openai_messages = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "max_tokens": 500,
                "messages": openai_messages,
                "stream": True,
            },
            stream=True,
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        yield "Can't reach the OpenAI API."
        return
 
    if resp.status_code != 200:
        yield f"AI request failed ({resp.status_code}): {resp.text[:200]}"
        return
 
    for line in resp.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data:"):
            continue
        data_str = decoded[len("data:"):].strip()
        if data_str == "[DONE]":
            break
        try:
            event = json.loads(data_str)
            choices = event.get("choices", [])
            if choices:
                content = choices[0].get("delta", {}).get("content")
                if content:
                    yield content
        except json.JSONDecodeError:
            continue
    
    

