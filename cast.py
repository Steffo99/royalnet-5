import random
import math


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
    if platform == "telegram":
        return f"❇️ Ho lanciato <b>{spell}</b> su " \
               f"<i>{target_name}</i>.\n" \
               f"{crit_msg}" \
               f"<i>{target_name}</i> subisce {dmg_dice}d{dmg_max}" \
               f"{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}" \
               f"{'×' + str(crit) if crit > 1 else ''}" \
               f"=<b>{total if total > 0 else 0}</b> danni {dmg_type}!"
    elif platform == "discord":
        return f"❇️ Ho lanciato **{spell}** su " \
               f"_{target_name}_.\n" \
               f"{crit_msg}" \
               f"_{target_name}_ subisce {dmg_dice}d{dmg_max}" \
               f"{'+' if dmg_mod > 0 else ''}{str(dmg_mod) if dmg_mod != 0 else ''}" \
               f"{'×' + str(crit) if crit > 1 else ''}" \
               f"=**{total if total > 0 else 0}** danni {dmg_type}!"