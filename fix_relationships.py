import os

models_dir = "app/models"
for file in os.listdir(models_dir):
    if not file.endswith(".py"): continue
    path = os.path.join(models_dir, file)
    with open(path, "r") as f:
        content = f.read()
    
    content = content.replace('back_populates="ai_api_keys"', 'back_populates="api_keys"')
    content = content.replace('back_populates="ai_rate_limits"', 'back_populates="rate_limits"')
    content = content.replace('back_populates="ai_usage_logs"', 'back_populates="usage_logs"')
    content = content.replace('back_populates="ai_users"', 'back_populates="users"')
    content = content.replace('back_populates="ai_providers"', 'back_populates="providers"')
    
    with open(path, "w") as f:
        f.write(content)
