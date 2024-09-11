from flask import Flask, redirect, url_for, render_template, session
from flask_oidc import OpenIDConnect
import requests
import json

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Initialize OIDC for Keycloak
oidc = OpenIDConnect(app)

# Home page (public)
@app.route('/')
def home():
    if oidc.user_loggedin:
        return f'Hello, {oidc.user_getfield("email")}'
    else:
        return 'Welcome to the Multi-cloud SSO System. Please log in.'

# Login route (protected)
@app.route('/login')
@oidc.require_login
def login():
    return redirect(url_for('dashboard'))

# Dashboard (protected and requires login)
@app.route('/dashboard')
@oidc.require_login
def dashboard():
    user_info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    roles = get_roles_from_keycloak(user_info['sub'])
    
    return render_template('dashboard.html', username=user_info['preferred_username'], roles=roles)

# Logout route
@app.route('/logout')
def logout():
    oidc.logout()
    return redirect(url_for('home'))

# Helper function to get user roles from Keycloak Admin API
def get_roles_from_keycloak(user_id):
    token = oidc.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    url = f"http://localhost:8080/auth/admin/realms/my_realm/users/user_id/role-mappings/realm"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        roles = json.loads(response.content)
        return roles
    else:
        return []

# Function to assign a role to a user
def assign_role_to_user(user_id, role_name):
    token = oidc.get_access_token()
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f"http://localhost:8080/auth/admin/realms/your_realm/users/user_id/role-mappings/realm"

    # Define the role JSON object
    role_data = {
        "name": role_name,
        "clientRole": False
    }

    response = requests.post(url, headers=headers, json=[role_data])
    return response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
