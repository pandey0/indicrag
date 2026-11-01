"""Batch 7 LLM drafts (UNREVIEWED) from the remaining unused Wikipedia passages (data/labelling/pilot_sheet_b7.csv)."""
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

HI = {
    "hi-pilot-002": ("आरटीआई के तहत सूचना मांगने के लिए केंद्र सरकार ने आवेदन फीस कितनी तय की है और किसे फीस में छूट मिलती है?", "factoid", "easy",
                     "केंद्र सरकार ने 10 रुपये की फीस तय की है; बीपीएल कार्डधारकों को आवेदन शुल्क में छूट प्राप्त है (कुछ राज्यों में फीस अधिक है)।"),
    "hi-pilot-003": ("राष्ट्रीय पेंशन प्रणाली (एनपीएस) कब शुरू की गई थी और पीएफआरडीए की स्थापना कब हुई?", "factoid", "medium",
                     "एनपीएस 1 जनवरी 2004 को शुरू की गई; पीएफआरडीए की स्थापना 10 अक्तूबर 2003 को हुई।"),
}
write_drafts(HI, "data/labelling/pilot_sheet_b7.csv", "data/gold/drafts/batch7_hi.jsonl", "b7")

EN = {
    "en-pilot-003": ("How many Pension Fund Managers are there in the NPS, and which one is the largest?", "factoid", "easy",
                     "There are 13 Pension Fund Managers; SBI Pension Funds is the largest."),
    "en-pilot-004": ("What extra endorsement does a driver need to carry hazardous goods in India?", "factoid", "easy",
                     "A Hazardous Goods endorsement, in addition to a transport-class or LMV-class licence."),
    "en-pilot-009": ("What nutritional support do pregnant women and lactating mothers get under the National Food Security Act?", "factoid", "medium",
                     "They are entitled to meals as per prescribed nutritional norms under ICDS and Mid-Day Meal schemes (children aged 6 months to 14 years are covered too)."),
    "en-pilot-010": ("What fee must a citizen pay with an RTI application and who is exempt?", "factoid", "medium",
                     "The fee is paid by postal order, demand draft, bankers cheque or court stamp payable to the public authority's Accounts Officer; a person from a disadvantaged community need not pay."),
    "en-pilot-006": ("What three components does the National Social Assistance Programme (NSAP) include?", "factoid", "easy",
                     "The National Old Age Pension Scheme (NOAPS), the National Family Benefit Scheme (NFBS) and the National Maternity Benefit Scheme (NMBS)."),
    "en-pilot-001": ("When was the NOTA option introduced on voting machines in India, and when was its symbol introduced?", "factoid", "medium",
                     "NOTA was introduced in 2014; its specific symbol (ballot paper with a black cross) was introduced on 18 September 2015."),
}
write_drafts(EN, "data/labelling/pilot_sheet_b7.csv", "data/gold/drafts/batch7_en.jsonl", "b7")
