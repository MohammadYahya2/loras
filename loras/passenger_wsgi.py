import os
import sys

# أضف جذر المشروع إلى PYTHONPATH
project_home = '/home/almalsxs/repositories/loras123'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ابدأ إعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loras.settings')

# حمّل تطبيق WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
