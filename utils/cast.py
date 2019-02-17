import random
import math
import typing
import strings
s = strings.safely_format_string


class Spell:
    version = "3.0"

    dice_type_distribution = ([4] * 1) +\
                             ([6] * 6) +\
                             ([8] * 24) +\
                             ([10] * 38) +\
                             ([12] * 24) +\
                             ([20] * 6) +\
                             ([100] * 1)

    all_damage_types = ["da fuoco", "da freddo", "elettrici", "sonici", "necrotici", "magici",
                        "da acido", "divini", "nucleari", "psichici", "fisici", "puri", "da taglio",
                        "da perforazione", "da impatto", "da caduta", "gelato", "onnipotenti", "oscuri",
                        "di luce", "da velocità", "da cactus", "meta", "dannosi", "da radiazione",
                        "tuamammici", "da maledizione", "pesanti", "leggeri", "immaginari", "da laser",
                        "da neutrini", "galattici", "cerebrali", "ritardati", "ritardanti", "morali", "materiali",
                        "energetici", "esplosivi"]

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
        self.miss_chance = random.randrange(80, 101)
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


class Hit:
    def __init__(self, spell: Spell):
        random.seed()
        self.hit_roll = random.randrange(0, 101)
        self.damage = 0
        self.crit_multiplier = 1
        self.damage_type = random.sample(spell.damage_types, 1)[0]
        if self.hit_roll > spell.miss_chance:
            return
        for _ in range(spell.dice_number):
            self.damage += random.randrange(1, spell.dice_type + 1)
        self.damage += spell.constant
        if self.damage < 0:
            self.damage = 0
        while random.randrange(1, 21) == 20:
            self.crit_multiplier *= 2

    @property
    def total_damage(self):
        return self.damage * self.crit_multiplier

class Cast:
    def __init__(self, spell: Spell):
        self.hits = []
        for _ in spell.repeat:
            self.hits.append(Hit(spell))

