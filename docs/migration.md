# Migration d'un site Wagtail existant

Ce guide réduit la migration à l'essentiel : sauvegarder, installer, migrer, mettre à jour les ContentTypes.

## 1. Sauvegarder
- Exportez la base : `python manage.py dumpdata > backup.json` (ou votre méthode habituelle).
- Sauvegardez les fichiers médias si nécessaire.

## 2. Installer wagtail-dsfr
- Ajoutez la dépendance : `pip install wagtail-dsfr`.
- Suivez la {doc}`page d'installation <guide/installation>` pour compléter `INSTALLED_APPS` et les context processors (pas de configuration Django/Wagtail générique ici : voir leurs docs officielles).

## 3. Appliquer les migrations
```bash
python manage.py migrate
python manage.py collectstatic
```

## 4. Mettre à jour les ContentTypes
Lancez la commande fournie pour réaligner les ContentTypes de l’ancien projet Sites Faciles vers `wagtail_dsfr` :

```bash
python manage.py migrate_contenttype --dry-run
python manage.py migrate_contenttype
```

La commande se trouve dans `wagtail_dsfr/management/commands/migrate_contenttype.py` et gère :
- Le basculement des `ContentType` `blog`, `events`, `forms`, `content_manager`, `config` vers leurs équivalents `wagtail_dsfr_*`
- La mise à jour des pages existantes pour pointer vers les nouveaux types

## 5. Vérifier
- Parcourez vos pages principales et l’admin Wagtail pour valider le rendu DSFR.
- Inspirez-vous du projet `demo/` pour les gabarits (header, footer, menus). Toute personnalisation Wagtail/Django non spécifique à `wagtail_dsfr` reste documentée sur <https://docs.wagtail.org/> et <https://docs.djangoproject.com/>.
