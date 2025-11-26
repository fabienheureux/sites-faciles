# {package_name}

Package Python pour {package_verbose_name}, un gestionnaire de contenu permettant de créer et gérer un site internet basé sur le Système de design de l'État (DSFR), accessible et responsive.

Ce package est généré automatiquement à partir du projet [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) officiel.

## Installation

```bash
pip install {package_name}
```

Ou avec poetry :

```bash
poetry add {package_name}
```

## Utilisation

Ajoutez les applications à votre `INSTALLED_APPS` dans `settings.py` :

```python
INSTALLED_APPS = [
    # ... vos autres apps
    "dsfr",
    "{package_name}",
    "{package_name}.blog",
    "{package_name}.content_manager",
    "{package_name}.events",
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
        "{package_name}.content_manager.context_processors.skiplinks",
        "{package_name}.content_manager.context_processors.mega_menus",
    ]
)
```

Configurez les URLs dans votre `urls.py` :

```python
# Option 1 : Utiliser directement la configuration d'URLs de {package_name} (recommandé)
from {package_name}.config.urls import *

# Option 2 : Configuration personnalisée
# Si vous avez besoin de personnaliser les URLs, vous pouvez copier le contenu
# de {package_name}.config.urls et l'adapter à vos besoins
```

## Migration depuis Sites Faciles

Si vous migrez un site existant depuis le dépôt Sites Faciles vers ce package, vous devez mettre à jour les références ContentType dans votre base de données.

### Étapes de migration

1. **Installez le package** comme décrit ci-dessus et ajoutez toutes les applications à `INSTALLED_APPS`

2. **Exécutez les migrations Django** pour créer les nouveaux ContentTypes :
   ```bash
   python manage.py migrate
   ```

3. **Migrez les ContentTypes existants** :
   ```bash
   python manage.py migrate_contenttype
   ```

   Cette commande va :
   - Identifier tous les ContentTypes de l'ancienne structure (blog, events, forms, content_manager, config)
   - Mettre à jour toutes les pages Wagtail pour pointer vers les nouveaux ContentTypes
   - Supprimer les anciens ContentTypes

4. **Vérifiez la migration** (optionnel - mode dry-run) :
   ```bash
   python manage.py migrate_contenttype --dry-run
   ```

### Pourquoi cette migration est nécessaire

Lorsque vous renommez des applications Django (par exemple de `blog` à `{package_name}_blog`), Django crée de nouveaux ContentTypes. Les pages Wagtail existantes référencent toujours les anciens ContentTypes, ce qui provoque l'erreur :

```
PageClassNotFoundError: The page 'xxx' cannot be edited because the model class
used to create it (blog.blogindexpage) can no longer be found in the codebase.
```

La commande `migrate_contenttype` résout ce problème en mettant à jour toutes les références.

## Personnalisation avec des blocs custom

{package_name} fournit un système de registre permettant d'ajouter facilement vos propres blocs StreamField personnalisés à tous les éditeurs de contenu.

### Utilisation du registre de blocs

Pour ajouter vos propres blocs au StreamField commun, utilisez le décorateur `@register_common_block` :

```python
from {package_name}.content_manager.registry import register_common_block
from wagtail import blocks

@register_common_block(
    label="Mon Bloc Personnalisé",
    group="Mes Blocs"
)
class MonBlocCustom(blocks.StructBlock):
    titre = blocks.CharBlock(label="Titre")
    contenu = blocks.RichTextBlock(label="Contenu")
    
    class Meta:
        icon = "doc-full"
        template = "blocks/mon_bloc_custom.html"
```

### Paramètres du décorateur

Le décorateur `@register_common_block` accepte les paramètres suivants :

- **`name`** (optionnel) : Nom unique du bloc. Si non fourni, le nom de la classe en snake_case est utilisé
- **`label`** (optionnel) : Libellé affiché dans l'éditeur. Si non fourni, le nom de la classe formaté est utilisé
- **`group`** (optionnel) : Groupe dans lequel ranger le bloc dans l'interface d'édition
- **`**block_kwargs`** : Arguments supplémentaires passés au bloc (ex: `icon`, `template`, etc.)

### Exemple complet

```python
# Dans votre application Django (ex: myapp/blocks.py)
from {package_name}.content_manager.registry import register_common_block
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

@register_common_block(
    label="Carte avec image",
    group="Composants personnalisés",
    icon="image"
)
class CarteImageBlock(blocks.StructBlock):
    titre = blocks.CharBlock(label="Titre de la carte")
    image = ImageChooserBlock(label="Image")
    description = blocks.TextBlock(label="Description")
    lien = blocks.URLBlock(label="Lien", required=False)
    
    class Meta:
        template = "blocks/carte_image.html"

@register_common_block(
    label="Citation mise en avant",
    group="Composants personnalisés"
)
class CitationBlock(blocks.StructBlock):
    citation = blocks.TextBlock(label="Citation")
    auteur = blocks.CharBlock(label="Auteur", required=False)
    source = blocks.CharBlock(label="Source", required=False)
    
    class Meta:
        icon = "openquote"
        template = "blocks/citation.html"
```

### Chargement automatique

Les blocs enregistrés sont automatiquement ajoutés à `STREAMFIELD_COMMON_BLOCKS` au démarrage de l'application, grâce au hook `ready()` de `ContentManagerConfig`. Assurez-vous simplement que votre fichier contenant les blocs personnalisés est importé au démarrage de votre application.

Pour cela, vous pouvez par exemple importer vos blocs dans le fichier `apps.py` de votre application :

```python
# Dans votre myapp/apps.py
from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        # Importer vos blocs pour qu'ils soient enregistrés
        from . import blocks  # noqa
```

## Documentation

Pour plus d'informations sur l'utilisation de Sites Faciles, consultez la [documentation officielle](https://github.com/numerique-gouv/sites-faciles).

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Crédits

Ce package est basé sur [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) développé par la DINUM.
