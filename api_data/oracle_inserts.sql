[
  {
    "table": "limit_requests",
    "customer_sql": "\nINSERT INTO customers (id, customer_id, name, email, phone, status, created_at) \nVALUES (\n    'f851808f-ece0-4cca-aaa5-482df4ff082f',\n    'CUST001',\n    'mefgn ghorai',\n    'john.doe@hdfc.com',\n    '+91-9876543210',\n    'active',\n    TIMESTAMP '2025-09-19T05:26:57.361518'\n);",
    "request_sql": "\nINSERT INTO limit_requests (id, customer_id, request_type, current_limit, requested_limit, reason, income_proof, status, request_date, last_updated) \nVALUES (\n    '2e595679-c300-413c-90b0-98b9ab70dc55',\n    'CUST001',\n    'limit_increase',\n    50000,\n    1000000,\n    'Salary increase and improved credit score. Need higher limit for business expenses.',\n    'demo_salary_slip.pdf',\n    'pending',\n    TIMESTAMP '2025-09-19T05:26:57.361518',\n    TIMESTAMP '2025-09-19T05:26:57.361544'\n);",
    "timestamp": "2025-09-19T05:26:57.364713"
  }
]