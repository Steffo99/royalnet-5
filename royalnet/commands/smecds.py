import random
from ..utils import Command, Call, safeformat


DS_LIST = ["della secca", "del seccatore", "del secchiello", "del secchio", "del secchione", "del secondino",
           "del sedano", "del sedativo", "della sedia", "del sedicente", "del sedile", "della sega", "del segale",
           "della segatura", "della seggiola", "del seggiolino", "della seggiovia", "della segheria", "del seghetto",
           "del segnalibro", "del segnaposto", "del segno", "del segretario", "della segreteria", "del seguace",
           "del segugio", "della selce", "della sella", "della selz", "della selva", "della selvaggina", "del semaforo",
           "del seme", "del semifreddo", "del seminario", "della seminarista", "della semola", "del semolino",
           "del semplicione", "della senape", "del senatore", "del seno", "del sensore", "della sentenza",
           "della sentinella", "del sentore", "della seppia", "del sequestratore", "della serenata", "del sergente",
           "del sermone", "della serpe", "del serpente", "della serpentina", "della serra", "del serraglio",
           "del serramanico", "della serranda", "della serratura", "del servitore", "della servitù", "del servizievole",
           "del servo", "del set", "della seta", "della setola", "del sidecar", "del siderurgico", "del sidro",
           "della siepe", "del sifone", "della sigaretta", "del sigaro", "del sigillo", "della signora",
           "della signorina", "del silenziatore", "della silhouette", "del silicio", "del silicone", "del siluro",
           "della sinagoga", "della sindacalista", "del sindacato", "del sindaco", "della sindrome", "della sinfonia",
           "del sipario", "del sire", "della sirena", "della siringa", "del sismografo", "del sobborgo",
           "del sobillatore", "del sobrio", "del soccorritore", "del socio", "del sociologo", "della soda", "del sofà",
           "della soffitta", "del software", "dello sogghignare", "del soggiorno", "della sogliola", "del sognatore",
           "della soia", "del solaio", "del solco", "del soldato", "del soldo", "del sole", "della soletta",
           "della solista", "del solitario", "del sollazzare", "del sollazzo", "del sollecito", "del solleone",
           "del solletico", "del sollevare", "del sollievo", "del solstizio", "del solubile", "del solvente",
           "della soluzione", "del somaro", "del sombrero", "del sommergibile", "del sommo", "della sommossa",
           "del sommozzatore", "del sonar", "della sonda", "del sondaggio", "del sondare", "del sonnacchioso",
           "del sonnambulo", "del sonnellino", "del sonnifero", "del sonno", "della sonnolenza", "del sontuoso",
           "del soppalco", "del soprabito", "del sopracciglio", "del sopraffare", "del sopraffino", "del sopraluogo",
           "del sopramobile", "del soprannome", "del soprano", "del soprappensiero", "del soprassalto",
           "del soprassedere", "del sopravvento", "del sopravvivere", "del soqquadro", "del sorbetto", "del sordido",
           "della sordina", "del sordo", "della sorella", "della sorgente", "del sornione", "del sorpasso",
           "della sorpresa", "del sorreggere", "del sorridere", "della sorsata", "del sorteggio", "del sortilegio",
           "del sorvegliante", "del sorvolare", "del sosia", "del sospettoso", "del sospirare", "della sosta",
           "della sostanza", "del sostegno", "del sostenitore", "del sostituto", "del sottaceto", "della sottana",
           "del sotterfugio", "del sotterraneo", "del sottile", "del sottilizzare", "del sottintendere",
           "del sottobanco", "del sottobosco", "del sottomarino", "del sottopassaggio", "del sottoposto",
           "del sottoscala", "della sottoscrizione", "del sottostare", "del sottosuolo", "del sottotetto",
           "del sottotitolo", "del sottovalutare", "del sottovaso", "della sottoveste", "del sottovuoto",
           "del sottufficiale", "della soubrette", "del souvenir", "del soverchiare", "del sovrano", "del sovrapprezzo",
           "della sovvenzione", "del sovversivo", "del sozzo", "dello suadente", "del sub", "del subalterno",
           "del subbuglio", "del subdolo", "del sublime", "del suburbano", "del successore", "del succo",
           "della succube", "del succulento", "della succursale", "del sudario", "della sudditanza", "del suddito",
           "del sudicio", "del suffisso", "del suffragio", "del suffumigio", "del suggeritore", "del sughero",
           "del sugo", "del suino", "della suite", "del sulfureo", "del sultano", "di Steffo", "di Spaggia",
           "di Sabrina", "del sas", "del ses", "del sis", "del sos", "del sus", "della supremazia", "del Santissimo",
           "della scatola", "del supercalifragilistichespiralidoso", "del sale", "del salame", "di (Town of) Salem",
           "di Stronghold", "di SOMA", "dei Saints", "di S.T.A.L.K.E.R.", "di Sanctum", "dei Sims", "di Sid",
           "delle Skullgirls", "di Sonic", "di Spiral (Knights)", "di Spore", "di Starbound", "di SimCity", "di Sensei",
           "di Ssssssssssssss... Boom! E' esploso il dizionario", "della scala", "di Sakura", "di Suzie", "di Shinji",
           "del senpai", "del support", "di Superman", "di Sekiro"]
SMECDS = "🤔 Secondo me, è colpa {ds}."


class SmecdsCommand(Command):

    command_name = "smecds"
    command_description = "Secondo me, è colpa dello stagista..."
    command_syntax = ""

    @classmethod
    async def common(cls, call: Call):
        ds = random.sample(DS_LIST, 1)[0]
        return await call.reply(safeformat(SMECDS, ds=ds))
