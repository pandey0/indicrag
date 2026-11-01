"""LLM-drafted pilot questions over pilot_sheet passages. Written to data/gold/drafts/ (gitignored) as UNREVIEWED.

A human must validate each item (answer supported by quote, question natural, not leaking passage wording) before
review_status is set to agreed and the item moves to data/gold/. Hindi/English only: no Kannada drafting.
"""
import csv
import json

DRAFTS = {
    "en-pilot-002": ("What is the loan amount range under Stand-Up India for SC/ST and women entrepreneurs?", "factoid", "easy",
                     "Bank loans of between ₹10 lakh and ₹1 crore, for new enterprises outside the farm sector."),
    "en-pilot-005": ("How much food grain is a priority household with a ration card entitled to?", "factoid", "easy",
                     "5 kilograms of food grain per member per month."),
    "en-pilot-008": ("How is the monthly foodgrain entitlement of an Antyodaya household different from other TPDS households?", "comparison", "medium",
                     "Antyodaya (AAY) households get 35 kg per household per month, while other covered households get 5 kg per person per month."),
    "en-pilot-009": ("How quickly should a free ambulance arrive after calling the toll-free number under the National Health Mission?", "factoid", "easy",
                     "Within 30 minutes of the call."),
    "en-pilot-010": ("How long do elected Gram Panchayat members serve, and who appoints the Panchayat Secretary?", "factoid", "medium",
                     "Elected representatives serve five years; the Secretary is a non-elected official appointed by the state government."),
    "hi-pilot-001": ("उज्ज्वला योजना के लाभार्थियों को प्रति सिलेंडर कितनी सब्सिडी दी गई, और अक्टूबर 2023 में क्या बदला?", "factoid", "medium",
                     "मई 2022 में 200 रुपये प्रति सिलेंडर सब्सिडी दी गई; अक्टूबर 2023 में इसे बढ़ाकर 300 रुपये कर दिया गया।"),
    "hi-pilot-002": ("आयुष्मान भारत योजना में हर परिवार को प्रति वर्ष कितने रुपये तक का अस्पताल कवरेज मिलता है?", "factoid", "easy",
                     "प्रति परिवार प्रति वर्ष 5 लाख रुपये तक का कवरेज।"),
    "hi-pilot-005": ("मनरेगा में प्रति परिवार हर साल कितने दिन का रोजगार मिलना चाहिए?", "factoid", "easy",
                     "हर वित्तीय वर्ष में प्रति परिवार 100 दिनों का रोजगार (या बेरोजगारी भत्ता) सक्षम और इच्छुक श्रमिकों को।"),
    "hi-pilot-006": ("क्या राशन कार्ड को पहचान या पते के प्रमाण के रूप में इस्तेमाल किया जा सकता है?", "factoid", "easy",
                     "हाँ, राशन कार्ड पहचान और पते के प्रमाण के रूप में काम करता है, और अधिवास प्रमाण पत्र, मतदाता पहचान पत्र आदि के आवेदन में उपयोग किया जा सकता है।"),
    "hi-pilot-008": ("प्रधानमंत्री जीवन ज्योति बीमा योजना किस आयु वर्ग के लोगों के लिए उपलब्ध है?", "eligibility", "easy",
                     "18 से 50 वर्ष के आयु वर्ग के लोगों के लिए।"),
    "hi-pilot-010": ("पैन कार्ड के लिए आवेदन कब तक कर देना चाहिए?", "procedure", "medium",
                     "संबंधित निर्धारण वर्ष के 30 जून से पहले।"),
}
rows = {r["id"]: r for r in csv.DictReader(open("data/labelling/pilot_sheet.csv", encoding="utf-8"))}
with open("data/gold/drafts/pilot_drafts.jsonl", "w", encoding="utf-8") as f:
    for iid, (q, qtype, diff, ans) in DRAFTS.items():
        r = rows[iid]
        f.write(json.dumps({
            "id": iid.replace("pilot", "draft"), "lang": r["lang"], "register": "formal", "question": q, "qtype": qtype, "difficulty": diff,
            "answer": ans, "answerable": True, "valid_as_of": "2026-11-01", "writer": "claude-draft", "review_status": "unreviewed",
            "dataset_version": "0.0-draft", "source_kind": "llm_drafted_validated",
            "notes": "DRAFT: LLM-written, not human validated; source is Wikipedia fallback corpus (CC BY-SA 4.0)",
            "evidence": [{"doc_id": r["doc_id"], "doc_sha256": r["doc_sha256"], "parsed_sha256": r["parsed_sha256"], "parser_version": r["parser_version"],
                          "char_start": int(r["char_start"]), "char_end": int(r["char_end"]), "quote": r["quote"]}]}, ensure_ascii=False) + "\n")
print(len(DRAFTS), "drafts written")
