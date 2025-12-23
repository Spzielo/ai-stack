# ADR-003: Système de Notifications (Slack vs Pushover)

* **Status**: Accepted
* **Date**: 2025-12-23

## Context
Le système doit pouvoir notifier l'utilisateur humain de deux types d'événements :
1.  **Logs** : Activité normale (ex: "Capture traitée").
2.  **Alertes** : Problèmes ou décisions requises.

Nous avons initialement implémenté Pushover pour sa simplicité mobile.

## Decision
Abandonner Pushover au profit de **Slack (Incoming Webhooks)**.

## Consequences
### ✅ Positif
*   **Granularité** : Slack permet de router vers des canaux distincts (`#log`, `#alert`).
*   **Richesse** : Formatage "Block Kit" (couleurs, boutons, mise en page) impossible sur Pushover.
*   **Historique** : Les logs sont conservés et recherchables dans un outil dédié au travail.

### ❌ Négatif
*   Configuration un peu plus lourde (création d'App, Webhooks).
*   App mobile Slack moins "alerte pure" que Pushover.
