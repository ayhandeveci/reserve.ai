
import streamlit as st

def section_toggle(state_key: str, label: str = "Aktif mi?") -> bool:
    default = st.session_state.get(state_key, False)
    active = st.toggle(label, value=default, key=state_key)
    return active

def secure_delete(keys):
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
