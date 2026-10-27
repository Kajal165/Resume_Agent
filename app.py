
# Regular expressions se AI report ke score aur counts nikalne ke liye
import re

# Streamlit se web application banane ke liye
import streamlit as st

# PDF resume se text extract karne ke liye
from resume_parser import extract_resume_text

# Resume aur Job Description compare karne wale agent ke liye
from resume_agent import generate_match_report


# --------------------------------------------------
# 1. Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Resume and Job Matching Agent",
    page_icon="📄",
    layout="wide"
)


# --------------------------------------------------
# 2. Application Header
# --------------------------------------------------

st.title("📄 Resume and Job Matching Agent")

st.write(
    "Apna resume aur Job Description compare karein, "
    "skills ka match dekhein aur improvement suggestions paayein."
)

st.caption(
    "Note: Match score ek approximate assessment hai, "
    "hiring probability nahi."
)


# --------------------------------------------------
# 3. Sidebar
# --------------------------------------------------

with st.sidebar:
    st.title("🤖 Resume Agent")

    st.write("### Kaise use karein?")

    st.markdown(
        """
        1. Apna PDF resume upload karein.
        2. Job Description paste karein.
        3. Analyze Resume par click karein.
        4. Match score aur detailed report dekhein.
        5. Report ko download bhi kar sakte hain.
        """
    )

    st.divider()

    st.info(
        "Best results ke liye text-based PDF resume "
        "aur complete Job Description use karein."
    )


# --------------------------------------------------
# 4. Resume Upload Section
# --------------------------------------------------

st.subheader("1. 📎 Upload Your Resume")

uploaded_file = st.file_uploader(
    "Apna resume PDF upload karein",
    type=["pdf"],
    help="Filhaal sirf PDF format supported hai."
)


# --------------------------------------------------
# 5. Job Description Section
# --------------------------------------------------

st.subheader("2. 💼 Job Description")

job_description = st.text_area(
    "Job Description yahan paste karein",
    height=220,
    placeholder=(
        "Example:\n"
        "Required Skills: Python, SQL, Azure...\n"
        "Experience: 2-4 years...\n"
        "Responsibilities: ..."
    )
)


# --------------------------------------------------
# 6. Analyze Button
# --------------------------------------------------

if st.button(
    "🔍 Analyze Resume",
    type="primary",
    use_container_width=True
):

    # Check karein ki resume upload hua hai ya nahi
    if uploaded_file is None:
        st.error("Please pehle apna PDF resume upload karein.")

    # Check karein ki Job Description enter ki gayi hai ya nahi
    elif not job_description.strip():
        st.error("Please Job Description paste karein.")

    else:
        try:
            # Analysis ke dauraan loading message dikhayein
            with st.spinner(
                "Resume analyze ho raha hai. Please wait..."
            ):

                # Step 1: PDF se resume ka text nikaalein
                resume_text = extract_resume_text(
                    uploaded_file.getvalue()
                )

                # Step 2: Resume aur JD ko AI agent se analyze karein
                report = generate_match_report(
                    resume_text,
                    job_description.strip()
                )

            # --------------------------------------------------
            # 7. AI Report Se Score Aur Counts Extract Karein
            # --------------------------------------------------

            # Match score nikaalein
            score_match = re.search(
                r"MATCH_SCORE:\s*(\d{1,3})",
                report,
                re.IGNORECASE
            )

            # Matching skills ka count nikaalein
            matching_match = re.search(
                r"MATCHING_SKILLS_COUNT:\s*(\d+)",
                report,
                re.IGNORECASE
            )

            # Partial matches ka count nikaalein
            partial_match = re.search(
                r"PARTIAL_MATCHES_COUNT:\s*(\d+)",
                report,
                re.IGNORECASE
            )

            # No evidence requirements ka count nikaalein
            missing_match = re.search(
                r"NO_EVIDENCE_COUNT:\s*(\d+)",
                report,
                re.IGNORECASE
            )

            # --------------------------------------------------
            # 8. Report Display
            # --------------------------------------------------

            st.success("Resume analysis complete!")

            # Agar AI expected format mein fields return nahi karta
            if not all([
                score_match,
                matching_match,
                partial_match,
                missing_match
            ]):

                st.warning(
                    "AI report mein expected score fields nahi mile. "
                    "Neeche detailed report di gayi hai."
                )

                st.subheader("📋 Detailed Matching Report")
                st.markdown(report)

            else:
                # Regular expression se actual numeric values lein
                score = int(score_match.group(1))
                matching = int(matching_match.group(1))
                partial = int(partial_match.group(1))
                missing = int(missing_match.group(1))

                # Score aur counts ki basic validation
                total_requirements = matching + partial + missing

                if not (
                    0 <= score <= 100
                    and total_requirements > 0
                ):
                    st.warning(
                        "AI ne invalid score ya requirement counts "
                        "return kiye hain. Detailed report neeche hai."
                    )

                    st.markdown(report)

                else:
                    # ------------------------------------------
                    # 9. Match Score
                    # ------------------------------------------

                    st.subheader("📊 Resume Match Score")

                    score_col, info_col = st.columns([1, 2])

                    with score_col:
                        st.metric(
                            label="Estimated Match",
                            value=f"{score}%"
                        )

                    with info_col:
                        st.write("**Match Score Progress**")
                        st.progress(score / 100)

                        st.caption(
                            "Yeh score AI ke assessment par based hai."
                        )

                    st.divider()

                    # ------------------------------------------
                    # 10. Skill Count Metrics
                    # ------------------------------------------

                    st.subheader("🧩 Skills Matching Overview")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            label="✅ Matching",
                            value=matching
                        )

                    with col2:
                        st.metric(
                            label="🟡 Partial Matches",
                            value=partial
                        )

                    with col3:
                        st.metric(
                            label="⚪ No Resume Evidence",
                            value=missing
                        )

                    st.caption(
                        "No Resume Evidence ka matlab hai ki "
                        "resume mein us skill ka clear evidence "
                        "nahi mila; iska matlab yeh nahi ki "
                        "candidate ko woh skill aati hi nahi."
                    )

                    st.divider()

                    # ------------------------------------------
                    # 11. Detailed Report
                    # ------------------------------------------

                    st.subheader("📋 Detailed Matching Report")

                    # Report ke starting machine-readable headers
                    # ko clean display ke liye hata dein
                    clean_report = re.sub(
                        r"^\s*(MATCH_SCORE|MATCHING_SKILLS_COUNT|"
                        r"PARTIAL_MATCHES_COUNT|NO_EVIDENCE_COUNT)"
                        r"\s*:\s*\d+\s*",
                        "",
                        report,
                        flags=re.IGNORECASE | re.MULTILINE
                    ).strip()

                    st.markdown(clean_report or report)

                    # ------------------------------------------
                    # 12. Download Report
                    # ------------------------------------------

                    st.download_button(
                        label="⬇️ Download Matching Report",
                        data=(
                            f"Resume and Job Matching Report\n\n"
                            f"Estimated Match: {score}%\n"
                            f"Matching Skills: {matching}\n"
                            f"Partial Matches: {partial}\n"
                            f"No Resume Evidence: {missing}\n\n"
                            f"{clean_report or report}"
                        ),
                        file_name="resume_matching_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

        # --------------------------------------------------
        # 13. Error Handling
        # --------------------------------------------------

        except Exception as error:
            st.error(
                "Resume analysis complete nahi ho saka. "
                "Please input aur configuration check karein."
            )

            with st.expander("View Technical Error"):
                st.code(str(error))


# --------------------------------------------------
# 14. Footer
# --------------------------------------------------

st.divider()

st.caption(
    "Built with Streamlit, LangChain and Groq | "
    "Resume analysis assistant"
)
