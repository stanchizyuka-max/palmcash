# Google OAuth Setup Instructions

## 🚀 **Setting Up Google OAuth for Palm Cash**

### **Step 1: Install Required Packages**

```bash
pip install django-allauth[socialaccount]==0.57.0 requests==2.31.0 requests-oauthlib==1.3.1
```

### **Step 2: Create Google OAuth Application**

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project** or select existing project
3. **Enable APIs**:
   - Go to "APIs & Services" → "Library"
   - Search and enable "Google+ API" and "Google People API"
4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Select "Web application"
   - Add authorized redirect URI: `https://yourdomain.com/accounts/google/login/callback/`
   - For development: `http://localhost:8000/accounts/google/login/callback/`
5. **Copy Client ID and Client Secret**

### **Step 3: Update Environment Variables**

Add to your `.env` file:
```bash
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret-here
```

### **Step 4: Run Migrations**

```bash
python manage.py migrate
```

### **Step 5: Create Superuser (if needed)**

```bash
python manage.py createsuperuser
```

### **Step 6: Test the Implementation**

1. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```

2. **Test Google Login**:
   - Go to `http://localhost:8000/accounts/login/`
   - Click "Continue with Google"
   - Complete Google authentication
   - Should redirect to dashboard

### **Step 7: Production Deployment**

For PythonAnywhere or other hosting:

1. **Update Redirect URI** in Google Console:
   - `https://yourdomain.com/accounts/google/login/callback/`

2. **Update ALLOWED_HOSTS** in settings:
   ```python
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

3. **Set Environment Variables** in hosting panel:
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `GOOGLE_OAUTH_CLIENT_SECRET`

## 🔧 **How It Works**

### **User Flow:**
1. User clicks "Continue with Google"
2. Redirected to Google for authentication
3. Google redirects back with authorization code
4. System exchanges code for access token
5. Gets user profile data (name, email)
6. Creates or links user account
7. Logs user in and redirects to dashboard

### **Account Creation Logic:**
- **New Users**: Creates account with Google data, sets role to 'borrower'
- **Existing Users**: Links Google account to existing Palm Cash account
- **Auto-Verification**: Google users are marked as verified

### **Security Features:**
- Email verification required for new accounts
- Secure OAuth 2.0 flow
- CSRF protection on all forms
- Session-based authentication

## 🎯 **Features Implemented**

✅ **Google OAuth Login**: Users can login with Google account
✅ **Auto Registration**: New users automatically registered
✅ **Account Linking**: Existing users can link Google accounts
✅ **Email Verification**: Required for new accounts
✅ **Role Assignment**: New users default to 'borrower' role
✅ **Profile Sync**: Name and email synced from Google
✅ **Secure Flow**: OAuth 2.0 with proper security
✅ **Error Handling**: User-friendly error messages
✅ **Responsive Design**: Works on all devices

## 🚨 **Important Notes**

1. **HTTPS Required**: Google OAuth requires HTTPS in production
2. **Domain Verification**: Add your domain to Google Console
3. **Rate Limits**: Google has API rate limits
4. **User Consent**: Users must consent to data sharing
5. **Privacy Policy**: Have a privacy policy for compliance

## 🔍 **Troubleshooting**

### **Common Issues:**
- **Redirect URI Mismatch**: Check Google Console settings
- **Client ID/Secret Wrong**: Verify environment variables
- **HTTPS Issues**: Use HTTPS in production
- **CORS Errors**: Check ALLOWED_HOSTS setting

### **Debug Mode:**
Add to settings for debugging:
```python
DEBUG = True
```

## 📞 **Support**

For issues with Google OAuth setup:
1. Check Google Cloud Console settings
2. Verify environment variables
3. Check Django error logs
4. Test with different Google accounts
