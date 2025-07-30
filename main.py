from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
import os
import jwt  # Add this import at the top
from dotenv import load_dotenv
import boto3  # Add this import

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key in production
oauth = OAuth(app)

admin_email = [
    "syihabuddin.y.muhammad@gdplabs.id",
    "michael.h.senatra@gdplabs.id"
    ]

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
    user = session.get('user', {})
    groups = user.get('cognito:groups', [])
    print(f'groups: {groups}')
    
    if not groups:
        return render_template('dashboard.html', error="No access: User is not in any Cognito group.")

    # Determine dashboard ID based on group
    dashboard_id = None
    if 'Sales' in groups:
        dashboard_id = os.getenv('SALES_DASHBOARD_ID')
    elif 'HR' in groups:
        dashboard_id = os.getenv('HR_DASHBOARD_ID')
    else:
        return render_template('dashboard.html', error="No access: User group not authorized.")

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
        user_email = user.get('email', 'unknown')
        if user_email in admin_email:
            user_email = "millenio.ramadizsa@gdplabs.id"  # Use a default email for admin users
        response = quicksight.get_dashboard_embed_url(
            AwsAccountId=os.getenv('AWS_ACCOUNT_ID'),
            DashboardId=dashboard_id,
            IdentityType='QUICKSIGHT',
            UserArn=f"arn:aws:quicksight:ap-southeast-1:{os.getenv('AWS_ACCOUNT_ID')}:user/default/{user_email}",
            SessionLifetimeInMinutes=120
        )
        print(f'response: {response}')
        embed_url = response['EmbedUrl']
        return render_template('dashboard.html', embed_url=embed_url)
    except Exception as e:
        return render_template('dashboard.html', error=f"Error loading dashboard: {str(e)}")


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
    return render_template('index.html', user=user)
    

@app.route('/login')
def login():
    # Use url_for to automatically construct the correct redirect URI for any environment
    redirect_uri = url_for('authorize', _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('HOST'), port=os.getenv('PORT'))