# ADR-004: Gestion des Dépendances (Poetry)

* **Status**: Accepted
* **Date**: 2025-12-23

## Context
La gestion des librairies Python se faisait via des commandes `pip install` manuelles dans le Dockerfile.
Risque : Divergence de versions entre le développement et la production, ou cassure du build si une librairie met à jour une dépendance transitrice.

## Decision
Adopter **Poetry** comme gestionnaire de paquets unique.

## Consequences
### ✅ Positif
*   **Lock File** : `poetry.lock` garantit des builds déterministes.
*   **Résolution** : Gestion intelligente des conflits de versions.
*   **Standards** : Utilisation de `pyproject.toml`.

### ❌ Négatif
*   Dockerfile plus complexe (multi-stage ou configuration spécifique).
*   Nécessite d'apprendre les commandes Poetry (`poetry add` vs `pip install`).
