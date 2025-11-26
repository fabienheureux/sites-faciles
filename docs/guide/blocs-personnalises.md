# Blocs StreamField

wagtail-dsfr fournit une collection de blocs StreamField adaptés au DSFR pour composer vos pages sans réinventer les composants.

## Ajouter les blocs à vos pages

```python
from wagtail.fields import StreamField
from wagtail_dsfr.content_manager.blocks import STREAMFIELD_COMMON_BLOCKS, HERO_STREAMFIELD_BLOCKS

class ContentPage(Page):
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS + HERO_STREAMFIELD_BLOCKS,
        use_json_field=True,
    )
```

- `STREAMFIELD_COMMON_BLOCKS` : alertes, accordéons, cartes, tableaux, boutons, listes, etc.
- `HERO_STREAMFIELD_BLOCKS` : variantes d’en-têtes (bandeau, image + texte, fond héro).

## Astuces d'intégration

- Combinez les blocs DSFR avec vos blocs maison en ajoutant vos tuples à la liste passée au `StreamField`.
- Pour le templating, utilisez les conventions Wagtail (héritage de `base.html`, blocs `{% block %}`) et référez-vous à la doc officielle : <https://docs.wagtail.org/en/stable/topics/streamfield.html>.
- Inspirez-vous du projet `demo/` pour voir les blocs en situation (héros, pages de blog, etc.).
