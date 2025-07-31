# privacy.py

import streamlit as st
import os
import json
from faker import Faker
from cryptography.fernet import Fernet

@st.cache_resource
def get_faker():
    return Faker()

@st.cache_resource
def get_cipher(keyfile="secret.key"):
    if not os.path.exists(keyfile):
        with open(keyfile, "wb") as kf:
            kf.write(Fernet.generate_key())
    with open(keyfile, "rb") as kf:
        key = kf.read()
    return Fernet(key)

fake = get_faker()
cipher = get_cipher()

def anonymize_candidate_data(data):
    anonymized = data.copy()
    anonymized['full_name'] = fake.name()
    anonymized['email'] = fake.email()
    anonymized['phone'] = fake.phone_number()
    return anonymized

def securely_store_candidate(candidate_data, filename="candidate.dat"):
    anonymized = anonymize_candidate_data(candidate_data)
    data_bytes = json.dumps(anonymized).encode()
    encrypted_data = cipher.encrypt(data_bytes)
    with open(filename, "wb") as f:
        f.write(encrypted_data)
