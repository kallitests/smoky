Voici le workflow type, du ticket Jira/Xray jusqu'au reporting, adapté au contexte de l'offre (60% auto / 40% manuel, web + mobile), avec la couche **agent IA (type Smoky)** intégrée et **Cypress** comme seul outil d'automatisation (Playwright retiré) :

```
═══════════════════════════════════════════════════════════════════
 WORKFLOW QA — DU TICKET JIRA/XRAY AU REPORTING (AGENT IA + CYPRESS)
═══════════════════════════════════════════════════════════════════

[1] EXPRESSION DU BESOIN
    └─ User Story créée dans Jira (Product Owner)
       └─ Critères d'acceptation rédigés en Gherkin (Given/When/Then)
          — c'est ce Gherkin qui sert de contrat entre PO/Dev/QA et de
          source de vérité pour l'agent IA à l'étape [3B]

[2] TICKET DE TEST — JIRA + XRAY
    └─ Xray génère un "Test" lié à la Story (traçabilité Story <-> Test)
       ├─ Type = Manual    → cas de test rédigé dans Xray (steps, expected)
       └─ Type = Automated → Test Repository Xray, lié au spec Cypress
    └─ Décision Auto vs Manuel (règle 60/40) :
       ├─ Critique / répétitif / smoke / régression → AUTOMATISÉ (Cypress)
       └─ Exploratoire / UX / edge-case rare         → MANUEL

═══════════════════════════════════════════════════════════════════
 BRANCHE A — TEST MANUEL (40%)
═══════════════════════════════════════════════════════════════════
[3A] Exécution manuelle
     └─ Testeur exécute le Test Xray (Web ou Mobile)
        └─ Résultat saisi dans Xray (Pass/Fail/Blocked)
           └─ Si Fail → Bug créé dans Jira, lié au Test (Xray Defects)
              └─ Retour Dev → Re-test manuel après correctif

═══════════════════════════════════════════════════════════════════
 BRANCHE B — TEST AUTOMATISÉ, GÉNÉRÉ PAR L'AGENT IA (60%)
═══════════════════════════════════════════════════════════════════
[3B-1] Détection du ticket par l'agent IA
       └─ Label "smoky-ready" sur le ticket Jira, ou statut dédié
          └─ Polling Jira (toutes les 5 min) ou webhook temps réel

[3B-2] Génération du scénario Cypress par l'agent IA (Claude)
       └─ Lecture de la User Story + du Gherkin de l'étape [1]
          ├─ Génération directe d'un spec Cypress (.cy.ts) — happy path
          │  + au moins un unhappy path (erreur, edge case)
          ├─ Grounding dans le vrai code de l'appli cible (sélecteurs
          │  data-test, routes réelles — rien n'est inventé ; si une
          │  info manque, commentaire // SMOKY_UNCERTAIN)
          ├─ Tests API en Cypress (request context), séparés de l'UI
          │  pour exécution indépendante et plus rapide
          └─ Réutilisation de commandes custom / fixtures existantes

[3B-3] Auto-validation de l'agent (avant tout déclenchement CI)
       └─ Claude note son propre output sur 4 axes (score /10) :
          cohérence avec la Story, absence d'hallucination, couverture
          (happy + unhappy path), format Cypress valide
          ├─ Score ≥ 6 → le pipeline CI est déclenché
          └─ Score < 6 → pipeline bloqué, demande de clarification
             postée en commentaire Jira + alerte Slack

[4] VERSIONNING
     └─ Commit du spec Cypress généré (branche dédiée agent) + PR
        automatique → Code Review humaine avant merge (pairing avec
        l'équipe) — l'humain reste dans la boucle pour la décision,
        pas pour l'écriture du script

[5] CI/CD — DÉCLENCHEMENT
     └─ Push / PR merge → Pipeline CI (GitLab CI / GitHub Actions),
        conteneurs Docker multi-stage, exécution en non-root
        ├─ Stage 1 : Lint / Build
        ├─ Stage 2 : Unit tests (si applicable côté app)
        ├─ Stage 3 : Tests API Cypress
        ├─ Stage 4 : Smoke tests Cypress (Web + Web mobile) — objectif
        │  < 5 minutes, bloquant, verdict de confiance rapide
        └─ Stage 5 : Suite de Régression Cypress — complète, planifiée
           (nightly / avant release) — c'est la couche suivante à
           construire au-dessus du périmètre smoke de l'agent IA,
           pas un livrable de l'agent lui-même

[6] EXÉCUTION DES TESTS (Cypress)
     └─ Exécution parallèle (sharding) sur navigateurs
        (Chromium/WebKit/Firefox) et web mobile responsive (viewport
        émulé) — pour du natif mobile, Cypress ne suffit pas : prévoir
        un outil complémentaire (Appium) en dehors du périmètre agent
        └─ Captures : screenshots, vidéos Cypress en cas d'échec

═══════════════════════════════════════════════════════════════════
 REPORTING & ALERTING
═══════════════════════════════════════════════════════════════════
[7] REPORTING AUTOMATISÉ
     └─ Génération rapport (Cypress mochawesome HTML report / JSON)
        ├─ Publication résultats → Xray (mise à jour statut Test
        │  Execution) via Xray API/CLI, import JUnit/JSON
        ├─ Publication → Power BI (flakiness historisé dans Redis —
        │  dernières 20 exécutions par test)
        └─ Historique de tendance (taux de succès, flakiness, durée)

[8] ALERTING — ROUTAGE PAR SÉVÉRITÉ ET PAR AUDIENCE
     └─ Si échec Stage 4 (Smoke) → alerte immédiate, routée et non
        diffusée à l'identique partout
        ├─ Slack (canal QA/Dev, temps réel, canal principal)
        ├─ Teams / Discord (optionnel, échecs @critical uniquement)
        ├─ Gmail (digest quotidien/hebdomadaire groupé, non-bloquant,
        │  audience moins technique)
        └─ Sévérité :
           ├─ Bloquant     → alerte immédiate + Bug Jira auto-créé
           │  (lié au Test Xray)
           └─ Non-bloquant → ticket créé, priorisé au triage, inclus
              dans le digest groupé

[9] TRIAGE & RETOUR BOUCLE
     └─ Revue quotidienne/sprint des échecs (Dev + QA)
        ├─ Bug confirmé          → correctif → nouveau run CI → validation
        ├─ Faux positif / flaky  → maintenance du spec Cypress,
        │  historique de flakiness consulté dans Redis (retour à [3B-2])
        └─ Score d'auto-validation faible récurrent ou dérive détectée
           → révision du prompt système de l'agent (retour à [10])

[10] AUTO-ÉVALUATION CONTINUE DE L'AGENT IA (CE QUE SMOKY TESTE SUR
     LUI-MÊME — la question posée en filigrane : peut-on faire
     confiance à une IA pour tester notre logiciel, et comment le
     prouver ?)
     └─ DeepEval  → note chaque spec généré vs la Story source
        (pertinence, fidélité, complétude)
     └─ RAGAS     → mesure la fidélité spec / critères d'acceptation
     └─ Promptfoo → non-régression entre versions de prompt, benchmarké
        sur un jeu de tickets de référence avant tout merge de prompt
     └─ Gate qualité en CI : un run est bloqué si le score
        DeepEval/RAGAS descend sous le seuil, comme un test unitaire
        qui échoue bloque un déploiement

═══════════════════════════════════════════════════════════════════
 CYCLE DE VIE GLOBAL (SPRINT DE 2 SEMAINES)
═══════════════════════════════════════════════════════════════════
 Sprint N :
   J1-J3   : Nouvelles Stories → cas de test Xray (auto/manuel) rédigés
   Continu : Agent IA génère et auto-valide les specs Cypress smoke à
             chaque ticket taggé "smoky-ready" (pas seulement en
             milieu de sprint — dès que le ticket est prêt)
   J3-J8   : Dev + revue humaine des specs générés, écriture manuelle
             des cas hors périmètre smoke (régression, exploratoire)
   J8-J10  : Exécution manuelle des cas non automatisables
   Continu : CI/CD Cypress à chaque commit (Smoke, < 5 min) + nightly
             (Régression complète) + auto-évaluation continue de l'IA
   Fin sprint : Rapport consolidé (Auto + Manuel) → Revue Xray →
                Démo/Review
   Rétro    : Ajustement ratio auto/manuel, dette de test, flakiness
              à traiter, dérive de qualité des specs générés par l'IA
═══════════════════════════════════════════════════════════════════
```

**Points clés pour le POC** :
- Le lien **Xray ↔ Cypress** se fait via l'**Xray API/CLI** (import des résultats JUnit/JSON générés par Cypress/mochawesome).
- Prévoir la **gestion du flaky test** dès le POC (retry policy, quarantaine, historique dans Redis) — c'est souvent ce qui décrédibilise un pipeline sinon.
- Pour le mobile, Cypress ne couvre que le **web mobile responsive** ; pour du natif, il faudra un outil complémentaire (Appium) en dehors du périmètre de l'agent — bon point à creuser en entretien.
- La couche IA (génération + auto-validation + auto-évaluation continue) est volontairement scoping **smoke tests uniquement** — happy path + unhappy path sur les parcours critiques, verdict en moins de 5 minutes. La suite de régression complète reste construite et maintenue par l'équipe, pas générée par l'agent : c'est la couche suivante, pas un livrable de ce périmètre.
- Le pipeline Cypress est dockerisé, multi-stage, et s'exécute en non-root — cohérent avec une architecture CI/CD "produit interne" plutôt qu'un simple script.