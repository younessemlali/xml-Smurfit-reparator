# XML Smurfit Reparator

Application **Streamlit** pour corriger automatiquement des fichiers XML utilisés dans le périmètre **Smurfit Kappa**.

## 🎯 Objectif

Dans chaque bloc XML, la balise `<Description>` contient une valeur entre guillemets telle que `"A - Peu Qualifié"`.  
Cette application :
1. Détecte automatiquement la valeur entre guillemets
2. Crée ou met à jour la balise `<PositionLevel>` avec cette valeur
3. Propose le fichier corrigé en téléchargement
4. Fournit un **monitoring en temps réel** (logs, statistiques, graphiques)

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## 🚀 Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/younessemlali/xml-Smurfit-reparator.git
cd xml-Smurfit-reparator
```

### 2. Créer un environnement virtuel (recommandé)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Utilisation

### Lancer l'application
```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut à l'adresse `http://localhost:8501`.

### Étapes d'utilisation

1. **Charger les fichiers** : Cliquez sur "Browse files" et sélectionnez un ou plusieurs fichiers XML
2. **Lancer le traitement** : Cliquez sur le bouton "🚀 Lancer le traitement"
3. **Consulter les résultats** : 
   - Tableau de monitoring avec le statut de chaque fichier
   - Graphique des balises ajoutées
   - Statistiques de traitement
4. **Télécharger** :
   - Les fichiers XML corrigés (format ZIP)
   - Les logs de traitement (format CSV)

## 📁 Structure du projet

```
xml-Smurfit-reparator/
│
├── app.py                 # Application Streamlit principale
├── xml_processor.py       # Module de traitement XML
├── requirements.txt       # Dépendances Python
├── README.md             # Documentation
└── .gitignore           # Fichiers à ignorer par Git
```

## 🔧 Exemple de transformation

### Avant :
```xml
<Job>
    <Description>Poste de niveau "A - Peu Qualifié"</Description>
    <Salary>25000</Salary>
</Job>
```

### Après :
```xml
<Job>
    <Description>Poste de niveau "A - Peu Qualifié"</Description>
    <Salary>25000</Salary>
    <PositionLevel>A - Peu Qualifié</PositionLevel>
</Job>
```

## 📊 Fonctionnalités

- ✅ **Traitement par lot** : Traitez plusieurs fichiers XML simultanément
- ✅ **Monitoring en temps réel** : Suivez la progression et les résultats
- ✅ **Gestion des erreurs** : Les fichiers avec erreurs sont identifiés et isolés
- ✅ **Export des résultats** : Téléchargez les fichiers corrigés et les logs
- ✅ **Interface intuitive** : Interface web simple et moderne
- ✅ **Sécurité XML** : Protection contre les attaques XXE avec defusedxml

## 🐛 Dépannage

### L'application ne démarre pas
- Vérifiez que Python 3.8+ est installé : `python --version`
- Assurez-vous que toutes les dépendances sont installées : `pip install -r requirements.txt`
- Vérifiez que le port 8501 n'est pas déjà utilisé

### Erreur lors du traitement XML
- Vérifiez que vos fichiers sont bien au format XML valide
- Assurez-vous que les balises `<Description>` contiennent bien du texte entre guillemets
- Consultez les logs pour plus de détails sur l'erreur

### Performance lente
- Pour de gros volumes de fichiers, traitez-les par lots de 50-100 fichiers
- Fermez les autres applications gourmandes en ressources

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout de fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👤 Auteur

**Younes Semlali**
- GitHub: [@younessemlali](https://github.com/younessemlali)

## 🙏 Remerciements

- Équipe Smurfit Kappa pour les spécifications
- Communauté Streamlit pour l'excellent framework
- Contributeurs open source des bibliothèques utilisées
