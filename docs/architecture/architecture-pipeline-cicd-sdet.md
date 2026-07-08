# Architecture d'un Pipeline CI/CD de Test — De la User Story à l'Agent IA

## Résumé exécutif

L'objectif est de construire, à partir d'une **User Story**, un pipeline CI/CD complet et démontrable qui couvre tout le cycle de qualité logicielle : qualité de code en local (pre-commit), tests automatisés à tous les niveaux de la pyramide (unitaires, API, smoke, non-régression), exécution orchestrée en CI/CD (GitHub Actions / GitLab CI), reporting consolidé (Cucumber, Cypress Cloud, Power BI) et alerting multicanal (Teams, Slack, Discord, Gmail).

Ce document n'est pas une simple liste d'outils : c'est une architecture pensée comme un **produit interne**, avec une traçabilité de bout en bout entre l'exigence métier (la User Story) et le résultat de test remonté au bon interlocuteur, au bon moment, sur le bon canal. C'est cette traçabilité qui constitue la fondation sur laquelle viendra se greffer, en phase 2, l'agent IA.

Pitch en une phrase pour un recruteur : *"J'ai construit un pipeline qui transforme une User Story en tests exécutables, exécute ces tests à chaque commit, et informe automatiquement la bonne personne, avec la bonne donnée, sur le bon outil — le tout observable dans un dashboard business."*

---

## 1. Principe fondateur : la User Story comme source de vérité unique

Tout part de la User Story rédigée au format `En tant que... je veux... afin de...` accompagnée de critères d'acceptation au format Gherkin (`Given / When / Then`).

**Pitch** : au lieu de considérer la User Story comme un simple ticket Jira, elle devient un **artefact versionné** dans le repository (dossier `features/`). Elle sert de contrat entre le Product Owner, le Dev et le QA. C'est cette discipline qui permettra plus tard à un LLM de lire la User Story et de générer automatiquement des scénarios Gherkin, puis des tests Cypress — la BDD n'est donc pas un choix stylistique, c'est le pont entre langage métier et langage machine.

Chaque User Story est taguée dès la rédaction avec un niveau de criticité (`@smoke`, `@regression`, `@critical`, `@api`) qui pilotera ensuite la stratégie d'exécution en CI.

---

## 2. Architecture globale — vue en couches

L'architecture se lit en 5 couches, de la plus locale à la plus visible :

1. **Couche Qualité locale** (pre-commit) — bloque les erreurs avant même le push.
2. **Couche Test** (pyramide de tests) — unitaire, API, UI smoke, UI régression.
3. **Couche Orchestration CI/CD** (GitHub Actions / GitLab CI) — déclenche, parallélise, isole.
4. **Couche Reporting** (Cucumber, Cypress Cloud, Power BI) — transforme la donnée brute en insight.
5. **Couche Alerting** (Teams, Slack, Discord, Gmail) — pousse l'information vers l'humain sans qu'il ait à aller la chercher.

**Pitch** : cette séparation en couches est volontairement calquée sur une architecture d'entreprise réelle (observabilité + CI/CD + collaboration), ce qui permet de justifier chaque choix technique en entretien avec un vocabulaire d'architecte, pas seulement de testeur.

---

## 3. Organisation du repository

Structure logique recommandée (description, pas de code) :

- `features/` : fichiers Gherkin, un fichier par User Story, nommage `US-XXX-nom-fonctionnalite.feature`
- `cypress/e2e/` : step definitions et specs UI, organisées par domaine fonctionnel (pas par type de test)
- `cypress/api/` : specs de tests API, séparées des tests UI pour permettre une exécution indépendante et plus rapide
- `tests/unit/` : tests unitaires des fonctions utilitaires, des commandes custom Cypress, et de la logique métier front si applicable
- `.github/workflows/` et `.gitlab-ci.yml` : pipelines, avec un fichier par déclencheur (PR, merge, nightly)
- `.husky/` : hooks pre-commit et pre-push
- `reports/` : sortie brute des rapports (ignorée par git, publiée en artefact CI)
- `docs/architecture/` : ce type de document, versionné et vivant

**Pitch** : séparer physiquement API/UI/unitaire permet des pipelines à vitesses différentes — un recruteur technique appréciera que la vitesse de feedback soit un critère de conception, pas un hasard.

---

## 4. Étape 1 — Qualité de code locale (pre-commit)

Avant qu'un seul test ne tourne en CI, la qualité est vérifiée localement via des hooks Git :

- **Pre-commit** : linter (ESLint avec règles Cypress/Testing Library dédiées), formatteur (Prettier), vérification des fichiers stagés uniquement (lint-staged) pour rester rapide.
- **Commit-msg** : validation du format de commit (Conventional Commits : `feat`, `fix`, `test`, `chore`...) — ce format sera réutilisé plus tard pour générer un changelog automatique et alimenter les métriques DORA.
- **Pre-push** : exécution des tests unitaires et d'un sous-ensemble de smoke tests critiques, pour éviter de polluer la CI avec des erreurs évidentes.

**Pitch** : le principe directeur est "*fail fast, fail local*". Chaque minute économisée en local est une minute de CI économisée, et c'est un argument fort en entretien : ça montre une conscience du coût réel (temps, argent, frustration des devs) d'une CI mal pensée.

---

## 5. Étape 2 — La pyramide de tests

### 5.1 Tests unitaires
Ciblent la logique pure : commandes Cypress custom, helpers, transformateurs de données, fixtures dynamiques. Exécutés à chaque commit, en quelques secondes, avec un seuil de couverture minimal comme quality gate (ex. 80%).

### 5.2 Tests API
Valident les contrats d'interface indépendamment de l'UI (statuts HTTP, schémas de réponse, temps de réponse, cas d'erreur). Exécutés en tout premier dans le pipeline car rapides et peu coûteux — s'ils échouent, inutile de lancer les tests UI qui dépendent des mêmes services.

### 5.3 Smoke tests
Sous-ensemble minimal et critique du parcours utilisateur (connexion, création d'une ressource clé, parcours d'achat...). Taggés `@smoke` dès la User Story. Objectif : moins de 5 minutes d'exécution, déclenchés sur **chaque Pull Request**.

### 5.4 Tests de non-régression
Suite complète couvrant l'ensemble des parcours et cas limites. Plus longue, exécutée sur merge vers la branche principale et en nightly build, avec parallélisation et exécution cross-navigateur.

### 5.5 Le lien BDD ↔ User Story
Chaque scénario Gherkin est directement traçable à sa User Story d'origine. Les step definitions Cypress implémentent ces scénarios sans dupliquer la logique métier déjà décrite. Cucumber devient ainsi le langage commun entre le rapport de test et le ticket produit.

**Pitch de la pyramide** : la stratégie n'est pas "tout tester partout tout le temps" mais "le bon niveau de test au bon moment du cycle de vie du code" — c'est l'argument qui différencie un SDET senior d'un testeur qui clique un bouton "Run all".

---

## 6. Étape 3 — Pipeline CI/CD (GitHub Actions & GitLab CI)

### 6.1 Stratégie de déclenchement
- **Sur Pull Request** : lint + tests unitaires + tests API + smoke tests UI → feedback en moins de 10 minutes.
- **Sur merge vers `main`** : suite de non-régression complète + tests API étendus + build de l'artefact de reporting.
- **Nightly / planifié** : suite complète cross-navigateur, tests de charge légers, audit de dépendances.
- **Manuel (workflow_dispatch)** : possibilité de relancer une suite ciblée par tag, utile en démo devant un recruteur.

### 6.2 Structure des jobs
Les jobs sont découpés pour maximiser le parallélisme : un job "qualité" (lint/format), un job "unitaire", un job "API", un job "UI smoke", un job "UI régression" sharded sur plusieurs runners. Chaque job publie ses résultats comme artefact CI indépendamment, pour que l'échec d'un job n'empêche pas la remontée des résultats des autres.

### 6.3 Isolation et environnements
Utilisation de conteneurs Docker pour garantir la reproductibilité (même image en local, en CI, et pour la démo). Gestion différenciée des environnements (dev/staging) via des fichiers de configuration Cypress dédiés et des secrets stockés dans le gestionnaire de secrets natif de la plateforme CI (jamais en clair dans le repo).

### 6.4 Quality gates
Le pipeline bloque la fusion si : couverture de tests unitaires sous le seuil, lint en échec, un smoke test critique rouge, ou un taux de flakiness anormal détecté sur les dernières exécutions. Ces règles sont configurées comme "required checks" sur la branche protégée.

**Pitch** : présenter le pipeline comme une **suite de portes de qualité progressives** plutôt qu'un bloc monolithique permet de raconter une histoire claire en entretien : "je sais dimensionner un pipeline pour qu'il donne du feedback vite sans sacrifier la rigueur sur le long terme."

---

## 7. Étape 4 — Reporting consolidé

### 7.1 Cucumber Reports
Génération d'un rapport HTML lisible par un profil non-technique (Product Owner), organisé par feature/scénario, avec captures d'écran attachées aux étapes en échec.

### 7.2 Cypress Cloud (cypress.io)
Centralisation des exécutions, replay vidéo des échecs, détection automatique de flakiness, analytics de tendance sur la durée d'exécution — sert de source de vérité technique pour l'équipe QA/Dev.

### 7.3 Power BI — le pont vers le reporting business
Les résultats structurés (issus des exports JSON/JUnit de Cucumber et Cypress) sont poussés vers un espace de stockage intermédiaire (ex. base de données ou fichier partagé), puis consommés par Power BI via un connecteur ou une actualisation planifiée. Le modèle sémantique expose des indicateurs comme : taux de succès par module, temps d'exécution moyen, taux de flakiness, nombre de régressions par sprint, corrélation entre User Story et taux d'échec.

**Pitch** : la présence de Power BI est ce qui distingue ce portfolio d'un simple projet Cypress — cela montre la capacité à parler à un public non-technique (management, product) avec des KPIs business, une compétence rare chez les SDET.

---

## 8. Étape 5 — Alerting intelligent et multicanal

Le principe directeur est le **routage par sévérité et par audience**, pas la diffusion en masse du même message partout :

- **Slack / Teams** : notifications techniques en temps réel dans les canaux d'équipe dev/QA à chaque échec de pipeline, avec lien direct vers le run et la vidéo de l'échec.
- **Discord** : canal dédié à la démo/portfolio, utile pour montrer en entretien un webhook custom avec embed formaté (statut, durée, lien).
- **Gmail** : rapport de synthèse quotidien ou hebdomadaire (digest), destiné à un public moins technique, avec le résumé Cucumber en pièce jointe.
- **Escalade conditionnelle** : un échec sur un smoke test critique déclenche une alerte immédiate et distincte d'un échec sur un test de régression secondaire — logique de priorisation intégrée au pipeline plutôt que laissée à l'humain.

**Pitch** : l'alerting n'est pas "brancher un webhook", c'est concevoir **qui a besoin de savoir quoi, sous quelle forme, à quelle fréquence** — c'est un raisonnement produit appliqué à un pipeline technique, encore un signal fort en entretien.

---

## 9. Observabilité et métriques

Au-delà du pass/fail, le pipeline doit exposer des métriques de pilotage :

- Taux de flakiness par test (pour identifier les tests à réécrire).
- Temps d'exécution moyen par suite (pour détecter la dérive de performance).
- Indicateurs DORA adaptés au test (fréquence de déploiement, temps moyen de détection d'une régression, temps moyen de résolution).
- Corrélation entre complexité de la User Story et taux d'échec des tests associés.

**Pitch** : mesurer la qualité du pipeline lui-même (et pas seulement la qualité du produit testé) est ce qui permet de dire en entretien "je sais faire évoluer un système de test dans le temps, pas seulement l'écrire une fois."

---

## 10. Sécurité et gouvernance

- Aucun secret en clair : utilisation exclusive des gestionnaires de secrets CI natifs.
- Scan automatique des dépendances (audit npm, Dependabot ou équivalent) intégré en pipeline hebdomadaire.
- Permissions minimales sur les tokens utilisés par les workflows (principe du moindre privilège).
- Séparation stricte entre les webhooks de démo (Discord) et les canaux de production (Slack/Teams) pour éviter toute fuite d'information réelle pendant une démonstration.

---

## 11. Roadmap — Vers l'agent IA (Phase 2)

Ce pipeline est conçu comme un socle sur lequel un agent IA viendra se greffer, avec des capacités progressives :

1. **Génération de scénarios** : lecture d'une User Story en langage naturel et génération automatique du fichier Gherkin correspondant.
2. **Génération de tests** : à partir du Gherkin, proposition automatique des step definitions Cypress (UI et API) à valider par le SDET.
3. **Auto-triage des échecs** : analyse automatique des logs/vidéos d'échec pour distinguer un vrai bug d'une régression liée à l'environnement (flakiness), avec résumé en langage naturel envoyé sur Slack/Teams.
4. **Auto-réparation des sélecteurs** : détection des sélecteurs UI cassés par un changement de DOM et proposition de correctif (self-healing tests).
5. **Rapport narratif automatique** : génération d'un résumé exécutif en langage naturel du run de test, injecté directement dans le mail de synthèse et le rapport Power BI.

**Pitch final pour l'entretien** : *"Ce que je montre aujourd'hui, c'est un pipeline CI/CD de test complet et industrialisé. Ce que je peux construire ensuite avec ce socle, c'est un agent qui ferme la boucle entre l'expression du besoin métier et la validation automatisée de sa réalisation — sans intervention humaine pour les tâches répétitives, avec l'humain gardé dans la boucle pour les décisions à enjeu."*
