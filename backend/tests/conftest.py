"""Fixtures partagees : force un environnement de dev/sqlite propre et
isole avant que app.main soit importe (ses effets de bord au chargement -
valider_configuration, create_all - dependent de app.config.settings).

Un fichier sqlite reel (pas ":memory:") : en memoire, chaque nouvelle
connexion du pool verrait une base differente et vide (create_all() au
chargement porterait sur une connexion, les requetes des tests sur une
autre) - un fichier partage evite ce piege sans toucher au pooling de
database.py, qui doit rester identique a la production."""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="suite_artisan_tests_")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
