from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
import jwt  # Add this import at the top
from dotenv import load_dotenv
import boto3  # Add this import

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key in production
oauth = OAuth(app)


oauth.register(
  name='oidc',
  authority=os.getenv('AUTHORITY'),
  client_id=os.getenv('CLIENT_ID'),
  client_secret=os.getenv('CLIENT_SECRET'),
  server_metadata_url=os.getenv('SERVER_METADATA_URL'),
  client_kwargs={'scope': 'email openid phone'}
)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    print(f'session: {session}')
    # Fix: Get cognito:groups from the user object
    groups = session.get('user', {}).get('cognito:groups', [])
    print(f'groups: {groups}')
    if not groups:
        return "No access: User is not in any Cognito group."

    # Determine dashboard ID based on group
    dashboard_id = None
    if 'Sales' in groups:
        dashboard_id = os.getenv('SALES_DASHBOARD_ID')
    elif 'HR' in groups:
        dashboard_id = os.getenv('HR_DASHBOARD_ID')
    else:
        return "No access: User group not authorized."

    # Generate embed URL
    quicksight = boto3.client(
        'quicksight',
        region_name='ap-southeast-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    try:
        # try using identity type Quicksight
        # Check if user is not allowed to see certain dashboards
        response = quicksight.get_dashboard_embed_url(
            AwsAccountId=os.getenv('AWS_ACCOUNT_ID'),
            DashboardId=dashboard_id,
            IdentityType='QUICKSIGHT',
            UserArn=f"arn:aws:quicksight:ap-southeast-1:{os.getenv('AWS_ACCOUNT_ID')}:user/default/{user.get('email', 'unknown')}",
            SessionLifetimeInMinutes=120
        )
        print(f'response: {response}')
        embed_url = response['EmbedUrl']
        return f'''
            <iframe src="{embed_url}" width="100%" height="700px"></iframe>
            <a href="/logout">Logout</a>
        '''
    except Exception as e:
        return f"Error loading dashboard: {str(e)}"

@app.route('/authorize')
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token['userinfo']
    session['user'] = user

    # Decode ID token to get Cognito groups
    id_token = token['id_token']
    try:
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        groups = decoded.get('cognito:groups', [])
        session['groups'] = groups  # Store groups in session
        print(f"User groups: {groups}")
    except Exception as e:
        print(f"Error decoding token: {e}")

    return redirect(url_for('index'))

@app.route('/')
def index():
    user = session.get('user')
    if user:
        return f'''
            Hello, {user["email"]}! 
            <a href="/dashboard">View Dashboard</a> | 
            <a href="/logout">Logout</a>
        '''
    else:
        return 'Welcome! Please <a href="/login">Login</a>.'
    

@app.route('/login')
def login():
    # Alternate option to redirect to /authorize
    # redirect_uri = url_for('authorize', _external=True)
    # return oauth.oidc.authorize_redirect(redirect_uri)
    return oauth.oidc.authorize_redirect('http://localhost:5000/authorize')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

    