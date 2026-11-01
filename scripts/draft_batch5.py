"""Batch 5 LLM drafts (UNREVIEWED): every question names its scheme; includes unanswerable items verified absent from the corpus."""
import json
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

EN = {
    "en-pilot-002": ("Under the 'Award of Cash Incentive to the Toppers at Regional Level' scheme in Puducherry, how long must a student have lived in Puducherry if not born there?", "eligibility", "medium",
                     "A minimum of five years of continuous residence (or residency by birth)."),
    "en-pilot-003": ("What is the maximum family income to be eligible for the Saraswati Sadhana Yojana for economically backward class girls?", "eligibility", "easy",
                     "₹6,00,000 per annum; families with income equal to or below this are eligible."),
    "en-pilot-010": ("Where do I first go to get the application form for the Residential School for Blinds scheme?", "procedure", "easy",
                     "The guardian or social worker visits the District Social Welfare Office and requests a hard copy of the application form."),
    "en-pilot-011": ("What documents are needed to claim the first instalment under the Coffee Development Programme in the North Eastern Region (Expansion of Coffee)?", "doc_list", "medium",
                     "The duly filled application and self-declaration, proof of photo identity, proof of land ownership, and bank account details."),
    "en-pilot-013": ("How is the marketing incentive calculated under the Handloom Marketing Assistance scheme?", "factoid", "medium",
                     "At 10% of your average sales of handloom products over the last 3 years."),
    "en-pilot-017": ("What is the maximum assistance per student under the Scholarship for Self Finance Colleges Students of NT/DNT?", "factoid", "easy",
                     "Up to ₹50,000 per eligible student for education-related expenses."),
    "en-pilot-018": ("To whom do I submit the application form for the Indira Gandhi National Old Age Pension Scheme (Punjab)?", "procedure", "easy",
                     "To the District Social Security Officer, with the duly filled and signed form and documents."),
    "en-pilot-019": ("Through whom is the application submitted under the Meghalaya Tribal Students' Book Grant (Post-Matric)?", "procedure", "medium",
                     "To the Director of Public Instruction, Meghalaya, through the Head of the Institution where the candidate studies."),
    "en-pilot-021": ("How can farmers apply for the National Mission on Edible Oil-Oil Palm planting materials scheme?", "procedure", "easy",
                     "By visiting the iKhedut portal, filling the application form online, uploading the required documents and submitting it for departmental verification."),
    "en-pilot-022": ("Who is eligible for the Mukhyamantri Medhavi Chhatra Puraskar Yojana?", "eligibility", "medium",
                     "The top three students in each faculty (Arts, Science, Commerce) with the highest university-level marks in graduation and post-graduation courses."),
    "en-pilot-023": ("How much reward do students in classes IX to X get under the Scheme for Grant of Rewards to the Children of Salt Labourers, and what share is reserved for girls?", "factoid", "hard",
                     "₹1500 for classes IX to X; at least 50% of the allocation per state is reserved for girl children."),
    "en-pilot-024": ("What must an applicant submit for the Retired Sportsperson Pension Scheme?", "doc_list", "easy",
                     "An affidavit and a domicile certificate proving Gujarat residency."),
    "en-pilot-026": ("What is the usual maximum financial assistance for a project under the Financial Assistance for Tagore Cultural Complexes scheme?", "factoid", "medium",
                     "Normally up to ₹15 crores; in extremely rare cases of outstanding merit it can go up to ₹50 crores."),
    "en-pilot-028": ("How is an application processed under the Incentive Scheme for Marrying a Disabled Young Man/Woman?", "procedure", "medium",
                     "The Assistant Social Welfare Officer verifies it and forwards it with recommendations to the District Social Welfare Officer; the District Committee reviews it and, on approval, the incentive is paid."),
}
HI = {
    "hi-pilot-005": ("डिजीलॉकर में खाता कैसे खोला जाता है?", "procedure", "medium",
                     "डिजिलॉकर की वेबसाइट पर 'अभी रजिस्टर करें' दबाकर आधार कार्ड नंबर डालें, फिर ओटीपी या अंगुली के निशान से लॉगिन करें और मांगी गई सूचना भरें; इसके बाद खाता बन जाता है।"),
    "hi-pilot-016": ("मिड डे मील योजना में प्राथमिक और उच्च प्राथमिक कक्षाओं के प्रति बच्चे प्रति स्कूल दिवस कितना खाद्यान्न निःशुल्क दिया जाता है?", "factoid", "medium",
                     "प्राथमिक कक्षाओं के लिए 100 ग्राम और उच्च प्राथमिक कक्षाओं के लिए 150 ग्राम प्रति बच्चा प्रति स्कूल दिवस।"),
    "hi-pilot-021": ("आयुष्मान भारत (प्रधानमंत्री जन आरोग्य योजना) पूरे भारत में कब लागू की गई?", "factoid", "easy",
                     "23 सितम्बर 2018 को।"),
    "hi-pilot-023": ("प्रधानमंत्री गरीब कल्याण अन्न योजना में हर महीने कितना मुफ्त राशन मिलता है और इसे कितने वर्षों के लिए बढ़ाया गया?", "factoid", "medium",
                     "प्रति माह पांच किलोग्राम मुफ्त खाद्य सामग्री; योजना को अगले पांच वर्षों के लिए बढ़ाया गया है।"),
    "hi-pilot-028": ("30 मार्च 2023 तक देश में कितने किसान क्रेडिट कार्ड खाते थे और कितना ऋण स्वीकृत था?", "factoid", "medium",
                     "7.35 करोड़ किसान क्रेडिट कार्ड खाते थे और 8.85 लाख करोड़ रुपये का ऋण स्वीकृत था।"),
}
write_drafts(EN, "data/labelling/pilot_sheet_ms2.csv", "data/gold/drafts/batch5_en.jsonl", "b5")
write_drafts(HI, "data/labelling/pilot_sheet_hi3.csv", "data/gold/drafts/batch5_hi.jsonl", "b5")

# Unanswerable: the asked fact must be absent from the corpus (checked with regexes in the drafting session; re-check on reviewing).
UNANS = [
    ("b5-un-001", "What is the toll-free helpline number of the Aapki Beti Yojana?", "no helpline/toll-free/phone text in ms_aby; scheme name appears in no other document"),
    ("b5-un-002", "What is the last date to apply for the Gatidhara Scheme?", "no last date/deadline text in ms_gs-west-bengal; scheme name appears in no other document"),
    ("b5-un-003", "What is the toll-free helpline number of the Laado Protsahan Yojana?", "no helpline/toll-free/last date text in ms_lpy; scheme name appears in no other document"),
    ("b5-un-004", "What is the application fee for the Financial Assistance to Helpless Artists scheme?", "no fee/last date text in ms_fatha; scheme name appears in no other document"),
]
with open("data/gold/drafts/batch5_unanswerable.jsonl", "w", encoding="utf-8") as f:
    for iid, q, why in UNANS:
        f.write(json.dumps({"id": iid, "lang": "en", "register": "formal", "question": q, "qtype": "unanswerable", "difficulty": "medium",
                            "answer": "The available documents do not say.", "answerable": False, "valid_as_of": "2026-11-01", "writer": "claude-draft",
                            "review_status": "unreviewed", "dataset_version": "0.0-draft", "source_kind": "llm_drafted_validated",
                            "notes": "DRAFT unanswerable; corpus check: " + why, "evidence": []}, ensure_ascii=False) + "\n")
print(len(UNANS), "unanswerable drafts")
