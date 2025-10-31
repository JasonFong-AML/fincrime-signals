# data_generator.py
import csv
import random
from faker import Faker

fake = Faker()
Faker.seed(42)

with open('customers.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'name', 'country', 'risk_level'])
    for i in range(1, 101):
        writer.writerow([
            i,
            fake.name(),
            fake.country(),
            random.choice(['Low', 'Medium', 'High'])
        ])

with open('transactions.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['transaction_id', 'customer_id', 'amount', 'timestamp', 'is_fraud'])
    for i in range(1, 1001):
        writer.writerow([
            i,
            random.randint(1, 100),
            round(random.uniform(10, 10000), 2),
            fake.date_time_this_year(),
            random.choice([0, 1]) if random.random() < 0.05 else 0
        ])

print("✅ Synthetic data generated: customers.csv & transactions.csv")
