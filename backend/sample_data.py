"""
Sample data for Veritus Legal Intelligence Platform
This provides sample judgments and citations when no local data is available
"""

SAMPLE_JUDGMENTS = [
    {
        "id": 1,
        "case_title": "Kesavananda Bharati vs State of Kerala",
        "case_number": "Writ Petition (Civil) No. 135 of 1970",
        "petitioner": "Kesavananda Bharati",
        "respondent": "State of Kerala",
        "judgment_date": "1973-04-24",
        "summary": "Landmark case that established the basic structure doctrine of the Indian Constitution. The Supreme Court held that Parliament cannot alter the basic structure of the Constitution.",
        "court": "Supreme Court of India",
        "judges": ["Justice S.M. Sikri", "Justice J.M. Shelat", "Justice A.N. Grover", "Justice K.S. Hegde", "Justice A.K. Mukherjea"],
        "is_processed": True,
        "filename": "kesavananda_bharati_1973.pdf",
        "extraction_status": "completed",
        "file_size": 2456789,
        "upload_date": "2024-01-15T10:30:00",
        "full_text": "This landmark judgment established the basic structure doctrine, holding that certain features of the Constitution are so fundamental that they cannot be altered by Parliament through constitutional amendments. The Court identified features like supremacy of the Constitution, rule of law, independence of judiciary, and federalism as part of the basic structure."
    },
    {
        "id": 2,
        "case_title": "Maneka Gandhi vs Union of India",
        "case_number": "AIR 1978 SC 597",
        "petitioner": "Maneka Gandhi",
        "respondent": "Union of India",
        "judgment_date": "1978-01-25",
        "summary": "Revolutionary judgment that expanded the scope of Article 21 (Right to Life and Personal Liberty) and established the principle of procedural due process.",
        "court": "Supreme Court of India",
        "judges": ["Justice P.N. Bhagwati", "Justice N.L. Untwalia", "Justice V.R. Krishna Iyer"],
        "is_processed": True,
        "filename": "maneka_gandhi_1978.pdf",
        "extraction_status": "completed",
        "file_size": 1234567,
        "upload_date": "2024-01-16T14:20:00",
        "full_text": "The Court held that Article 21 is not merely a protection against executive action but also against legislative action. The procedure established by law must be right, just and fair, not arbitrary, fanciful or oppressive. This judgment revolutionized the interpretation of fundamental rights."
    },
    {
        "id": 3,
        "case_title": "Vishaka vs State of Rajasthan",
        "case_number": "AIR 1997 SC 3011",
        "petitioner": "Vishaka and Others",
        "respondent": "State of Rajasthan and Others",
        "judgment_date": "1997-08-13",
        "summary": "Landmark judgment on sexual harassment at workplace. The Court laid down guidelines for prevention and redressal of sexual harassment complaints.",
        "court": "Supreme Court of India",
        "judges": ["Justice J.S. Verma", "Justice Sujata V. Manohar", "Justice B.N. Kirpal"],
        "is_processed": True,
        "filename": "vishaka_1997.pdf",
        "extraction_status": "completed",
        "file_size": 987654,
        "upload_date": "2024-01-17T09:15:00",
        "full_text": "In the absence of legislation on sexual harassment at workplace, the Court laid down detailed guidelines based on international conventions. These guidelines became known as the Vishaka Guidelines and were later codified in the Sexual Harassment of Women at Workplace Act, 2013."
    },
    {
        "id": 4,
        "case_title": "K.S. Puttaswamy vs Union of India",
        "case_number": "Writ Petition (Civil) No. 494 of 2012",
        "petitioner": "K.S. Puttaswamy (Retd.) and Others",
        "respondent": "Union of India and Others",
        "judgment_date": "2017-08-24",
        "summary": "Nine-judge bench unanimously declared privacy as a fundamental right under Articles 14, 19, and 21 of the Constitution.",
        "court": "Supreme Court of India",
        "judges": ["Justice J.S. Khehar", "Justice J. Chelameswar", "Justice S.A. Bobde", "Justice R.K. Agrawal", "Justice R.F. Nariman", "Justice A.M. Sapre", "Justice D.Y. Chandrachud", "Justice S.K. Kaul", "Justice S. Abdul Nazeer"],
        "is_processed": True,
        "filename": "puttaswamy_privacy_2017.pdf",
        "extraction_status": "completed",
        "file_size": 3456789,
        "upload_date": "2024-01-18T16:45:00",
        "full_text": "Privacy is a fundamental right inherent to life and liberty and forms a part of the rights guaranteed by Part III of the Constitution. The right to privacy is protected as an intrinsic part of the right to life and personal liberty under Article 21 and as a part of the freedoms guaranteed by Part III of the Constitution."
    },
    {
        "id": 5,
        "case_title": "Navtej Singh Johar vs Union of India",
        "case_number": "Writ Petition (Criminal) No. 76 of 2016",
        "petitioner": "Navtej Singh Johar and Others",
        "respondent": "Union of India",
        "judgment_date": "2018-09-06",
        "summary": "Historic judgment that decriminalized consensual homosexual acts by reading down Section 377 of the Indian Penal Code.",
        "court": "Supreme Court of India",
        "judges": ["Justice Dipak Misra", "Justice R.F. Nariman", "Justice A.M. Khanwilkar", "Justice D.Y. Chandrachud", "Justice Indu Malhotra"],
        "is_processed": True,
        "filename": "navtej_johar_377_2018.pdf",
        "extraction_status": "completed",
        "file_size": 2789456,
        "upload_date": "2024-01-19T11:30:00",
        "full_text": "Section 377 IPC, insofar as it criminalizes consensual sexual conduct between adults of the same sex, is unconstitutional. The LGBT community possesses the same human, fundamental, and constitutional rights as other citizens. Sexual orientation is a natural phenomenon determined by nature."
    }
]

SAMPLE_CITATIONS = [
    {
        "source_case": "K.S. Puttaswamy vs Union of India",
        "target_case": "Maneka Gandhi vs Union of India",
        "citation_type": "followed",
        "context": "The Court relied on Maneka Gandhi's interpretation of Article 21 to establish privacy as a fundamental right.",
        "strength": "strong"
    },
    {
        "source_case": "Navtej Singh Johar vs Union of India", 
        "target_case": "K.S. Puttaswamy vs Union of India",
        "citation_type": "applied",
        "context": "The privacy judgment was applied to protect sexual autonomy and dignity of LGBT individuals.",
        "strength": "strong"
    },
    {
        "source_case": "Vishaka vs State of Rajasthan",
        "target_case": "Maneka Gandhi vs Union of India", 
        "citation_type": "relied_upon",
        "context": "Article 21 interpretation was used to derive right to work in dignity without harassment.",
        "strength": "medium"
    }
]

def get_sample_judgments():
    """Return sample judgments data"""
    return SAMPLE_JUDGMENTS

def get_sample_citations():
    """Return sample citations data"""
    return SAMPLE_CITATIONS

def get_judgment_by_id(judgment_id: int):
    """Get a specific judgment by ID"""
    for judgment in SAMPLE_JUDGMENTS:
        if judgment["id"] == judgment_id:
            return judgment
    return None
