# ============================================
# generate_customers.csv
# --------------------------------------------
# Generates 1,000 synthetic customers aligned to AML/KYC risk methodology.
# Fields: customer_id, name, dob, nationality, residency_country,
# jurisdiction_risk, account_type, occupation, source_of_funds, pep_flag,
# screening_result, device_count, join_date, kyc_status, risk_score,
# onboarding_decision
# ============================================

import pandas as pd
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

# --- Jurisdiction risk tiers (160 countries from your verified list) ---
jurisdiction_map = {
    "Low": [
        "Andorra","Austria","Belgium","Bosnia and Herzegovina","Bulgaria","Czech Republic",
        "Denmark","Estonia","Finland","France","Greece","Iceland","Ireland","Kosovo","Latvia",
        "Liechtenstein","Lithuania","Luxembourg","Monaco","Montenegro","North Macedonia",
        "Norway","Poland","Portugal","San Marino","Slovakia","Slovenia","Spain","Sweden",
        "Switzerland","Vatican City","United Kingdom","Gibraltar","Guernsey","Jersey","Isle of Man",
        "Canada","Chile","Uruguay","Armenia","Brunei","Israel","South Korea","Taiwan","Australia",
        "Norfolk Island","New Zealand","Cook Islands","Niue","New Caledonia","French Polynesia",
        "Bermuda","Cayman Islands","British Virgin Islands","Puerto Rico","Guam","American Samoa",
        "Northern Mariana Islands"
    ],
    "Medium": [
        "Croatia","Cyprus","Germany","Hungary","Italy","Malta","Moldova","Romania","Serbia",
        "Ukraine","Netherlands","Aruba","Curaçao","Sint Maarten","United States","Mexico","Argentina",
        "Brazil","Colombia","Peru","Paraguay","Ecuador","Bolivia","Panama","Costa Rica","Guatemala",
        "Honduras","Dominican Republic","Jamaica","Bahamas","Barbados","Guyana","Botswana","Egypt",
        "Ethiopia","Ghana","Lesotho","Malawi","Mauritius","Morocco","Namibia","Rwanda","Senegal",
        "Seychelles","South Africa","Tunisia","Uganda","Zambia","Zimbabwe","Azerbaijan","Bahrain",
        "Bangladesh","Georgia","India","Indonesia","Japan","Jordan","Kazakhstan","Kyrgyzstan",
        "Lebanon","Malaysia","Maldives","Mongolia","Oman","Pakistan","Philippines","Qatar",
        "Saudi Arabia","Singapore","Sri Lanka","Turkey","United Arab Emirates","Uzbekistan",
        "Hong Kong SAR","Macau SAR","Fiji","Samoa","Tonga","Vanuatu","Papua New Guinea","Palau",
        "Micronesia","Marshall Islands","Timor-Leste"
    ],
    "High": [
        "Algeria","Cameroon","Côte d’Ivoire","Kenya","Madagascar","Mozambique","Nigeria","Tanzania",
        "Cambodia","China","Kuwait","Laos","Nepal","Tajikistan","Vietnam","Solomon Islands"
    ]
}

# --- Helper lists ---
occupations = {
    "Low": ["Teacher","Engineer","Doctor","Civil Servant","Nurse","Software Developer"],
    "Medium": ["Real Estate Agent","Importer/Exporter","Consultant","Crypto Trader","Freelancer"],
    "High": ["Used Car Dealer","Pawn Broker","Nightclub Owner","Cash Courier"]
}
sources = ["Salary","Business Revenue","Savings","Inheritance","Crypto","Cash"]
account_types = ["Personal","Business"]

def random_date(start_year=1955, end_year=2005):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def random_join_date():
    start = date.today() - timedelta(days=3*365)
    end = date.today()
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

# --- Generate dataset ---
customers = []
for _ in range(1000):
    # Select jurisdiction based on weighted region risk
    risk_level = random.choices(["Low","Medium","High"], weights=[0.6,0.3,0.1])[0]
    country = random.choice(jurisdiction_map[risk_level])

    # Assign KYC profile fields
    name = fake.name()
    dob = random_date()
    nationality = random.choice(country.split())
    residency_country = country
    account_type = random.choices(account_types, weights=[0.85,0.15])[0]

    # Occupation and SoF
    occ_risk = random.choices(["Low","Medium","High"], weights=[0.5,0.3,0.2])[0]
    occupation = random.choice(occupations[occ_risk])
    source_of_funds = random.choices(sources, weights=[0.6,0.2,0.1,0.05,0.03,0.02])[0]

    # Flags
    pep_flag = random.random() < 0.02
    screening_result = (
        "Confirmed Hit" if pep_flag else
        random.choices(["Clear","Potential Match"], weights=[0.95,0.05])[0]
    )
    device_count = random.choices([1,2,3,4,5], weights=[0.5,0.25,0.15,0.07,0.03])[0]
    join_date = random_join_date()
    kyc_status = random.choices(["Verified","Pending","Rejected"], weights=[0.9,0.05,0.05])[0]

    # Risk score logic
    score = {"Low":0,"Medium":1,"High":2}[risk_level]
    score += {"Personal":0,"Business":2}[account_type]
    score += {"Low":0,"Medium":1,"High":2}[occ_risk]
    score += 2 if source_of_funds in ["Crypto","Cash"] else 1 if source_of_funds in ["Business Revenue","Inheritance"] else 0
    score += 2 if pep_flag else 0
    score += 0 if device_count==1 else 1 if device_count==2 else 2

    risk_score = (
        "Low" if score <= 2 else
        "Medium" if score <= 5 else
        "High"
    )

    onboarding_decision = (
        "Rejected" if kyc_status == "Rejected" else
        "Manual Review" if risk_score == "High" or screening_result != "Clear" else
        "Approved"
    )

    customers.append({
        "customer_id": fake.uuid4(),
        "name": name,
        "dob": dob,
        "nationality": nationality,
        "residency_country": residency_country,
        "jurisdiction_risk": risk_level,
        "account_type": account_type,
        "occupation": occupation,
        "source_of_funds": source_of_funds,
        "pep_flag": pep_flag,
        "screening_result": screening_result,
        "device_count": device_count,
        "join_date": join_date,
        "kyc_status": kyc_status,
        "risk_score": risk_score,
        "onboarding_decision": onboarding_decision
    })

df = pd.DataFrame(customers)
# --- Keep only approved or manual review customers ---
df = df[df["onboarding_decision"].isin(["Approved", "Manual Review"])]

# --- Save clean customer base ---
df.to_csv("data/customers.csv", index=False)
print(f"✅ Saved {len(df)} onboarded customers -> data/customers.csv")
print(df["onboarding_decision"].value_counts())
