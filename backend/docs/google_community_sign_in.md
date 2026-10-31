# Optional Google sign-in for Farmer Community

Google sign-in is optional. Email and password remain available, and the Google button stays hidden until both OAuth credentials are configured on the backend.

## Configure Google Cloud

1. Create an OAuth 2.0 **Web application** client in Google Cloud Console and configure the consent screen for the intended users.
2. Add the exact backend callback as an authorized redirect URI:
   - Local: `http://localhost:8002/community/auth/google/callback`
   - Production: `https://<api-host>/community/auth/google/callback`
3. Configure the backend environment:

   ```dotenv
   GOOGLE_OAUTH_CLIENT_ID=<web-client-id>
   GOOGLE_OAUTH_CLIENT_SECRET=<web-client-secret>
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8002/community/auth/google/callback
   COMMUNITY_GOOGLE_CALLBACK_URL=http://localhost:8501/Community
   ```

   The backend and frontend callback URLs must share a hostname so the browser can carry the short-lived, HttpOnly handoff cookie. If production uses separate subdomains such as `api.example.org` and `app.example.org`, set `COMMUNITY_GOOGLE_HANDOFF_COOKIE_DOMAIN=example.org` (the shared parent domain, not a public suffix). For production, use HTTPS for both callback URLs. Keep the client secret in the backend environment only. Do not expose it to Streamlit or commit it.

4. Apply migrations `0016_community_google_sign_in.sql`, `0017_dynamic_field_mapping.sql`, and `0018_google_oauth_browser_binding.sql` in numeric order, then restart the API and Streamlit.

Google sign-in requests only the OpenID Connect `openid email profile` scopes. The API validates Google's signed ID token, audience, expiry, nonce, and verified-email claim. It uses state, PKCE, short-lived HttpOnly cookies, and a single-use handoff code bound to the browser that started sign-in before issuing an Agri-Menya Community session.

A Google sign-in can create a Farmer account. It can automatically link to an existing Community account only when Google controls the email domain (a Gmail address or matching Google Workspace hosted domain). Otherwise, the user must continue using the account's existing sign-in method; a third-party email's Google verification alone is not treated as sufficient proof to link accounts.

Google Cloud Console requires the redirect URI to match exactly, including scheme, hostname, port, path, and trailing slash. See Google's [web server OAuth guide](https://developers.google.com/identity/protocols/oauth2/web-server) and [OpenID Connect guide](https://developers.google.com/identity/openid-connect/openid-connect).
