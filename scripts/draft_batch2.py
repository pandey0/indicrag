"""Batch 2 LLM drafts over data/labelling/pilot_sheet_twins.csv (articles that have a Kannada twin). UNREVIEWED."""
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

D = {
    "en-pilot-001": ("When was Ujjwala Scheme II launched, and how many extra connections was it meant to provide?", "factoid", "easy",
                     "It was launched on 10 August 2021 to provide fuel to 1 crore families left out of the first scheme."),
    "en-pilot-003": ("Who launched UPI 123PAY, when, and for which users?", "factoid", "medium",
                     "RBI governor Shaktikanta Das launched it on 8 March 2022 for almost 40 crore feature-phone users."),
    "en-pilot-004": ("What UPI tax payment ceiling did the RBI suggest on 8 August 2024?", "factoid", "medium",
                     "Raising it from ₹1 lakh to ₹5 lakh."),
    "en-pilot-005": ("Are black and white copies of an Aadhaar card valid?", "factoid", "easy",
                     "Yes, the government has stated that black and white copies are valid; PVC versions sold as smart cards have no official validity."),
    "en-pilot-008": ("Can a minor open a Jan Dhan account?", "eligibility", "easy",
                     "Yes, minors aged 10 and older can open an account, with a guardian to manage it."),
    "en-pilot-009": ("What was the Pradhan Mantri Matru Vandana Yojana called before 2017, and which ministry implements it?", "factoid", "medium",
                     "It was previously the Indira Gandhi Matritva Sahyog Yojana; it is implemented by the Ministry of Women and Child Development."),
    "en-pilot-016": ("When did the RTI Act come into force?", "factoid", "easy",
                     "On 12 October 2005 (the Bill was passed by Parliament on 15 June 2005)."),
    "hi-pilot-002": ("डिजीलॉकर क्या है और इसमें कौन-से दस्तावेज़ रखे जा सकते हैं?", "factoid", "medium",
                     "यह MeitY की डिजिटल भारत पहल के तहत एक ऑनलाइन सेवा है जो क्लाउड में खाता देती है, जिसमें ड्राइविंग लाइसेंस, वाहन पंजीकरण और शैक्षणिक मार्कशीट जैसे दस्तावेज़ रखे जा सकते हैं।"),
    "hi-pilot-004": ("RTI में सूचना देने से इनकार करने या ज़्यादा फीस माँगने पर शिकायत कहाँ की जा सकती है?", "procedure", "medium",
                     "केन्द्रीय या राज्य सूचना आयोग के पास शिकायत की जा सकती है।"),
    "hi-pilot-010": ("स्वच्छ भारत मिशन में घरेलू शौचालय की इकाई लागत कितनी है, और उसमें केंद्र व राज्य का हिस्सा कितना है?", "factoid", "medium",
                     "इकाई लागत ₹12,000 है; केंद्र सरकार की सहायता ₹9,000 और राज्य सरकार का योगदान ₹3,000 है।"),
    "hi-pilot-012": ("उज्ज्वला योजना के आवेदन पत्र में कौन-सी जानकारी भरनी होती है और उसे कहाँ जमा करना होता है?", "doc_list", "medium",
                     "नाम, पता, आधार नंबर और जन धन बैंक खाता नंबर भरकर वितरण केंद्र पर जमा करना होता है।"),
}
write_drafts(D, "data/labelling/pilot_sheet_twins.csv", "data/gold/drafts/batch2_drafts.jsonl", "b2")
