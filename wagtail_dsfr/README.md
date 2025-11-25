# wagtail_dsfr

Package Python pour Wagtail Dsfr, un gestionnaire de contenu permettant de créer et gérer un site internet basé sur le Système de design de l'État (DSFR), accessible et responsive.

Ce package est généré automatiquement à partir du projet [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) officiel.

## Installation

```bash
pip install wagtail_dsfr
```

Ou avec poetry :

```bash
poetry add wagtail_dsfr
```

## Utilisation

Ajoutez les applications à votre `INSTALLED_APPS` dans `settings.py` :

```python
INSTALLED_APPS = [
    # ... vos autres apps
    "dsfr",
    "wagtail_dsfr",
    "wagtail_dsfr.blog",
    "wagtail_dsfr.content_manager",
    "wagtail_dsfr.events",
    "wagtail.contrib.settings",
    "wagtail.contrib.typed_table_block",
    "wagtail.contrib.routable_page",
    "wagtail_modeladmin",
    "wagtailmenus",
    "wagtailmarkdown",
]
```

Ajoutez les context processors nécessaires :

```python
TEMPLATES[0]["OPTIONS"]["context_processors"].extend(
    [
        "wagtailmenus.context_processors.wagtailmenus",
        "wagtail_dsfr.content_manager.context_processors.skiplinks",
        "wagtail_dsfr.content_manager.context_processors.mega_menus",
    ]
)
```

## Documentation

Pour plus d'informations sur l'utilisation de Sites Faciles, consultez la [documentation officielle](https://github.com/numerique-gouv/sites-faciles).

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Crédits

Ce package est basé sur [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) développé par la DINUM.
