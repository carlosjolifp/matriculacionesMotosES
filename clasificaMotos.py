import json
import os
import re

DICCIONARIO_MODELOS = {
    "WW125": "PCX 125", "WW 125": "PCX 125", "PCX125": "PCX 125", "JK05": "PCX 125",
    "SH125": "Scoopy SH125i", "SH125AD": "Scoopy SH125i", "SH 125": "Scoopy SH125i", "JF90": "Scoopy SH125i",
    "ADV350": "ADV 350", "ADV 350": "ADV 350", "NF13": "ADV 350",
    "NSS125": "Forza 125", "NSS 125": "Forza 125", "JK02": "Forza 125",
    "NSS350": "Forza 350", "NSS 350": "Forza 350", "NF10": "Forza 350",
    "NSS750": "Forza 750", "RH11": "Forza 750",
    "GPD125": "NMAX 125", "GPD 125": "NMAX 125", "SEC7": "NMAX 125", "SE86": "NMAX 125",
    "CZD300": "XMAX 300", "CZD 300": "XMAX 300", "SH14": "XMAX 300",
    "XP500": "TMAX 560", "XP560": "TMAX 560", "SJ18": "TMAX 560",
    "MT07": "MT-07", "MT 07": "MT-07", "Z900": "Z900", "Z 900": "Z900"
}

PATRONES_SCOOTER = [
    "PCX", "NMAX", "SCOOPY", "SH125", "SH 125", "SH300", "SH350", "AGILITY", "SYMPHONY", 
    "FORZA", "XMAX", "X-MAX", "BURGMAN", "ADV 350", "ADV350", "X-ADV", "XADV", "TMAX", "T-MAX", 
    "TRICITY", "MEDLEY", "LIBERTY", "VESPA", "JET 14", "JET14", "DTX", "VIESTE", "SR1", "E350",
    "D350", "M350", "M125", "D125", "CRUISYM", "MAXSYM", "SUPER DINK", "XCITING", "AK 550", "AK550",
    "WW125", "GPD125", "SH125AD", "UH125", "CZD300"
]

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
    print(f"🔄 Analizando {len(archivos)} archivos...")

    for archivo in archivos:
        path = os.path.join(carpeta_data, archivo)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Detectar dónde está la lista de registros de forma segura
            registros = []
            if isinstance(data, list):
                registros = data
            elif isinstance(data, dict):
                if "registros" in data:
                    registros = data["registros"]
                elif "data" in data:
                    registros = data["data"]
                else:
                    # Buscar la primera llave que contenga una lista
                    for k, v in data.items():
                        if isinstance(v, list):
                            registros = v
                            break

            if not registros:
                print(f"  ⚠️ Advertencia: No se encontraron registros en {archivo}")
                continue

            # Procesar cada registro
            for reg in registros:
                marca = reg.get("mar", "").strip()
                modelo_crudo = reg.get("mod", "").strip()
                
                nombre_comercial = obtener_nombre_comercial(marca, modelo_crudo)
                reg["mod"] = nombre_comercial
                reg["scoot"] = es_scooter(marca, modelo_crudo, nombre_comercial)

            # Guardar cambios manteniendo la estructura original
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                
            print(f"  ✓ {archivo} modificado correctamente con 'scoot'.")

        except Exception as e:
            print(f"  ❌ Error en {archivo}: {e}")

    print("\n🏁 Proceso finalizado.")

if __name__ == "__main__":
    actualizar_jsons()