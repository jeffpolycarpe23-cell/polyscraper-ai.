        # On demande à l'IA un formatage spécifique
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur de données. Réponds TOUJOURS en utilisant le format Markdown. Mets le NOM en titre (###), le PRIX en gras et utilise une liste à puces pour les CARACTÉRISTIQUES."},
                {"role": "user", "content": f"Extrais proprement les infos de ce site : {contexte}"}
            ]
        )
