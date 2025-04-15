def calcul_frais_entretien(montant):
    if 10000 <= montant <= 100000:
        return 3500
    elif 101000 <= montant <= 500000:
        return 15500
    return 0

def calcul_duree_remboursement(montant):
    if montant <= 50000:
        return 60
    elif montant >= 200000:
        return 250
    return 90