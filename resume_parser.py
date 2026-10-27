
# PDF file ko memory se read karne ke liye BytesIO import kar rahe hain
from io import BytesIO

# PDF se text extract karne ke liye PdfReader import kar rahe hain
from pypdf import PdfReader


# Ye function uploaded PDF resume ka text nikalta hai
def extract_resume_text(pdf_bytes: bytes) -> str:

    # PDF ke bytes se PDF reader object banate hain
    reader = PdfReader(BytesIO(pdf_bytes))

    # Har page ka text extract karke list mein rakhte hain
    pages = [
        page.extract_text() or ""
        for page in reader.pages
    ]

    # Saare pages ke text ko ek string mein combine karte hain
    resume_text = "\n\n".join(pages).strip()

    # Agar PDF se text nahi mila, toh error show karte hain
    if not resume_text:
        raise ValueError(
            "PDF se text nahi mila. Please text-based PDF resume upload karein."
        )

    # Extract kiya hua resume text return karte hain
    return resume_text
