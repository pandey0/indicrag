"""Batch 6 LLM drafts (UNREVIEWED), Hindi from newly ingested Wikipedia articles (data/labelling/pilot_sheet_b6.csv)."""
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

HI = {
    "hi-pilot-007": ("पीपीएफ (सार्वजनिक भविष्य निधि) खाते में प्रतिवर्ष कम से कम और अधिकतम कितनी राशि जमा की जा सकती है?", "factoid", "medium",
                     "प्रतिवर्ष कम से कम 500 रुपये जमा करना अनिवार्य है और अधिकतम एक लाख पचास हजार रुपये प्रतिवर्ष (वित्तवर्ष) जमा किये जा सकते हैं।"),
    "hi-pilot-045": ("पीपीएफ खाते की अवधि कितनी होती है और उसे कैसे बढ़ाया जा सकता है?", "factoid", "medium",
                     "खाते की अवधि 15 वर्ष होती है; समाप्ति पर उसे पाँच-पाँच वर्ष के लिए कितनी भी बार बढ़ाया जा सकता है, और बढ़े हुए खाते में भी कर आदि के लाभ मिलते रहते हैं।"),
    "hi-pilot-048": ("भारत में मुख्य चुनाव आयुक्त की नियुक्ति कौन करता है और उनका कार्यकाल कितना होता है?", "factoid", "medium",
                     "नियुक्ति भारत का राष्ट्रपति करता है; मुख्य चुनाव आयुक्त का कार्यकाल 6 वर्ष या आयु 65 साल, जो पहले हो, का होता है।"),
    "hi-pilot-029": ("भारतीय चुनाव आयोग की स्थापना कब की गई थी?", "factoid", "easy",
                     "25 जनवरी 1950 को।"),
    "hi-pilot-003": ("भारतीय चुनाव आयोग में वर्तमान में कितने सदस्य होते हैं?", "factoid", "easy",
                     "एक मुख्य चुनाव आयुक्त और दो चुनाव आयुक्त।"),
    "hi-pilot-055": ("प्रधानमंत्री कौशल विकास योजना में पंजीकरण कितनी अवधि के लिए होता है और प्रमाणपत्र कहाँ मान्य है?", "factoid", "medium",
                     "तीन महीने, छह महीने और एक साल के लिए पंजीकरण होता है; कोर्स पूरा होने पर मिलने वाला प्रमाणपत्र पूरे देश में मान्य होता है।"),
    "hi-pilot-014": ("कर्मचारी राज्य बीमा निगम (ESIC) किस मंत्रालय के अधीन कार्य करता है?", "factoid", "easy",
                     "श्रम एवं रोजगार मंत्रालय के अधीन।"),
    "hi-pilot-015": ("सर्व शिक्षा अभियान में शिक्षकों को कक्षा कार्रवाई के लिए कितना शिक्षक अनुदान दिया जाता है?", "factoid", "easy",
                     "सभी एलपी/यूपी शिक्षकों को 500 रुपये का अनुदान दिया जाता है।"),
    "hi-pilot-043": ("नई शिक्षा नीति में मानव संसाधन मंत्रालय का नाम बदलकर क्या करने का फैसला लिया गया है?", "factoid", "easy",
                     "मानव संसाधन मंत्रालय का नाम पुनः \"शिक्षा मंत्रालय\" करने का फैसला लिया गया है।"),
}
write_drafts(HI, "data/labelling/pilot_sheet_b6.csv", "data/gold/drafts/batch6_hi.jsonl", "b6")

EN = {
    "en-pilot-048": ("What does a BPL family pay to join the Rashtriya Swasthya Bima Yojana, and how much inpatient cover does it get per year?", "factoid", "medium",
                     "A ₹30 registration fee for a biometric smart card; inpatient care up to ₹30,000 per family per year in empanelled hospitals."),
    "en-pilot-016": ("What are the employer and employee ESI contribution rates for employees earning ₹21,000 or less per month?", "factoid", "medium",
                     "The employer contributes 3.25% and the employee 0.75%, a total share of 4%."),
    "en-pilot-072": ("How is the Public Provident Fund (PPF) taxed?", "factoid", "medium",
                     "It is in the EEE (Exempt, Exempt, Exempt) category: contributions get tax benefit under Section 80C in the old tax regime, interest is exempt and maturity proceeds are exempt."),
    "en-pilot-036": ("What is the Reverse Charge Mechanism in GST?", "factoid", "medium",
                     "The receiver of goods or services pays the tax on behalf of unregistered, smaller suppliers; the receiver can claim Input Tax Credit while the unregistered dealer cannot."),
}
write_drafts(EN, "data/labelling/pilot_sheet_b6.csv", "data/gold/drafts/batch6_en.jsonl", "b6")
