import os
import glob

replacements = {
    '"ix_users_': '"ix_ai_users_',
    "'ix_users_": "'ix_ai_users_",
    '"ix_api_keys_': '"ix_ai_api_keys_',
    "'ix_api_keys_": "'ix_ai_api_keys_",
    '"ix_usage_logs_': '"ix_ai_usage_logs_',
    "'ix_usage_logs_": "'ix_ai_usage_logs_",
    '"ix_providers_': '"ix_ai_providers_',
    "'ix_providers_": "'ix_ai_providers_",
    '"ix_alerts_sent_': '"ix_ai_alerts_sent_',
    "'ix_alerts_sent_": "'ix_ai_alerts_sent_",
    '"ix_reconciliation_results_': '"ix_ai_reconciliation_results_',
    "'ix_reconciliation_results_": "'ix_ai_reconciliation_results_",
    '"ix_job_runs_': '"ix_ai_job_runs_',
    "'ix_job_runs_": "'ix_ai_job_runs_",
    '"ix_rate_limits_': '"ix_ai_rate_limits_',
    "'ix_rate_limits_": "'ix_ai_rate_limits_"
}

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

files = glob.glob('alembic/versions/*.py')
for f in files:
    process_file(f)
