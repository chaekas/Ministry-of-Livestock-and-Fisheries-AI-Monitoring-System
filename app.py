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
from services.fish_counting import (
    count_image,
    count_video_sampled_frames,
    get_model_path,
    load_model,
)
from services.livestock_counting import (
    count_video_sampled_frames as count_livestock_video_sampled_frames,
    get_model_path as get_livestock_model_path,
    load_model as load_livestock_model,
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




def show_fish_counting(user):
    """Interactive fish-counting page using a locally supplied custom YOLO model."""
    st.subheader("Fish Counting")
    st.write(
        "Upload a fish image or video to detect visible fish with the configured "
        "YOLO model. Review every result before saving it as an official inspection."
    )
    model_path = get_model_path()
    st.caption(f"Configured model path: {model_path}")

    if not model_path.is_file():
        st.warning(
            "The fish model is not installed yet. Install the optional AI dependencies, "
            "then run 'python scripts/download_fish_model.py' as described in README.md. "
            "The supplied starter model is intended for grayscale underwater footage."
        )
        st.code(str(model_path), language="text")
        st.info(
            "Use a model trained for fish detection. Generic YOLO weights may not "
            "contain a fish class and should not be treated as a fish-counting model. "
            "You can still capture a photo here, but AI counting needs the model file."
        )

    tab_image, tab_video = st.tabs(["Count from image", "Analyse video"])
    result_summary = None

    with tab_image:
        camera_image = st.camera_input("Take a fish photo at the market", key="fish_camera")
        uploaded_image = st.file_uploader(
            "Or upload a fish image", type=["jpg", "jpeg", "png", "webp"], key="fish_image"
        )
        image_file = camera_image if camera_image is not None else uploaded_image
        image_confidence = st.slider(
            "Image detection confidence", 0.10, 0.90, 0.35, 0.05, key="fish_image_confidence"
        )
        if image_file is not None and st.button("Detect fish in image", key="detect_fish_image"):
            try:
                from PIL import Image
                import io

                image = Image.open(io.BytesIO(image_file.getvalue())).convert("RGB")
                with st.spinner("Loading model and detecting fish..."):
                    model = load_model()
                    count, annotated = count_image(model, image, image_confidence)
                st.session_state["fish_count_result"] = {
                    "kind": "image",
                    "count": count,
                    "summary": f"YOLO detected {count} fish in the uploaded image.",
                    "annotated": annotated,
                }
            except Exception as exc:
                st.error(f"Fish detection could not be completed: {exc}")

        current = st.session_state.get("fish_count_result")
        if current and current.get("kind") == "image":
            st.metric("Fish detections in image", current["count"])
            if current.get("annotated") is not None:
                st.image(current["annotated"], caption="Annotated detections", use_container_width=True)
            result_summary = current["summary"]

    with tab_video:
        video_file = st.file_uploader(
            "Upload a fish video", type=["mp4", "mov", "avi", "mkv"], key="fish_video"
        )
        video_confidence = st.slider(
            "Video detection confidence", 0.10, 0.90, 0.35, 0.05, key="fish_video_confidence"
        )
        if video_file is not None and st.button("Analyse sampled video frames", key="detect_fish_video"):
            import tempfile

            suffix = "." + video_file.name.rsplit(".", 1)[-1].lower()
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix) as temp_video:
                    temp_video.write(video_file.getvalue())
                    temp_video.flush()
                    with st.spinner("Sampling video frames and detecting fish..."):
                        model = load_model()
                        frame_counts = count_video_sampled_frames(
                            model, temp_video.name, confidence=video_confidence
                        )
                peak = max(item["fish_count"] for item in frame_counts)
                summary = (
                    f"Sampled {len(frame_counts)} frames. Peak observed count was {peak} "
                    "fish in a single sampled frame; this is not a unique-fish total."
                )
                st.session_state["fish_count_result"] = {
                    "kind": "video",
                    "count": peak,
                    "summary": summary,
                    "frames": frame_counts,
                }
            except Exception as exc:
                st.error(f"Video analysis could not be completed: {exc}")

        current = st.session_state.get("fish_count_result")
        if current and current.get("kind") == "video":
            st.metric("Peak detections in a sampled frame", current["count"])
            st.caption(current["summary"])
            st.dataframe(pd.DataFrame(current["frames"]), use_container_width=True, hide_index=True)
            result_summary = current["summary"]

    current = st.session_state.get("fish_count_result")
    if current and result_summary:
        st.divider()
        st.subheader("Save reviewed result")
        st.warning(
            "AI detections are estimates. Verify the result before saving it as an "
            "inspection record."
        )
        with st.form("save_fish_count_result"):
            location = st.text_input("District, facility, tank, or channel location")
            verified_count = st.number_input(
                "Verified fish count", min_value=0, value=int(current["count"]), step=1
            )
            notes = st.text_area("Verification notes")
            save_result = st.form_submit_button("Save verified inspection")
        if save_result:
            if not location.strip() or not notes.strip():
                st.error("Location and verification notes are required.")
            else:
                record_id = create_inspection(
                    "Fish Counting",
                    location.strip(),
                    "Fish",
                    f"AI result: {current['summary']} Officer-verified count: "
                    f"{int(verified_count)}. Verification notes: {notes.strip()}",
                    user["username"],
                )
                record_audit(
                    user["username"],
                    "fish_count_result_saved",
                    f"Inspection ID {record_id}; verified count {int(verified_count)}",
                )
                st.success(f"Verified fish-counting inspection #{record_id} saved.")


def show_livestock_counting(user):
    """Livestock counting page with camera capture and uploaded media."""
    st.subheader("Livestock Counting")
    st.write(
        "Take a photo directly with your device camera or upload a photo/video "
        "from a livestock market. Review detections before saving an inspection."
    )
    model_path = get_livestock_model_path()
    st.caption(f"Configured model path: {model_path}")
    if not model_path.is_file():
        st.warning(
            "A trained livestock YOLO model is not installed yet. Add suitable "
            "weights at the path shown above or set LIVESTOCK_YOLO_MODEL. The "
            "application will not substitute generic weights or invent counts."
        )

    tab_image, tab_video = st.tabs(["Count from photo", "Analyse uploaded video"])
    result_summary = None

    with tab_image:
        camera_image = st.camera_input("Take a livestock photo at the market", key="livestock_camera")
        uploaded_image = st.file_uploader(
            "Or upload a livestock photo", type=["jpg", "jpeg", "png", "webp"], key="livestock_image"
        )
        image_file = camera_image if camera_image is not None else uploaded_image
        confidence = st.slider(
            "Detection confidence", 0.10, 0.90, 0.35, 0.05, key="livestock_confidence"
        )
        if image_file is not None and st.button("Count livestock in photo", key="count_livestock_image"):
            try:
                from PIL import Image
                import io

                image = Image.open(io.BytesIO(image_file.getvalue())).convert("RGB")
                with st.spinner("Loading livestock model and detecting animals..."):
                    model = load_livestock_model()
                    count, annotated = count_image(model, image, confidence)
                st.session_state["livestock_count_result"] = {
                    "kind": "image",
                    "count": count,
                    "summary": f"Model detected {count} objects in the livestock photo.",
                    "annotated": annotated,
                }
            except Exception as exc:
                st.error(f"Livestock counting could not be completed: {exc}")

        current = st.session_state.get("livestock_count_result")
        if current and current.get("kind") == "image":
            st.metric("Detections in photo", current["count"])
            if current.get("annotated") is not None:
                st.image(current["annotated"], caption="Annotated detections", use_container_width=True)
            result_summary = current["summary"]

    with tab_video:
        video_file = st.file_uploader(
            "Upload a livestock market video", type=["mp4", "mov", "avi", "mkv"], key="livestock_video"
        )
        video_confidence = st.slider(
            "Video detection confidence", 0.10, 0.90, 0.35, 0.05, key="livestock_video_confidence"
        )
        if video_file is not None and st.button("Analyse sampled video frames", key="count_livestock_video"):
            import tempfile

            suffix = "." + video_file.name.rsplit(".", 1)[-1].lower()
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix) as temp_video:
                    temp_video.write(video_file.getvalue())
                    temp_video.flush()
                    with st.spinner("Sampling video frames and detecting livestock..."):
                        model = load_livestock_model()
                        frame_counts = count_livestock_video_sampled_frames(
                            model, temp_video.name, confidence=video_confidence
                        )
                peak = max(item["animal_count"] for item in frame_counts)
                summary = (
                    f"Sampled {len(frame_counts)} frames. Peak observed detections were {peak} "
                    "in one sampled frame; this is not a unique-animal total."
                )
                st.session_state["livestock_count_result"] = {
                    "kind": "video",
                    "count": peak,
                    "summary": summary,
                    "frames": frame_counts,
                }
            except Exception as exc:
                st.error(f"Livestock video analysis could not be completed: {exc}")

        current = st.session_state.get("livestock_count_result")
        if current and current.get("kind") == "video":
            st.metric("Peak detections in one sampled frame", current["count"])
            st.caption(current["summary"])
            st.dataframe(pd.DataFrame(current["frames"]), use_container_width=True, hide_index=True)
            result_summary = current["summary"]

    current = st.session_state.get("livestock_count_result")
    if current and result_summary:
        st.divider()
        st.subheader("Save reviewed result")
        st.warning("AI detections are estimates. Verify the count before saving an inspection.")
        with st.form("save_livestock_count_result"):
            location = st.text_input("Market, district, or facility location")
            subject = st.selectbox("Livestock category", ["Cattle", "Goats", "Sheep", "Mixed livestock", "Other"])
            verified_count = st.number_input(
                "Verified animal count", min_value=0, value=int(current["count"]), step=1
            )
            notes = st.text_area("Verification notes")
            save_result = st.form_submit_button("Save verified inspection")
        if save_result:
            if not location.strip() or not notes.strip():
                st.error("Location and verification notes are required.")
            else:
                record_id = create_inspection(
                    "Livestock Counting",
                    location.strip(),
                    subject,
                    f"AI result: {current['summary']} Officer-verified count: "
                    f"{int(verified_count)}. Verification notes: {notes.strip()}",
                    user["username"],
                )
                record_audit(
                    user["username"],
                    "livestock_count_result_saved",
                    f"Inspection ID {record_id}; verified count {int(verified_count)}",
                )
                st.success(f"Verified livestock-counting inspection #{record_id} saved.")


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

    elif section == "Fish Counting":
        show_fish_counting(user)

    elif section == "Livestock Counting":
        show_livestock_counting(user)

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
