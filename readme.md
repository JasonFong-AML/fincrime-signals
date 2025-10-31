# 🌍 FinCrime Signals

**FinCrime Signals** is a synthetic data and workflow simulator inspired by real-world financial-crime controls. It models **cross-border money movement**, **KYC/EDD pipelines**, and **jurisdictional risk logic** across 160 supported countries and territories.

## 🧠 Overview

This project builds a realistic AML/KYC simulation environment using Python and synthetic data to reproduce Wise-like compliance behaviors:

The focus of this project will be on the AML investigator workflow hence the customer onboarding and kyc risk scoring will be assumed as fields in 


- Customer onboarding and KYC risk scoring  
- Enhanced Due Diligence (EDD) for high-risk profile
- Transaction monitoring and sanctions screening  
- Country and currency-based regulatory logic  
- Data pipelines that generate realistic customer & transaction CSVs

## Compliance Workflow

| 🧠 KYC | 🔍 EDD | 🔄 ODD | 💣 AML | 🧩 Fraud & Risk Investigation |
|:--|:--|:--|:--|:--|
| **Purpose:** Verify customer identity and assess baseline risk before onboarding. | **Purpose:** Investigate high-risk customers in detail before approval. | **Purpose:** Monitor customer behavior and ensure risk profile stays accurate. | **Purpose:** Detect, investigate, and report suspicious transactions (fraud, money laundering, terrorist financing). | **Purpose:** Integrated with AML — focused on chargebacks, account takeovers (ATO), phishing, and scam trends. |
| **Workflow:** <br>• Customer Onboarding <br>• Identity Verification <br>• Screening <br>• Customer Risk Scoring <br>• Decision | **Workflow:** <br>• Trigger <br>• Information Gathering <br>• Advanced Screening <br>• Risk Re-Assessment <br>• Outcome | **Workflow:** <br>• Continuous Monitoring <br>• Trigger Reviews <br>• Periodic KYC Refresh <br>• Feedback Loop | **Workflow:** <br>• Transaction Monitoring <br>• Alert Generation <br>• Alert Review <br>• Case Management <br>• SAR/STR Filing <br>• Post-Investigation Feedback | **Workflow:** <br>• Incident Detection <br>• Case Review <br>• Fraud Typology Analysis <br>• Risk Scoring <br>• Product Feedback |


``` mermaid
flowchart LR

    A[🧾 Customer Onboarding] --> B[🪪 Identity Verification]
    B --> C[🧮 Risk Scoring]
    C --> D[🚨 Screening & Sanctions]
    D --> E[📊 Customer Risk Rating]
    E --> F[🔁 Ongoing Due Diligence]

    classDef lowRisk fill:#a3f7b5,stroke:#333,stroke-width:1px;
    classDef highRisk fill:#f7a3a3,stroke:#333,stroke-width:1px;
    E:::lowRisk
    F:::highRisk

    %% title: Know Your Customer (KYC) Pipeline

```
## 💣 Know Your Customer

Customer Onboarding
Identity Verification
Screening
Customer Risk Scoring
Decision


## 🔍 Enhanced Due Diligence




## 🔄 Ongoing Due Diligence

## 🧩 Fraud & Risk Investigation






