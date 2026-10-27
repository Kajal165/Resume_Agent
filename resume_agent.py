import os
import re

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def generate_match_report(resume_text: str, job_description: str) -> str:

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
    )

    prompt = """
    You are a Resume and Job Matching Assistant.

    RESUME:
    {resume}

    JOB DESCRIPTION:
    {job_description}

    INSTRUCTIONS:
    1. Identify distinct requirements from the job description.
    2. Count each requirement only once.
    3. Classify each into exactly one: Matching (clear resume evidence),
       Partial (some evidence), No Evidence (no clear evidence).
    4. Do not invent skills. No evidence does not mean the candidate lacks the skill.
    5. Keep counts consistent with the requirements listed in the report.
    6. Do not use protected characteristics in any judgement.
    7. Keep the report concise (maximum 700 words), using short bullet points.

    OUTPUT FORMAT (follow exactly, first three lines must be these):
    MATCHING_SKILLS_COUNT: <number>
    PARTIAL_MATCHES_COUNT: <number>
    NO_EVIDENCE_COUNT: <number>

    Then the report with these sections:
    - Overall Match Summary
    - Matching Skills with Resume Evidence
    - Partial Matches
    - Skills with No Resume Evidence
    - Experience and Project Alignment
    - Learning Recommendations
    - Suggested Resume Improvements
    """

    final_prompt = prompt.format(
        resume=resume_text[:18000],
        job_description=job_description[:12000]
    )

    output = llm.invoke(final_prompt).content

    def get_count(name):
        m = re.search(rf"{name}:\s*(\d+)", output, re.IGNORECASE)
        if not m:
            raise ValueError(f"AI output mein {name} nahi mila. Dobara try karein.")
        return int(m.group(1))

    matching = get_count("MATCHING_SKILLS_COUNT")
    partial = get_count("PARTIAL_MATCHES_COUNT")
    missing = get_count("NO_EVIDENCE_COUNT")

    total = matching + partial + missing
    if total == 0:
        raise ValueError("AI could not identify any job requirements.")

    score = round(((matching + 0.5 * partial) / total) * 100)

    # AI ki count lines hata kar report ka baaki hissa lein
    body = re.sub(
        r"^\s*(MATCHING_SKILLS_COUNT|PARTIAL_MATCHES_COUNT|NO_EVIDENCE_COUNT)\s*:\s*\d+\s*$",
        "",
        output,
        flags=re.IGNORECASE | re.MULTILINE
    ).strip()

    return f"""MATCH_SCORE: {score}
MATCHING_SKILLS_COUNT: {matching}
PARTIAL_MATCHES_COUNT: {partial}
NO_EVIDENCE_COUNT: {missing}

{body}""".strip()