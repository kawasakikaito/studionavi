from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

@api_view(['POST'])
def register(request):
    """
    ユーザー登録API
    """
    try:
        # リクエストデータのバリデーション
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([username, email, password]):
            return Response(
                {'error': '必須フィールドが不足しています'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # パスワードの検証
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {'error': e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ユーザー名とメールアドレスの重複チェック
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'このユーザー名は既に使用されています'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'このメールアドレスは既に使用されています'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ユーザーの作成
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return Response(
            {
                'message': 'ユーザー登録が完了しました',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'error': '予期せぬエラーが発生しました'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
