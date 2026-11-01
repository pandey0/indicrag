"""Batch 3 LLM drafts over myScheme passages (data/labelling/pilot_sheet_ms.csv). UNREVIEWED; English only."""
import sys

sys.path.insert(0, "scripts")
from _draft_lib import write_drafts  # noqa: E402

D = {
    "en-pilot-001": ("What documents do I need to apply for the Integrated Horticulture Development Program for Tribal Area Farmers?", "doc_list", "medium",
                     "An Aadhaar card for identity proof, a 7/12 certificate for land ownership, and a bank passbook or cancelled cheque for direct benefit transfer."),
    "en-pilot-003": ("Is there a limit on how many girl children can receive the third and later instalments?", "factoid", "medium",
                     "No, there is no limit; all girls who already received the first two instalments continue to be entitled."),
    "en-pilot-004": ("What documents must fishermen have to claim the diesel subsidy?", "doc_list", "easy",
                     "A valid diesel card, a boat registration certificate and identification proof such as an Aadhaar card or Fishermen ID; the authority may ask for more."),
    "en-pilot-007": ("How much is the Veerjyoti Puraskar award and how many people receive it each year?", "factoid", "medium",
                     "A cash prize of ₹20,000 and a scroll/citation, given to two selected persons annually."),
    "en-pilot-008": ("How much subsidy is given for buying a commercial vehicle under the West Bengal Gatidhara scheme?", "factoid", "medium",
                     "30% of the ex-showroom price, subject to a maximum of ₹1,00,000."),
    "en-pilot-009": ("How much is the research fellowship per year and how many days of research are required?", "factoid", "medium",
                     "₹60,000 per year, provided at least 90 days of research work are completed each year in the host institution."),
    "en-pilot-010": ("How much financial assistance does the Aapki Beti Yojana give to a BPL orphan girl in Class 9 to 12?", "factoid", "medium",
                     "₹2,500 per year for girls in Class 9 to 12 (₹2,100 per year for Class 1 to 8)."),
    "en-pilot-013": ("Who can get monthly assistance under the Financial Assistance to Helpless Artists scheme in Gujarat?", "eligibility", "medium",
                     "Artists and their dependents who are physically disabled, above 60 years of age, have a monthly income below ₹600 and cannot sustain themselves due to age or disability."),
    "en-pilot-015": ("By when must the capital subsidy application be submitted online?", "procedure", "easy",
                     "Within one year from the date of commencement of operation."),
    "en-pilot-016": ("Is there an income limit to get ICT training benefits under this scheme?", "eligibility", "easy",
                     "No, there is no income limit prescribed for availing the ICT training benefits."),
    "en-pilot-021": ("How much monthly stipend do backward class students get for professional and ITI courses?", "factoid", "easy",
                     "₹400 per month for one year for socially and economically backward class students in recognised professional and Government ITI courses."),
    "en-pilot-022": ("What prize is given for a cow or buffalo that gives a lot of milk, and how much milk qualifies?", "factoid", "medium",
                     "A cash prize of ₹1,000 per animal giving 15 litres or more milk per day, paid to the owner's bank account."),
}
write_drafts(D, "data/labelling/pilot_sheet_ms.csv", "data/gold/drafts/batch3_drafts.jsonl", "b3")
