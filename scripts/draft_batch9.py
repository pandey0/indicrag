"""Batch 9 LLM drafts (UNREVIEWED), from unused Wikipedia passages (data/labelling/pilot_sheet_b9.csv)."""
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

HI = {
    "hi-pilot-002": ("भारत में आयकर के अंतर्गत वाहन भत्ते के रूप में प्रति माह कितनी राशि तक कर मुक्त है और क्या इसके लिए बिल चाहिए?", "factoid", "easy",
                     "800 रुपये प्रति माह (9,600 रुपये प्रति वर्ष) तक वाहन भत्ता कर मुक्त है और इस राशि के लिए किसी बिल की आवश्यकता नहीं होती।"),
    "hi-pilot-003": ("नई दिल्ली के अखिल भारतीय आयुर्विज्ञान संस्थान (एम्स) की आधारशिला कब रखी गई और इसका सृजन किस वर्ष संसद के अधिनियम से हुआ?", "factoid", "medium",
                     "आधारशिला 4 अप्रैल 1952 को रखी गई और इसका सृजन 1956 में संसद के एक अधिनियम के माध्यम से स्वायत्त संस्थान के रूप में हुआ।"),
    "hi-pilot-005": ("भारतीय नागरिकता के लिए पंजीकरण का आवेदन देने से पहले आवेदक को कम से कम कितने समय से भारत में रहना चाहिए, यदि वह या उसका कोई अभिभावक पहले स्वतंत्र भारत का नागरिक था?", "factoid", "medium",
                     "आवेदन देने से पहले एक साल से भारत में रह रहा होना चाहिए (पूर्ण आयु और क्षमता वाला व्यक्ति)।"),
}
write_drafts(HI, "data/labelling/pilot_sheet_b9.csv", "data/gold/drafts/batch9_hi.jsonl", "b9")

EN = {
    "en-pilot-002": ("When can a second loan be taken against a PPF account, and who cannot take loans?", "factoid", "medium",
                     "A second loan can be taken within the third and before the sixth year and only if the first is fully repaid; individuals eligible for withdrawals cannot take loans, and inactive or discontinued accounts are not eligible."),
    "en-pilot-003": ("When was Mission Indradhanush launched and what immunisation coverage does it target?", "factoid", "medium",
                     "It was launched on 25 December 2014 and seeks 90% full immunisation coverage, sustained to 2020, for children up to two years and pregnant women."),
    "en-pilot-008": ("What minimum monthly pension is provided to pensioners under EPS 1995 and from which date?", "factoid", "easy",
                     "A minimum pension of ₹1000 per month, from 01.09.2014."),
    "en-pilot-009": ("How are government employees' NPS contributions distributed under the default Standard scheme?", "factoid", "medium",
                     "Evenly across three public sector fund managers: SBI Pension Funds, LIC Pension Fund and UTI Pension Fund."),
    "en-pilot-010": ("How much does the Central Government expect to spend on food subsidy under PMGKAY from January 2024 to December 2028?", "factoid", "medium",
                     "Approximately Rs 11.80 lakh crore over five years."),
    "en-pilot-013": ("Who issues ration cards in India and what are they used for?", "factoid", "easy",
                     "State governments issue them to eligible households to buy subsidised food grain from the Public Distribution System under the NFSA; they also serve as a common form of identification."),
}
write_drafts(EN, "data/labelling/pilot_sheet_b9.csv", "data/gold/drafts/batch9_en.jsonl", "b9")
