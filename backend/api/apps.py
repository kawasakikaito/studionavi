from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        """
        Djangoアプリケーション起動時にスクレイパーを初期化
        """
        from .scrapers.scraper_registry import AvailabilityService
        
        service = AvailabilityService()
        service.initialize_scrapers()