# Configuration file for the Sphinx documentation builder.

project = "wagtail-dsfr"
copyright = "2025, DINUM"
author = "DINUM"
release = "2.1.0"

extensions = [
    "sphinx_wagtail_theme",
    "myst_parser",  # For Markdown support
]

# MyST Parser configuration for Markdown support
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "fr"

html_theme = "sphinx_wagtail_theme"
html_static_path = ["_static"]
html_baseurl = "https://wagtail-dsfr.fabien.cool/"

html_theme_options = {
    "project_name": "wagtail-dsfr",
    "github_url": "https://github.com/fabienheureux/wagtail-dsfr/",
    "logo": "logo.svg",
    "logo_alt": "wagtail-dsfr",
}

html_context = {
    "github_user": "fabienheureux",
    "github_repo": "wagtail-dsfr",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
