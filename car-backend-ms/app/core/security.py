import firebase_admin
from firebase_admin import auth, credentials

from config import get_settings


def _get_app() -> firebase_admin.App:
    """Return the default Firebase app, initializing it on first call."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        settings = get_settings()
        # On Cloud Run, Application Default Credentials are picked up automatically
        # from the attached service account. Locally, set GOOGLE_APPLICATION_CREDENTIALS
        # to a downloaded service account key JSON file.
        cred = credentials.ApplicationDefault()
        return firebase_admin.initialize_app(
            cred, {"projectId": settings.FIREBASE_PROJECT_ID}
        )


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    _get_app()
    return auth.verify_id_token(id_token)
