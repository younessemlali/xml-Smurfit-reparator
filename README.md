# XML Smurfit Reparator

Application **Streamlit** pour corriger automatiquement des fichiers XML utilisés dans le périmètre **Smurfit Kappa**.

## 🎯 Objectif
Dans chaque bloc XML, la balise `<Description>` contient une valeur entre guillemets telle que `"A - Peu Qualifié"`.  
Cette application :
1. Détecte automatiquement la valeur entre guillemets.
2. Crée ou met à jour la balise `<PositionLevel>` avec cette valeur.
3. Propose le fichier corrigé en téléchargement.
4. Fournit un **monitoring en temps réel** (logs, statistiques, graphiques).

---

## 🚀 Démarrage rapide

### 1. Cloner le dépôt
```bash
git clone https://github.com/younessemlali/xml-Smurfit-reparator.git
cd xml-Smurfit-reparator
