import random
import math
import db


def cast(spell_name: str, target_name: str, platform: str) -> str:
    spell = spell_name.capitalize()
    # Seed the rng with the spell name
    # so that spells always deal the same damage
    random.seed(spell)
    dmg_dice = random.randrange(1, 11)
    dmg_max = random.sample([4, 6, 8, 10, 12, 20, 100], 1)[0]
    dmg_mod = random.randrange(math.floor(-dmg_max / 5), math.ceil(dmg_max / 5) + 1)
    dmg_type = random.sample(["da fuoco", "da freddo", "elettrici", "sonici", "necrotici", "magici",
                              "da acido", "divini", "nucleari", "psichici", "fisici", "puri", "da taglio",
                              "da perforazione", "da impatto", "da caduta", "gelato", "onnipotenti", "oscuri",
                              "di luce", "da velocità", "da cactus", "meta", "dannosi", "da radiazione",
                              "tuamammici", "da maledizione", "pesanti", "leggeri", "immaginari", "da laser",
                              "da neutrini", "galattici", "cerebrali", "ritardati", "ritardanti"], 1)[0]
    # Reseed the rng with a random value
    # so that the dice roll always deals a different damage
    random.seed()
    total = dmg_mod
    # Check for a critical hit
    crit = 1
    while True:
        crit_die = random.randrange(1, 21)
        if crit_die == 20:
            crit *= 2
        else:
            break
    for dice in range(0, dmg_dice):
        total += random.randrange(1, dmg_max + 1)
    if crit > 1:
        if platform == "telegram":
            crit_msg = f"<b>CRITICO ×{crit}{'!' * crit}</b>\n"
        elif platform == "discord":
            crit_msg = f"**CRITICO ×{crit}{'!' * crit}**\n"
        total *= crit
    else:
        crit_msg = ""
    # HALLOWEEN
    if total >= 800:
        return f"❇️ Ho lanciato <b>{spell}</b> su " \
               f"<i>{target_name}</i>.\n" \
               f"{crit_msg}" \
               f"...ma non succede nulla."
    # END
    if platform == "telegram":
        if dmg_dice == 10 and dmg_max == 100 and dmg_mod == 20:
            return f"❇️‼️ Ho lanciato <b>{spell}</b> su " \
                   f"<i>{target_name}</i>.\n" \
                   f"Una grande luce illumina il cielo, seguita poco dopo da un fungo di fumo nel luogo" \
                   f" in cui si trovava <i>{target_name}</i>.\n" \
                   f"Il fungo si espande a velocità smodata, finchè il fumo non ricopre la Terra intera e le tenebre" \
                   f" cadono su di essa.\n" \
                   f"Dopo qualche minuto, la temperatura ambiente raggiunge gli 0 °C, e continua a diminuire.\n" \
                   f"L'Apocalisse Nucleare è giunta, e tutto per polverizzare <i>{target_name}</i>" \
                   f" con <b>{spell}</b>.\n" \
                   f"<i>{target_name}</i> subisce 10d100+20=<b>9999</b> danni apocalittici!"
        return f"❇️ Ho lanciato <b>{spell}</b> su " \
               f"<i>{target_name}</i>.\n" \
               f"{crit_msg}" \
               f"<i>{target_name}</i> subisce {dmg_dice}d{dmg_max}" \
               f"{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}" \
               f"{'×' + str(crit) if crit > 1 else ''}" \
               f"=<b>{total if total > 0 else 0}</b> danni {dmg_type}!"
    elif platform == "discord":
        if dmg_dice == 10 and dmg_max == 100 and dmg_mod == 20:
            return f"❇️‼️ Ho lanciato **{spell}** su " \
                   f"_{target_name}_.\n" \
                   f"Una grande luce illumina il cielo, seguita poco dopo da un fungo di fumo nel luogo" \
                   f" in cui si trovava _{target_name}_.\n" \
                   f"Il fungo si espande a velocità smodata, finchè il fumo non ricopre la Terra intera e le tenebre" \
                   f" cadono su di essa.\n" \
                   f"Dopo qualche minuto, la temperatura ambiente raggiunge gli 0 °C, e continua a diminuire.\n" \
                   f"L'Apocalisse Nucleare è giunta, e tutto per polverizzare _{target_name}_" \
                   f" con **{spell}**.\n" \
                   f"_{target_name}_ subisce 10d100+20=**9999** danni apocalittici!"
        return f"❇️ Ho lanciato **{spell}** su " \
               f"_{target_name}_.\n" \
               f"{crit_msg}" \
               f"_{target_name}_ subisce {dmg_dice}d{dmg_max}" \
               f"{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}" \
               f"{'×' + str(crit) if crit > 1 else ''}" \
               f"=**{total if total > 0 else 0}** danni {dmg_type}!"
