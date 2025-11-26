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

Configurez les URLs dans votre `urls.py` :

```python
# Option 1 : Utiliser directement la configuration d'URLs de wagtail_dsfr (recommandé)
from wagtail_dsfr.config.urls import *

# Option 2 : Configuration personnalisée
# Si vous avez besoin de personnaliser les URLs, vous pouvez copier le contenu
# de wagtail_dsfr.config.urls et l'adapter à vos besoins
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

Lorsque vous renommez des applications Django (par exemple de `blog` à `wagtail_dsfr_blog`), Django crée de nouveaux ContentTypes. Les pages Wagtail existantes référencent toujours les anciens ContentTypes, ce qui provoque l'erreur :

```
PageClassNotFoundError: The page 'xxx' cannot be edited because the model class
used to create it (blog.blogindexpage) can no longer be found in the codebase.
```

La commande `migrate_contenttype` résout ce problème en mettant à jour toutes les références.

## Modèles de pages personnalisés

wagtail_dsfr utilise des modèles de pages configurables, similaires au système `AUTH_USER_MODEL` de Django ou `WAGTAILIMAGES_IMAGE_MODEL` de Wagtail.

### Modèles par défaut

Par défaut, le package fournit les modèles concrets suivants :
- `wagtail_dsfr_blog.BlogIndexPage`
- `wagtail_dsfr_blog.BlogEntryPage`
- `wagtail_dsfr_events.EventsIndexPage`
- `wagtail_dsfr_events.EventEntryPage`
- `wagtail_dsfr_content_manager.ContentPage`

### Utilisation de modèles personnalisés

Si vous souhaitez personnaliser complètement ces modèles (par exemple, pour modifier les StreamField disponibles), vous pouvez créer vos propres modèles et les configurer via les settings Django.

#### Étape 1 : Créer vos modèles personnalisés

Par exemple, pour créer un modèle de blog personnalisé avec des blocs supplémentaires :

```python
# myapp/models.py
from wagtail_dsfr.blog.models import BlogIndexPage as AbstractBlogIndexPage
from wagtail_dsfr.blog.models import BlogEntryPage as AbstractBlogEntryPage
from wagtail.fields import StreamField
from wagtail import blocks

# Définir vos blocs personnalisés
CUSTOM_BLOCKS = [
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('custom_block', MyCustomBlock()),  # Votre bloc personnalisé
]

class CustomBlogIndexPage(AbstractBlogIndexPage):
    # Vous pouvez ajouter des champs supplémentaires ici si nécessaire
    class Meta:
        verbose_name = "Index de blog personnalisé"

class CustomBlogEntryPage(AbstractBlogEntryPage):
    # Surcharger le StreamField avec vos blocs personnalisés
    body = StreamField(CUSTOM_BLOCKS, blank=True, use_json_field=True)
    
    class Meta:
        verbose_name = "Article de blog personnalisé"
```

#### Étape 2 : Configurer les settings

```python
# settings.py
{package_name_upper}_BLOG_INDEX_MODEL = 'myapp.CustomBlogIndexPage'
{package_name_upper}_BLOG_ENTRY_MODEL = 'myapp.CustomBlogEntryPage'
{package_name_upper}_EVENTS_INDEX_MODEL = 'myapp.CustomEventsIndexPage'
{package_name_upper}_EVENTS_ENTRY_MODEL = 'myapp.CustomEventEntryPage'
{package_name_upper}_CONTENT_PAGE_MODEL = 'myapp.CustomContentPage'
```

#### Étape 3 : Créer et appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

**Important :** Cette configuration doit être faite **avant** de créer votre première page. Si vous avez déjà des pages existantes, vous devrez migrer les données.

### Helper functions

Le package fournit des fonctions helpers pour obtenir les modèles configurés :

```python
from wagtail_dsfr.utils.models import (
    get_blog_index_model,
    get_blog_entry_model,
    get_events_index_model,
    get_events_entry_model,
    get_content_page_model,
)

# Obtenir le modèle configuré
BlogIndexPage = get_blog_index_model()
```

### Créer des blocs personnalisés avec références de modèles

Le package fournit des blocs `ChooserBlock` qui utilisent automatiquement les modèles configurés. Cela vous permet de créer des blocs personnalisés qui référencent les bonnes pages, même si vous utilisez des modèles personnalisés.

#### Exemple : Bloc de mise en avant d'articles

```python
# myapp/blocks.py
from wagtail import blocks
from wagtail_dsfr.content_manager.blocks.choosers import BlogIndexChooserBlock

class FeaturedArticlesBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Titre de la section")
    blog = BlogIndexChooserBlock(label="Blog source")
    number_of_articles = blocks.IntegerBlock(
        label="Nombre d'articles",
        min_value=1,
        max_value=10,
        default=3
    )
    
    class Meta:
        icon = "list-ul"
        template = "blocks/featured_articles.html"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        blog = value.get('blog')
        if blog:
            # Le bloc utilisera automatiquement le bon modèle
            context['articles'] = blog.posts[:value.get('number_of_articles', 3)]
        return context
```

#### Blocs disponibles

Le package fournit les chooser blocks suivants :

- `BlogIndexChooserBlock` - Pour sélectionner une page d'index de blog
- `EventsIndexChooserBlock` - Pour sélectionner une page d'index d'événements

Ces blocs s'adaptent automatiquement si vous configurez des modèles personnalisés via les settings.

#### Exemple d'utilisation dans un StreamField

```python
# myapp/models.py
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail_dsfr.content_manager.blocks.choosers import (
    BlogIndexChooserBlock,
    EventsIndexChooserBlock,
)

class MyCustomPage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('blog_reference', BlogIndexChooserBlock(label="Référence vers un blog")),
        ('events_reference', EventsIndexChooserBlock(label="Référence vers un calendrier")),
        ('featured_articles', FeaturedArticlesBlock()),
    ], blank=True, use_json_field=True)
```

## Documentation

Pour plus d'informations sur l'utilisation de Sites Faciles, consultez la [documentation officielle](https://github.com/numerique-gouv/sites-faciles).

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Crédits

Ce package est basé sur [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) développé par la DINUM.
