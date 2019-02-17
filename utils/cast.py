import random
import math
import typing
import strings
import enum
s = strings.safely_format_string


class SpellType(enum.Flag):
    DAMAGING = enum.auto()
    HEALING = enum.auto()
    STATS = enum.auto()


class DamageComponent:
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

    def __init__(self):
        # ENSURE THE SEED IS ALREADY SET WHEN CREATING THIS COMPONENT!!!
        self.dice_number = random.randrange(1, 21)
        self.dice_type = random.sample(self.dice_type_distribution, 1)[0]
        self.constant = random.randrange(math.floor(-self.dice_type / 4), math.ceil(self.dice_type / 4) + 1)
        self.miss_chance = random.randrange(50, 101)
        self.repeat = random.sample(self.repeat_distribution, 1)[0]
        self.damage_types_qty = random.sample(self.damage_types_distribution, 1)[0]
        self.damage_types = random.sample(self.all_damage_types, self.damage_types_qty)

    def stringify(self) -> str:
        string = ""
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
        string += s(strings.SPELL.ACCURACY, words={"accuracy": str(self.miss_chance)})
        if self.repeat > 1:
            string += s(strings.SPELL.REPEAT, words={"repeat": str(self.repeat)})


class HealingComponent:
    dice_type_distribution = ([4] * 12) +\
                             ([6] * 38) +\
                             ([8] * 30) +\
                             ([10] * 12) +\
                             ([12] * 6) +\
                             ([20] * 1) +\
                             ([100] * 1)

    def __init__(self):
        # ENSURE THE SEED IS ALREADY SET WHEN CREATING THIS COMPONENT!!!
        self.dice_number = random.randrange(1, 21)
        self.dice_type = random.sample(self.dice_type_distribution, 1)[0]
        self.constant = random.randrange(math.floor(-self.dice_type / 4), math.ceil(self.dice_type / 4) + 1)

    def stringify(self) -> str:
        string = ""
        if self.constant > 0:
            constant = "+" + str(self.constant)
        elif self.constant == 0:
            constant = ""
        else:
            constant = str(self.constant)
        string += s(strings.SPELL.HEALING,
                    words={"number": str(self.dice_number),
                           "type": str(self.dice_type),
                           "constant": constant})
        return string


class StatsComponent:
    all_stats = ["Attacco", "Difesa", "Velocità", "Elusione", "Tenacia", "Rubavita",
                 "Vampirismo", "Forza", "Destrezza", "Costituzione", "Intelligenza",
                 "Saggezza", "Carisma", "Attacco Speciale", "Difesa Speciale",
                 "Eccellenza", "Immaginazione", "Cromosomi", "Timidezza", "Sonno",
                 "Elasticità", "Peso", "Sanità", "Appetito", "Fortuna", "Percezione",
                 "Determinazione"]

    change_distribution = (["--"] * 1) +\
                          (["-"] * 3) +\
                          (["+"] * 3) +\
                          (["++"] * 1)
    
    multistat_distribution = ([1] * 7) +\
                             ([2] * 6) +\
                             ([3] * 4) +\
                             ([5] * 2) +\
                             ([8] * 1)

    def __init__(self):
        # ENSURE THE SEED IS ALREADY SET WHEN CREATING THIS COMPONENT!!!
        self.stat_changes = {}
        self.stat_number = random.sample(self.multistat_distribution, 1)[0]
        available_stats = self.all_stats.copy()
        for _ in range(self.stat_number):
            stat = random.sample(available_stats, 1)[0]
            available_stats.remove(stat)
            change = random.sample(self.change_distribution, 1)[0]
            self.stat_changes[stat] = change
    
    def stringify(self) -> str:
        string = ""
        for name in self.stat_changes:
            string += s(strings.SPELL.STAT, words={
                "name": name, 
                "change": self.stat_changes
            })
        return string


class Spell:
    version = "3.1"

    damaging_spell_chance = 0.8
    healing_spell_chance = 0.8  # If not a damaging spell
    additional_stats_chance = 0.2  # In addition to the damage/healing

    def __init__(self, name: str):
        seed = name.capitalize()
        random.seed(seed)
        # Spell name
        self.name = seed
        # Find the spell type
        self.spell_type = None
        if random.random() < self.damaging_spell_chance:
            self.spell_type = SpellType.DAMAGING
        elif random.random() < self.healing_spell_chance:
            self.spell_type = SpellType.HEALING
        if random.random() < self.additional_stats_chance:
            if self.spell_type is None:
                self.spell_type = SpellType.STATS
            else:
                self.spell_type |= SpellType.STATS
        # Damaging spells
        if self.spell_type & SpellType.DAMAGING:
            self.damage_component = DamageComponent()
        else:
            self.damage_component = None
        # Healing spells
        if self.spell_type & SpellType.HEALING:
            self.healing_component = HealingComponent()
        else:
            self.healing_component = None
        # Status spells
        if self.spell_type & SpellType.STATS:
            self.stats_component = StatsComponent()
        else:
            self.stats_component = None


    def stringify(self) -> str:
        string = s(strings.SPELL.HEADER, words={"name": self.name, "version": self.version})
        if self.spell_type & SpellType.DAMAGING:
            string += self.damage_component.stringify()
        if self.spell_type & SpellType.HEALING:
            string += self.healing_component.stringify()
        if self.spell_type & SpellType.STATS:
            string += self.stats_component.stringify()
        if self.spell_type = None
            string += s(strings.SPELL.NOTHING)
        return string
