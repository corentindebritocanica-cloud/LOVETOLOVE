import json
import random # Utilisé ici pour simuler les requêtes API

# --- 1. FONCTIONS DE COLLECTE DE DONNÉES (À relier à tes API) ---

def get_cotes_bookmakers(equipe_domicile, equipe_exterieur):
    # Simule une requête à une API de bookmakers (ex: The Odds API)
    # Plus la cote est proche de 1, plus la victoire est sûre.
    # Ici, on retourne une probabilité convertie (ex: cote de 1.20 = ~83% de probabilité)
    return {"prob_domicile": 85, "prob_exterieur": 15, "prob_nul": 10}

def get_historique_confrontations(equipe_domicile, equipe_exterieur):
    # Simule une requête pour l'historique (H2H - Head to Head)
    # Retourne le pourcentage de victoire de l'équipe domicile sur les 10 derniers matchs
    return {"taux_victoire_domicile": 80, "taux_victoire_exterieur": 10, "taux_nul": 10}

def get_actualites_et_absences(equipe):
    # Simule l'analyse des effectifs (blessures, cartons, forme de l'équipe)
    # Retourne un malus si des joueurs phares sont absents (ex: Mbappé absent = -20)
    absences_majeures = False # À remplacer par la vraie logique API
    
    impact_absence = 0
    if absences_majeures:
        impact_absence = -25 # Grosse perte de confiance si un joueur clé manque
    
    dynamique_equipe = random.randint(-5, 10) # Bonus/Malus lié à la forme du moment
    
    return dynamique_equipe + impact_absence

# --- 2. MOTEUR DE CALCUL DU SCORE DE CONFIANCE ---

def calculer_confiance_match(match):
    domicile = match["equipe_domicile"]
    exterieur = match["equipe_exterieur"]
    
    # Récupération des 3 piliers de données
    bookmakers = get_cotes_bookmakers(domicile, exterieur)
    historique = get_historique_confrontations(domicile, exterieur)
    actu_domicile = get_actualites_et_absences(domicile)
    actu_exterieur = get_actualites_et_absences(exterieur)
    
    # Pondération (Tu peux ajuster ces pourcentages selon ce que tu juges le plus fiable)
    poids_bookmakers = 0.50 # 50% de la décision vient des bookmakers
    poids_historique = 0.30 # 30% vient de l'historique
    poids_actu = 0.20       # 20% vient de l'actualité/forme
    
    # Calcul de base pour l'équipe favorite (ici on prend le domicile pour l'exemple)
    score_base = (bookmakers["prob_domicile"] * poids_bookmakers) + \
                 (historique["taux_victoire_domicile"] * poids_historique)
                 
    # Application des bonus/malus d'actualité
    score_final = score_base + (actu_domicile * poids_actu) - (actu_exterieur * poids_actu)
    
    # Plafonner à 100%
    score_final = min(100, max(0, score_final))
    
    # Déterminer si le match est "CHAAAUUD" (ex: Confiance > 85%)
    est_chaud = True if score_final >= 85 else False
    
    return round(score_final, 2), est_chaud

# --- 3. GÉNÉRATION DES DONNÉES ---

def generer_predictions():
    # Liste des matchs à analyser (à remplacer par ton calendrier de Coupe du Monde par exemple)
    calendrier = [
        {"equipe_domicile": "Portugal", "equipe_exterieur": "Corée du Sud", "competition": "Coupe du Monde"},
        {"equipe_domicile": "France", "equipe_exterieur": "Australie", "competition": "Coupe du Monde"},
        {"equipe_domicile": "Mexique", "equipe_exterieur": "Pologne", "competition": "Coupe du Monde"}
    ]
    
    resultats = []
    
    for match in calendrier:
        score, chaud = calculer_confiance_match(match)
        
        # On détermine le gagnant théorique pour l'affichage
        pronostic = match["equipe_domicile"] if score > 50 else match["equipe_exterieur"]
        
        resultats.append({
            "match": f"{match['equipe_domicile']} vs {match['equipe_exterieur']}",
            "pronostic": f"Victoire {pronostic}",
            "score_confiance": score,
            "est_chaud": chaud
        })
        
    # Sauvegarde dans le fichier JSON
    with open('data/predictions.json', 'w', encoding='utf-8') as f:
        json.dump(resultats, f, ensure_ascii=False, indent=4)
        
    print("Prédictions générées avec succès dans data/predictions.json !")

if __name__ == "__main__":
    generer_predictions()
