import random
import math
import typing
import strings
s = strings.safely_format_string


class Spell:
    version = "3.1"

    dice_type_distribution = ([4] * 7) +\
                             ([6] * 12) +\
                             ([8] * 32) +\
                             ([10] * 30) +\
                             ([12] * 12) +\
                             ([20] * 6) +\
                             ([100] * 1)

    all_damage_types = ["da fuoco", "da freddo", "elettrici", "sonici", "necrotici", "magici",
                        "da acido", "divini", "nucleari", "psichici", "fisici", "puri", "da taglio",
                        "da perforazione", "da impatto", "da caduta", "gelato", "onnipotenti", "oscuri",
                        "di luce", "da velocità", "da cactus", "dannosi", "da radiazione",
                        "tuamammici", "da maledizione", "pesanti", "leggeri", "immaginari", "da laser",
                        "da neutrini", "galattici", "cerebrali", "ritardati", "ritardanti", "morali", "materiali",
                        "energetici", "esplosivi", "energetici", "finanziari", "radianti", "sonori", "spaggiaritici",
                        "interiori", "endocrini", "invisibili", "inesistenti", "eccellenti", "bosonici",
                        "gellificanti", "terminali"]

    repeat_distribution = ([1] * 8) +\
                          ([2] * 1) +\
                          ([3] * 1)

    damage_types_distribution = ([1] * 6) + \
                                ([2] * 3) + \
                                ([3] * 1)

    def __init__(self, name: str):
        seed = name.capitalize()
        random.seed(seed)
        # Spell data
        self.name = seed
        self.dice_number = random.randrange(1, 21)
        self.dice_type = random.sample(self.dice_type_distribution, 1)[0]
        self.constant = random.randrange(math.floor(-self.dice_type / 4), math.ceil(self.dice_type / 4) + 1)
        self.miss_chance = random.randrange(50, 101)
        self.repeat = random.sample(self.repeat_distribution, 1)[0]
        self.damage_types_qty = random.sample(self.damage_types_distribution, 1)[0]
        self.damage_types = random.sample(self.all_damage_types, self.damage_types_qty)

    def stringify(self) -> str:
        string = s(strings.SPELL.HEADER, words={"name": self.name, "version": self.version})
        string += s(strings.SPELL.ACCURACY, words={"accuracy": str(self.miss_chance)})
        if self.constant > 0:
            constant = "+" + str(self.constant)
        elif self.constant == 0:
            constant = ""
        else:
            constant = str(self.constant)
        string += s(strings.SPELL.DAMAGE,
                    words={"number": str(self.dice_number),
                           "type": str(self.dice_type),
                           "constant": constant})
        for dmg_type in self.damage_types:
            string += s(strings.SPELL.TYPE, words={"type": dmg_type})
        if self.repeat > 1:
            string += s(strings.SPELL.REPEAT, words={"repeat": str(self.repeat)})
        return string
