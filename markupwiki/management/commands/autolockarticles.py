from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min
from markupwiki.models import Article, PUBLIC, LOCKED, DELETED
import datetime

class Command(BaseCommand):
    help = 'Auto-locks articles based on time and other factors'

    def handle(self, *args, **options):
        ''' Lock any public article that was created earlier than
            MARKUPWIKI_AUTOLOCK_TIMEDELTA ago.
        '''
        
        timedelta = getattr(settings, 'MARKUPWIKI_AUTOLOCK_TIMEDELTA', None)
        
        if timedelta is not None:
            
            ts = datetime.datetime.now() - timedelta
            qs = Article.objects.filter(status=PUBLIC).annotate(
                    timestamp=Min('versions__timestamp')).filter(timestamp__lte=ts)
            qs.update(status=LOCKED)
