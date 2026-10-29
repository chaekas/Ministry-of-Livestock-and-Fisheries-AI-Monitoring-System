"""Ministry of Livestock and Fisheries AI Monitoring System."""
import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import (
    count_users,
    create_inspection,
    get_dashboard_summary,
    initialize_database,
    list_inspections,
    record_audit,
)
from security.authentication import (
    authenticate_user,
    create_user,
    list_users,
)

st.set_page_config(
    page_title="Ministry AI Monitoring System",
    page_icon="🐄",
    layout="wide",
)

initialize_database()

MODULES = {
    "Livestock Counting": "Detect and count supported livestock in images or videos.",
    "Fish Counting": "Count visible fish in suitable tanks, channels, or videos.",
    "Animal Health Screening": "Flag visible abnormalities for veterinary review; this is not a diagnosis.",
    "Fish Species Identification": "Identify supported fish species using a model trained on labelled examples.",
    "Livestock Movement Monitoring": "Track animals crossing designated entry and exit lines.",
}


def show_header():
    st.title("Ministry of Livestock and Fisheries")
    st.caption("AI Monitoring and Decision-Support System")
    st.divider()


def show_initial_setup():
    show_header()
    st.subheader("Initial Administrator Setup")
    st.warning(
        "Create the first administrator account. Use a strong, unique password. "
        "This is a development prototype; do not enter real sensitive ministry data yet."
    )
    with st.form("initial_admin_setup"):
        username = st.text_input("Administrator username")
        password = st.text_input("Password (minimum 12 characters)", type="password")
        confirmation = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create administrator")
    if submitted:
        if not username.strip():
            st.error("Enter a username.")
            return
        if password != confirmation:
            st.error("The passwords do not match.")
            return
        if count_users() != 0:
            st.error("Setup has already been completed. Refresh and sign in.")
            st.rerun()
        try:
            create_user(username, password, "admin")
            record_audit(username.strip(), "initial_admin_created", "First administrator created")
            st.success("Administrator account created. Sign in with your new credentials.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Could not create the account. The username may already exist.")


def show_login():
    show_header()
    st.subheader("Authorized User Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        user = authenticate_user(username, password)
        if user is None:
            st.error("Invalid username or password.")
            return
        st.session_state["user"] = user
        record_audit(user["username"], "login", "Successful login")
        st.rerun()


def show_dashboard():
    user = st.session_state["user"]
    with st.sidebar:
        st.title("Navigation")
        st.caption(f"Signed in: {user['username']}")
        st.caption(f"Role: {user['role'].title()}")
        section = st.radio(
            "Open module",
            ["Dashboard", *MODULES.keys(), "New Inspection", "Reports", "User Management"],
        )
        if st.button("Sign out", use_container_width=True):
            record_audit(user["username"], "logout", "User signed out")
            st.session_state.pop("user", None)
            st.rerun()

    show_header()

    if section == "Dashboard":
        summary = get_dashboard_summary()
        st.subheader("Executive Dashboard")
        a, b, c = st.columns(3)
        a.metric("Saved inspections", summary["inspections"])
        b.metric("Active user accounts", summary["active_users"])
        c.metric("Planned AI modules", len(MODULES))
        st.subheader("Monitoring modules")
        for title, description in MODULES.items():
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(description)
                st.caption("Phase 1 foundation — AI integration is scheduled for later phases.")
        st.info("Dashboard statistics come from the application's database. No sample operational figures are fabricated.")

    elif section in MODULES:
        st.subheader(section)
        st.write(MODULES[section])
        st.warning(
            "The page is ready, but its specialized YOLO model is not connected yet. "
            "This module will be implemented and tested in a later phase."
        )
        st.write("For now, use New Inspection to save a manually verified record.")

    elif section == "New Inspection":
        st.subheader("Create an Inspection Record")
        with st.form("inspection_form"):
            module = st.selectbox("Module", list(MODULES.keys()))
            location = st.text_input("District, facility, or location")
            subject = st.text_input("Livestock type, fish species, or subject")
            notes = st.text_area("Notes or verified observations")
            submitted = st.form_submit_button("Save inspection")
        if submitted:
            if not location.strip() or not notes.strip():
                st.error("Location and notes are required.")
            else:
                record_id = create_inspection(
                    module, location.strip(), subject.strip(), notes.strip(), user["username"]
                )
                record_audit(user["username"], "inspection_created", f"Inspection ID {record_id}")
                st.success(f"Inspection record #{record_id} saved.")

    elif section == "Reports":
        st.subheader("Inspection Reports")
        records = list_inspections()
        if not records:
            st.info("No inspection records have been saved yet.")
        else:
            dataframe = pd.DataFrame(records)
            st.dataframe(dataframe, use_container_width=True, hide_index=True)
            counts = (
                dataframe.groupby("module", as_index=False)
                .size()
                .rename(columns={"size": "Inspection count"})
            )
            st.plotly_chart(
                px.bar(counts, x="module", y="Inspection count", title="Inspections by module"),
                use_container_width=True,
            )
            st.download_button(
                "Download inspection CSV",
                dataframe.to_csv(index=False).encode("utf-8"),
                file_name="ministry_inspections.csv",
                mime="text/csv",
            )

    elif section == "User Management":
        if user["role"] != "admin":
            st.error("Only administrators can manage accounts.")
            return
        st.subheader("User Management")
        with st.form("create_user_form"):
            new_username = st.text_input("New username")
            new_password = st.text_input("Temporary password (minimum 12 characters)", type="password")
            role = st.selectbox("Role", ["officer", "supervisor", "admin"])
            submitted = st.form_submit_button("Create user")
        if submitted:
            try:
                create_user(new_username, new_password, role)
                record_audit(user["username"], "user_created", f"Created account {new_username.strip()}")
                st.success("User account created.")
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Could not create the account. The username may already exist.")
        st.subheader("Existing accounts")
        users = list_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)


def main():
    if count_users() == 0:
        show_initial_setup()
    elif "user" not in st.session_state:
        show_login()
    else:
        show_dashboard()


main()
