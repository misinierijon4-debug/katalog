"""Manually verified entries for special-layout pages (216-225, 251-257, 260).

Source: visual reading of high-res page renders + rotated OCR pass.
Merged into katalog.json by parse step (run after parse.py).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

def campus(page, codes, name_suffix, size, gt, arts_spec, farbe, ycode, board):
    arts = [{"artnr": a, "stueck": s, "farbe": farbe, "groesse": g} for a, s, g in arts_spec]
    codes_all = list(codes) + ([ycode] if ycode else [])
    return {
        "id": f"p{page:03d}_{codes[0].replace('-','')}",
        "seite": page, "serie": "CAMPUS", "material": "Steingut/Feinsteinzeug 30x60 cm",
        "codes": codes_all, "tafel_groesse": size, "gt": gt, "artikel": arts,
        "label": None, "notizen": ["Mustertafel CAM 30x60 cm WAND"],
        "board_px200": board, "display": False, "manuell": True,
    }

def forum(page, variant, size, board, note=None):
    wand, bricks, boden, mosaik = variant
    arts = [
        {"artnr": wand, "stueck": None, "farbe": "Wand", "groesse": "30x60 cm"},
        {"artnr": bricks, "stueck": None, "farbe": "DI-Bricks", "groesse": None},
        {"artnr": boden, "stueck": None, "farbe": "Boden", "groesse": None},
        {"artnr": mosaik, "stueck": None, "farbe": "Mosaik", "groesse": None},
    ]
    notes = [f"Mustertafel FORUM 30x60 cm {wand.replace(' ','')} mit DI-Bricks {bricks.replace(' ','')} "
             f"und Boden {boden.replace(' ','')} und Mosaik {mosaik.replace(' ','')}",
             "Größen laut Kopfzeile: 72x78 / 65x130 / 94x134 / 97x184 / 104x184 / 107x184"
             + (" / 100x200" if wand != "FOM 1220" else "") + " / 100,5x192,5 / Sonderanfertigung"]
    if note:
        notes.append(note)
    gt = size.startswith("GT")
    return {
        "id": f"p{page:03d}_forum_{size.replace('GT ','').replace('x','_').replace(',','_').replace(' cm','')}",
        "seite": page, "serie": "FORUM", "material": "30x60 cm",
        "codes": [], "name": f"Mustertafel FORUM {size}" + ("" if gt else ""),
        "tafel_groesse": size, "gt": gt, "artikel": arts, "label": None,
        "notizen": notes, "board_px200": board, "display": False, "manuell": True,
    }

def mosa(page, nr, art_unten, art_oben, board):
    return {
        "id": f"p{page:03d}_mosa_tafel{nr}",
        "seite": page, "serie": "ARIZONA + GEORGIA", "material": "Mosaik",
        "codes": [], "name": f"Tafel {nr} (Mosaik ARIZONA + GEORGIA)",
        "tafel_groesse": "30x31 cm", "gt": False,
        "artikel": [
            {"artnr": art_unten[0], "stueck": "0,5", "farbe": art_unten[1], "groesse": None},
            {"artnr": art_oben[0], "stueck": "0,5", "farbe": art_oben[1], "groesse": None},
        ],
        "label": None,
        "notizen": ["Neuverklebung für Thekendisplay MOSA (Bestückungssatz 9569-MOSA-10-10)",
                     "Pro Tafel 2 Artikel (halbe Mosaikmatten), Etiketten rückseitig, ohne Verfugung"],
        "board_px200": board, "rot90": True, "display": False, "manuell": True,
    }

CAM_GT = [("CAM 1240", "1", "30x60 cm"), ("CAM 1241", "1", "30x60 cm")]
CAM_65 = [("CAM 1240", "2", "30x60 cm"), ("CAM 1241", "1", "30x60 cm")]
CAM_94 = [("CAM 1240", "2", "30x60 cm"), ("CAM 1240", "3", "30x30 cm"),
          ("CAM 1241", "1", "30x60 cm"), ("CAM 1241", "1", "30x30 cm")]
CAM_XL = [("CAM 1240", "3", "30x60 cm"), ("CAM 1240", "4", "30x30 cm"),
          ("CAM 1241", "2", "30x60 cm"), ("CAM 1241", "2", "30x30 cm")]
CAM8_GT = [("CAM 1280", "1", "30x60 cm"), ("CAM 1281", "1", "30x60 cm")]
CAM8_65 = [("CAM 1280", "2", "30x60 cm"), ("CAM 1281", "1", "30x60 cm")]
CAM8_94 = [("CAM 1280", "2", "30x60 cm"), ("CAM 1280", "3", "30x30 cm"),
           ("CAM 1281", "1", "30x60 cm"), ("CAM 1281", "1", "30x30 cm")]
CAM8_XL = [("CAM 1280", "3", "30x60 cm"), ("CAM 1280", "4", "30x30 cm"),
           ("CAM 1281", "2", "30x60 cm"), ("CAM 1281", "2", "30x30 cm")]

V1 = ("FOM 1220", "FOM 2540", "FOM 1240", "FOM 1442")
V2 = ("FOM 1280", "FOM 2570", "FOM 1270", "FOM 1472")
V3 = ("FOM 1280", "FOM 2590", "FOM 1290", "FOM 1492")

ENTRIES = [
    # ---- CAMPUS sand (CA41) ----
    campus(216, ["9555-CA41-04-10"], "GT", "GT 72x78 cm", True, CAM_GT, "sand", None,
           [104, 444, 526, 910]),
    campus(216, ["9585-CA41-04-10"], "65", "65x130 cm", False, CAM_65, "sand", "9336-CAM4-Y0",
           [100, 1184, 490, 1960]),
    campus(216, ["9557-CA41-04-10"], "94", "94x134 cm", False, CAM_94, "sand", "9336-CAM4-Y0",
           [772, 1162, 1336, 1960]),
    campus(217, ["9569-CA41-04-10", "9562-CA41-04-10", "9566-CA41-04-10"], "XL",
           "97x184 / 104x184 / 107x184 cm", False, CAM_XL, "sand", "9336-CAM4-Y0",
           [100, 700, 566, 1554]),
    campus(217, ["9568-CA41-04-10", "9587-CA41-04-10"], "XXL",
           "100x200 / 100,5x192,5 cm", False, CAM_XL, "sand", "9336-CAM4-Y0",
           [774, 628, 1240, 1556]),
    # ---- CAMPUS grau (CA81) ----
    campus(218, ["9555-CA81-04-10"], "GT", "GT 72x78 cm", True, CAM8_GT, "grau", None,
           [104, 444, 526, 910]),
    campus(218, ["9585-CA81-04-10"], "65", "65x130 cm", False, CAM8_65, "grau", "9336-CAM8-Y0",
           [100, 1184, 490, 1960]),
    campus(218, ["9557-CA81-04-10"], "94", "94x134 cm", False, CAM8_94, "grau", "9336-CAM8-Y0",
           [772, 1162, 1336, 1960]),
    campus(219, ["9569-CA81-04-10", "9562-CA81-04-10", "9566-CA81-04-10"], "XL",
           "97x184 / 104x184 / 107x184 cm", False, CAM8_XL, "grau", "9336-CAM8-Y0",
           [100, 700, 566, 1554]),
    campus(219, ["9568-CA81-04-10", "9587-CA81-04-10"], "XXL",
           "100x200 / 100,5x192,5 cm", False, CAM8_XL, "grau", "9336-CAM8-Y0",
           [774, 628, 1240, 1556]),
    # ---- FORUM ----
    forum(220, V1, "97x184 cm", [96, 696, 866, 2152]),
    forum(220, V1, "GT 72x78 cm", [924, 380, 1490, 994]),
    forum(220, V1, "65x130 cm", [924, 1104, 1444, 2116]),
    forum(221, V1, "94x134 cm", [60, 1130, 794, 2184],
          "Anmerkung: Prüfen ob untere Fliese ganz passt"),
    forum(221, V1, "100x200 cm", [840, 614, 1620, 2184],
          "Anmerkung: Vollflächige Verlegung – eventuell Boden kleiner"),
    forum(222, V2, "97x184 cm", [94, 690, 864, 2150]),
    forum(222, V2, "GT 72x78 cm", [924, 380, 1494, 994]),
    forum(222, V2, "65x130 cm", [924, 1104, 1444, 2114]),
    forum(223, V2, "94x134 cm", [60, 1130, 800, 2184]),
    forum(223, V2, "100x200 cm", [840, 610, 1624, 2184],
          "Anmerkung: Vollflächige Verlegung"),
    forum(224, V3, "97x184 cm", [94, 690, 864, 2150]),
    forum(224, V3, "GT 72x78 cm", [924, 380, 1494, 994]),
    forum(224, V3, "65x130 cm", [924, 1104, 1444, 2114]),
    forum(225, V3, "94x134 cm", [60, 1130, 800, 2184],
          "Anmerkung: Prüfen ob untere Fliese ganz passt"),
    forum(225, V3, "100x200 cm", [840, 610, 1624, 2184],
          "Anmerkung: Vollflächige Verlegung – eventuell dunkle Bordüre breiter"),
    # ---- MOSA info sheet ----
    {
        "id": "p251_mosa_info", "seite": 251, "serie": "ARIZONA + GEORGIA",
        "material": "Mosaik", "codes": ["9569-MOSA-10-10"],
        "name": "Bestückungssatz MOSA – 12 Mosaik-Tafeln",
        "tafel_groesse": "12 Tafeln je 30x31 cm", "gt": False, "artikel": [],
        "label": None,
        "notizen": ["Neuverklebung von 12 Tafeln (30x31 cm) für bestehende Thekendisplays MOSA",
                     "Pro Tafel jeweils 2 Artikel (halbe Mosaikmatten), Etiketten rückseitig",
                     "Ohne Verfugung", "Bitte auf gleiches Netz (Version 8E) achten"],
        "board_px200": [230, 190, 1430, 1310], "rot90": True, "display": True, "manuell": True,
    },
    # ---- MOSA Tafeln 1-12 (unten/oben = Anordnung auf der Tafel) ----
    mosa(252, 1, ("2ARI 0180", "ARI 180"), ("2ARI 0310", "ARI 310"), [300, 1190, 1390, 2310]),
    mosa(252, 2, ("2ARI 0110", "ARI 110"), ("2ARI 0270", "ARI 270"), [300, 50, 1390, 1130]),
    mosa(253, 3, ("2ARI 0230", "ARI 230"), ("2ARI 0380", "ARI 380"), [300, 1190, 1390, 2310]),
    mosa(253, 4, ("2ARI 0220", "ARI 220"), ("2ARI 0450", "ARI 450"), [300, 50, 1390, 1130]),
    mosa(254, 5, ("2ARI 0140", "ARI 140"), ("2ARI 0320", "ARI 320"), [300, 1190, 1390, 2310]),
    mosa(254, 6, ("2ARI 0240", "ARI 240"), ("2ARI 0360", "ARI 360"), [300, 50, 1390, 1130]),
    mosa(255, 7, ("2ARI 0160", "ARI 160"), ("2ARI 0440", "ARI 440"), [300, 1190, 1390, 2310]),
    mosa(255, 8, ("2ARI 0530", "ARI 530"), ("2ARI 0490", "ARI 490"), [300, 50, 1390, 1130]),
    mosa(256, 9, ("2ARI 0520", "ARI 520"), ("2ARI 0570", "ARI 570"), [300, 1190, 1390, 2310]),
    mosa(256, 10, ("2ARI 0590", "ARI 590"), ("2ARI 0580", "ARI 580"), [300, 50, 1390, 1130]),
    mosa(257, 11, ("2ARI 0540", "ARI 540"), ("2ARI 0560", "ARI 560"), [300, 1190, 1390, 2310]),
    mosa(257, 12, ("2GEO 0430", "GEO 430"), ("2GEO 0440", "GEO 440"), [300, 50, 1390, 1130]),
    # ---- GRADUS Display (p260) ----
    {
        "id": "p260_gradus", "seite": 260, "serie": "GRADUS",
        "material": None, "codes": ["9570-GR12-09-10"],
        "name": "Gradus 60x120 – Display (MÖBEL/DISPLAY/EXPOSITION)",
        "tafel_groesse": None, "gt": False, "artikel": [],
        "label": None,
        "notizen": ["Display für 8 Fliesen im Format 60x120 cm mit 10 mm Stärke",
                     "Höhe 122 cm (inkl. Bestückung) · Breite 76 cm · Tiefe 58 cm",
                     "Fliesen (60x120 cm): 8 Stück",
                     "Gewicht (netto) 7 kg · Gewicht bemustert 135 kg"],
        "board_px200": [217, 531, 750, 1281], "display": True, "manuell": True,
    },
]

# corrections for auto-parsed entries: id -> partial update
OVERRIDES = {
    "p232_9552WO900D10": {
        "artikel": [{"artnr": "WOO", "stueck": "4", "farbe": "anthrazit", "groesse": "20x120 cm"}],
        "unklar": ["Artikelnummer fehlt im PDF (dort steht nur 'Art. WOO (4 Stk.)')"],
    },
}

with open(os.path.join(HERE, "manual_entries.json"), "w", encoding="utf-8") as f:
    json.dump({"entries": ENTRIES, "overrides": OVERRIDES}, f, ensure_ascii=False, indent=1)
print("manual entries:", len(ENTRIES), "| overrides:", len(OVERRIDES))
