from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login

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

        # 作成後自動的にログイン
        login(request, user)

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

@api_view(['POST'])
def login_view(request):
    """
    ログインAPI
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not all([username, password]):
        return Response(
            {'error': 'ユーザー名とパスワードを入力してください'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({
            'message': 'ログインしました',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    else:
        return Response(
            {'error': 'ユーザー名またはパスワードが正しくありません'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
def get_user(request):
    """
    現在のログインユーザーの情報を取得するAPI
    """
    if request.user.is_authenticated:
        return Response({
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    return Response({'error': '認証されていません'}, status=status.HTTP_401_UNAUTHORIZED)
