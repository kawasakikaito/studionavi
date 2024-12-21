from django.core.management.base import BaseCommand
from api.factories import StudioFactory

class Command(BaseCommand):
    help = 'テストデータを作成するコマンド'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='作成するデータの数')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        
        self.stdout.write('テストデータを作成中...')
        
        # 指定された数のテストデータを作成
        studios = StudioFactory.create_batch(count)
        
        self.stdout.write(self.style.SUCCESS(f'{count}件のスタジオデータを作成しました'))
        
        # 作成したデータの確認
        for studio in studios:
            self.stdout.write(f"- {studio.name}: {studio.address}")