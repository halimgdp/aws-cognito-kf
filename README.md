# Flask QuickSight Dashboard with Cognito Authentication

## How to install

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file with your AWS credentials:
   ```env
   AUTHORITY=https://cognito-idp.{region}.amazonaws.com/{user-pool-id}
   CLIENT_ID=your-cognito-app-client-id
   CLIENT_SECRET=your-cognito-app-client-secret
   SERVER_METADATA_URL=https://cognito-idp.{region}.amazonaws.com/{user-pool-id}/.well-known/openid_configuration
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_ACCOUNT_ID=your-aws-account-id
   SALES_DASHBOARD_ID=your-sales-dashboard-id
   HR_DASHBOARD_ID=your-hr-dashboard-id
   ```

## How to run

1. Run Python flask:
   ```bash
   python3 main.py
   ```

2. Open browser to http://localhost:5000 
