from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


def blacklist_all_user_tokens(user):
        """
        Blacklists all outstanding refresh tokens for a given user.
        """
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for token_obj in outstanding_tokens:
            try:
                # Reconstruct RefreshToken object from the raw token
                refresh_token = RefreshToken(token_obj.token)
                refresh_token.blacklist()
            except Exception as e:
                print(f"Error blacklisting token {token_obj.token}: {e}")
        print(f"All tokens for user {user.username} have been blacklisted.")