import os
import glob

replacements = {
    '"usage_logs"': '"ai_usage_logs"',
    "'usage_logs'": "'ai_usage_logs'",
    '"rate_limits"': '"ai_rate_limits"',
    "'rate_limits'": "'ai_rate_limits'",
    '"alerts_sent"': '"ai_alerts_sent"',
    "'alerts_sent'": "'ai_alerts_sent'",
    '"api_keys"': '"ai_api_keys"',
    "'api_keys'": "'ai_api_keys'",
    '"users"': '"ai_users"',
    "'users'": "'ai_users'",
    '"providers"': '"ai_providers"',
    "'providers'": "'ai_providers'",
    '"job_runs"': '"ai_job_runs"',
    "'job_runs'": "'ai_job_runs'",
    '"reconciliation_results"': '"ai_reconciliation_results"',
    "'reconciliation_results'": "'ai_reconciliation_results'",
    '"provider_reported_usage"': '"ai_provider_reported_usage"',
    "'provider_reported_usage'": "'ai_provider_reported_usage'",
    '"providers.id"': '"ai_providers.id"',
    "'providers.id'": "'ai_providers.id'",
    '"users.id"': '"ai_users.id"',
    "'users.id'": "'ai_users.id'"
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

files = glob.glob('app/models/*.py') + glob.glob('alembic/versions/*.py')
for f in files:
    process_file(f)
