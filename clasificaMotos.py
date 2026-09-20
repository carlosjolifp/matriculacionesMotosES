import json
import os
import re

# DICCIONARIO AMPLIADO DE HOMOLOGACIONES DGT -> NOMBRES COMERCIALES
DICCIONARIO_MODELOS = {
    # HONDA
    "WW125": "PCX 125", "WW 125": "PCX 125", "PCX125": "PCX 125", "JK05": "PCX 125",
    "SH125": "Scoopy SH125i", "SH125AD": "Scoopy SH125i", "SH 125": "Scoopy SH125i", "JF90": "Scoopy SH125i",
    "ADV350": "ADV 350", "ADV 350": "ADV 350", "NF13": "ADV 350",
    "NSS125": "Forza 125", "NSS 125": "Forza 125", "JK02": "Forza 125",
    "NSS350": "Forza 350", "NSS 350": "Forza 350", "NF10": "Forza 350",
    "NSS750": "Forza 750", "RH11": "Forza 750",
    "NSC110": "Vision 110", "NSC 110": "Vision 110", "JF84": "Vision 110", "JK03": "Vision 110",
    "CB125R": "CB125R", "CBF125": "CB125F",
    "CB500X": "CB500X", "PC64": "CB500X", "NX500": "NX500", "PC70": "NX500",
    "CB750": "CB750 Hornet", "CB 750": "CB750 Hornet", "RH12": "CB750 Hornet",
    "XL750": "XL750 Transalp", "RD16": "XL750 Transalp",
    "CRF1100": "CRF1100L Africa Twin", "SD08": "CRF1100L Africa Twin", "SD09": "CRF1100L Africa Twin",
    "X-ADV": "X-ADV 750", "XADV": "X-ADV 750", "RC95": "X-ADV 750", "RH10": "X-ADV 750",
    "CMX500": "Rebel 500",

    # YAMAHA
    "GPD125": "NMAX 125", "GPD 125": "NMAX 125", "SEC7": "NMAX 125", "SE86": "NMAX 125",
    "MWD125": "Tricity 125",
    "CZD300": "XMAX 300", "CZD 300": "XMAX 300", "SH14": "XMAX 300",
    "SH08": "XMAX 125", "SEE1": "XMAX 125",
    "XP500": "TMAX 560", "XP560": "TMAX 560", "SJ18": "TMAX 560",
    "LCG125": "D'elight 125", "LCG 125": "D'elight 125", "SEC4": "D'elight 125",
    "YP125": "Xenter 125 / Cygnus", "YP125R": "XMAX 125", "YP125R-DA": "XMAX 125",
    "MT07": "MT-07", "MT 07": "MT-07", "Z900": "Z900", "Z 900": "Z900",

    # KAWASAKI
    "Z900": "Z900", "Z 900": "Z900", "ZR900B": "Z900", "ZR900F": "Z900", "ZR900H": "Z900 (A2)",
    "Z650": "Z650", "ER650H": "Z650", "Z125": "Z125", "BR125K": "Z125",
    "KLE650": "Versys 650", "VERSYS 650": "Versys 650",
    "EX400": "Ninja 400", "EX500": "Ninja 500",

    # SUZUKI
    "UH125": "Burgman 125", "UH 125": "Burgman 125", "AM121": "Burgman Street 125EX",
    "DL650": "V-Strom 650", "DL 650": "V-Strom 650", "DL800": "V-Strom 800",
    "GSX-8S": "GSX-8S", "GSX8S": "GSX-8S", "GSX-S1000GT": "GSX-S1000GT",

    # KYMCO
    "AGILITY CITY 125": "Agility City 125", "AGILITY 125": "Agility City 125", "C10000": "Agility City 125",
    "C11000": "Agility S 125", "DTX 125": "DTX 125", "DTX 350": "DTX 350", "SK25": "DTX 125",
    "SUPER DINK 125": "Super Dink 125", "V20000": "Super Dink 125",
    "XCITING 400": "Xciting VS 400", "AK550": "AK 550 Premium", "AK 550": "AK 550 Premium",

    # SYM
    "SYMPHONY 125": "Symphony 125", "SYMPHONY ST": "Symphony ST 125", "SYMPHONY SR": "Symphony SR 125", "LX12W": "Symphony 125",
    "JET 14 125": "Jet 14 125", "JET 14": "Jet 14 125",
    "XCITY 125": "Cruisym Alpha 125", "CRUISYM 125": "Cruisym Alpha 125",
    "MAXSYM TL": "Maxsym TL 508", "MAXSYM 508": "Maxsym TL 508",

    # BMW
    "R1250GS": "R 1250 GS", "R 1250 GS": "R 1250 GS", "1G13": "R 1250 GS",
    "R1300GS": "R 1300 GS", "R 1300 GS": "R 1300 GS", "GG13": "R 1300 GS",
    "F850GS": "F 850 GS", "F900XR": "F 900 XR", "F900R": "F 900 R",
    "CE04": "CE 04", "CE 04": "CE 04", "C400X": "C 400 X", "C400GT": "C 400 GT",

    # VOGE & ZONTES
    "900DSX": "900DSX", "525DSX": "525DSX", "SR4 MAX": "SR4 Max", "SR1": "SR1 125",
    "E350": "E350", "D350": "D350", "M350": "M350", "M125": "M125", "D125": "D125"
}

PATRONES_SCOOTER = [
    "PCX", "NMAX", "SCOOPY", "SH125", "SH 125", "SH300", "SH350", "AGILITY", "SYMPHONY", 
    "FORZA", "XMAX", "X-MAX", "BURGMAN", "ADV 350", "ADV350", "X-ADV", "XADV", "TMAX", "T-MAX", 
    "TRICITY", "MEDLEY", "LIBERTY", "VESPA", "JET 14", "JET14", "DTX", "VIESTE", "SR1", "SR3", "SR4", "SR16", "E350",
    "D350", "M350", "M125", "D125", "CRUISYM", "MAXSYM", "SUPER DINK", "XCITING", "AK 550", "AK550",
    "WW125", "GPD125", "SH125AD", "UH125", "CZD300", "125X", "125V", "368G", "125M", "368",
    "LCG", "YP", "RAYZR", "RAY ZR", "NSC110", "VISION"
]

def limpiar_marca(marca):
    """Limpia espacios sobrantes, unifica mayúsculas y agrupa variantes como Moto Guzzi"""
    if not marca:
        return "DESCONOCIDA"
    
    m_clean = re.sub(r'\s+', ' ', str(marca)).strip().upper()
    
    # Unificar variantes de marcas compuestas comunes si fuera necesario
    if "GUZZI" in m_clean:
        return "MOTO GUZZI"
    
    return m_clean

def obtener_nombre_comercial(marca, modelo_crudo):
    if not modelo_crudo:
        return marca
    modelo_clean = str(modelo_crudo).strip().upper()
    if modelo_clean in DICCIONARIO_MODELOS:
        return DICCIONARIO_MODELOS[modelo_clean]
    for clave, comercial in DICCIONARIO_MODELOS.items():
        if clave in modelo_clean:
            return comercial
    return re.sub(r'\s+', ' ', str(modelo_crudo)).strip()

def es_scooter(marca, modelo_crudo, nombre_comercial):
    cadena_busqueda = f"{marca} {modelo_crudo} {nombre_comercial}".upper()
    return any(patron in cadena_busqueda for patron in PATRONES_SCOOTER)

def actualizar_jsons():
    carpeta_data = "data_motos"
    if not os.path.exists(carpeta_data):
        print(f"❌ No se encuentra la carpeta '{carpeta_data}'")
        return

    archivos = [f for f in os.listdir(carpeta_data) if f.endswith(".json") and f != "index.json"]
    print(f"🔄 Analizando, unificando marcas y traduciendo {len(archivos)} archivos...")

    for archivo in archivos:
        path = os.path.join(carpeta_data, archivo)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            registros = []
            if isinstance(data, list):
                registros = data
            elif isinstance(data, dict):
                if "registros" in data:
                    registros = data["registros"]
                elif "data" in data:
                    registros = data["data"]
                else:
                    for k, v in data.items():
                        if isinstance(v, list):
                            registros = v
                            break

            if not registros:
                print(f"  ⚠️ Advertencia: No se encontraron registros en {archivo}")
                continue

            for reg in registros:
                # 1. Unificar y limpiar el nombre de la marca
                marca_limpia = limpiar_marca(reg.get("mar", ""))
                reg["mar"] = marca_limpia
                
                # 2. Obtener nombre comercial y etiqueta scooter
                modelo_crudo = reg.get("mod", "").strip()
                nombre_comercial = obtener_nombre_comercial(marca_limpia, modelo_crudo)
                reg["mod"] = nombre_comercial
                reg["scoot"] = es_scooter(marca_limpia, modelo_crudo, nombre_comercial)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                
            print(f"  ✓ {archivo} procesado con éxito.")

        except Exception as e:
            print(f"  ❌ Error en {archivo}: {e}")

    print("\n🏁 Proceso finalizado.")

if __name__ == "__main__":
    actualizar_jsons()