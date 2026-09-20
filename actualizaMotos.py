import os
import zipfile
import io
import json
import requests
from datetime import datetime

    # Este script descarga los archivos faltantes/nuevos de la dgt y añade el json limpio y adaptado

# Carpeta de destino de los JSON de motos
CARPETA_MOTOS = "data_motos"
os.makedirs(CARPETA_MOTOS, exist_ok=True)

# DICCIONARIO COMERCIAL (Puedes añadir aquí tus equivalencias de homologaciones DGT)
DICCIONARIO_MODELOS = {
    # HONDA
    "WW125": "PCX 125", "WW 125": "PCX 125", "PCX125": "PCX 125", "JK05": "PCX 125",
    "SH125": "Scoopy SH125i", "SH125AD": "Scoopy SH125i", "SH 125": "Scoopy SH125i", "JF90": "Scoopy SH125i",
    "ADV350": "ADV 350", "ADV 350": "ADV 350", "NF13": "ADV 350",
    "NSS125": "Forza 125", "NSS 125": "Forza 125", "JK02": "Forza 125",
    "NSS350": "Forza 350", "NSS 350": "Forza 350", "NF10": "Forza 350",
    "NSS750": "Forza 750", "RH11": "Forza 750",
    "NSC110": "Vision 110", "NSC 110": "Vision 110", "JF84": "Vision 110", "JK03": "Vision 110",
    
    # YAMAHA
    "GPD125": "NMAX 125", "GPD 125": "NMAX 125", "SEC7": "NMAX 125", "SE86": "NMAX 125",
    "MWD125": "Tricity 125",
    "CZD300": "XMAX 300", "CZD 300": "XMAX 300", "SH14": "XMAX 300",
    "SH08": "XMAX 125", "SEE1": "XMAX 125",
    "XP500": "TMAX 560", "XP560": "TMAX 560", "SJ18": "TMAX 560",
    "LCG125": "D'elight 125", "LCG 125": "D'elight 125", "SEC4": "D'elight 125",
    "YP125": "Xenter 125 / Cygnus", "YP125R": "XMAX 125", "YP125R-DA": "XMAX 125",
    
    # OTRAS / GENERALES
    "MT07": "MT-07", "MT 07": "MT-07", "Z900": "Z900", "Z 900": "Z900"
}

# PATRONES PARA DETECTAR SCOOTERS AUTOMÁTICAMENTE
PATRONES_SCOOTER = [
    "PCX", "NMAX", "SCOOPY", "SH125", "SH 125", "SH300", "SH350", "AGILITY", "SYMPHONY", 
    "FORZA", "XMAX", "X-MAX", "BURGMAN", "ADV 350", "ADV350", "X-ADV", "XADV", "TMAX", "T-MAX", 
    "TRICITY", "MEDLEY", "LIBERTY", "VESPA", "JET 14", "JET14", "DTX", "VIESTE", "SR1", "SR3", "SR4", "SR16", "E350",
    "D350", "M350", "M125", "D125", "CRUISYM", "MAXSYM", "SUPER DINK", "XCITING", "AK 550", "AK550",
    "WW125", "GPD125", "SH125AD", "UH125", "CZD300", "125X", "125V", "368G", "125M", "368", "C400", "C 400"
    "LCG", "YP", "RAYZR", "RAY ZR", "NSC110", "VISION", "SKYTOWN", "SKY TOWN", "SR GT", "SRGT", "ATR", "SILENCE", "S01", "S02", "S03", "E125"
]

def limpiar_marca(marca):
    """Limpia espacios sobrantes, unifica mayúsculas y agrupa variantes de marcas"""
    if not marca:
        return "DESCONOCIDA"
    m_clean = import_re = __import__('re').sub(r'\s+', ' ', str(marca)).strip().upper()
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
    import re
    return re.sub(r'\s+', ' ', str(modelo_crudo)).strip()

def es_scooter(marca, modelo_crudo, nombre_comercial):
    cadena_busqueda = f"{marca} {modelo_crudo} {nombre_comercial}".upper()
    return any(patron in cadena_busqueda for patron in PATRONES_SCOOTER)

def parse_linea_motos(line):
    """Parsea la línea de la DGT aplicando limpieza, diccionario y etiqueta scooter."""
    if len(line) < 100:
        return None

    def get_val(start, length):
        if len(line) < start:
            return ""
        return line[start:start + length].strip()

    cod_clase_mat = get_val(8, 1)
    cod_tipo = get_val(91, 2)
    
    # Excluir Ciclomotores y mantener solo Motocicletas (50)
    is_ciclomotor = cod_tipo in ["04", "05"] or cod_clase_mat == "6"
    is_motocicleta = cod_tipo == "50"

    if not is_motocicleta or is_ciclomotor:
        return None

    fec_mat_raw = get_val(0, 8)
    fec_mat = f"{fec_mat_raw[4:8]}-{fec_mat_raw[2:4]}-{fec_mat_raw[0:2]}" if len(fec_mat_raw) == 8 else fec_mat_raw
    
    marca_cruda = get_val(17, 30) or "SIN MARCA"
    marca = limpiar_marca(marca_cruda)
    
    modelo_crudo = get_val(47, 22) or "SIN MODELO"
    modelo = obtener_nombre_comercial(marca, modelo_crudo)
    
    scoot = es_scooter(marca, modelo_crudo, modelo)

    cod_prop = get_val(93, 1)
    cat_elec = get_val(321, 5)

    try:
        cil = int(get_val(94, 5) or 0)
    except ValueError:
        cil = 0
        
    try:
        cvf = float(get_val(99, 6) or 0)
    except ValueError:
        cvf = 0.0

    ind_nuevo_usado = get_val(178, 1) or "N"
    persona_fj = get_val(179, 1) or "D"

    prop_desc = "GASOLINA"
    if cat_elec in ["BEV", "PHEV", "HEV"]:
        prop_desc = cat_elec
    else:
        if cod_prop == "1":
            prop_desc = "DIESEL"
        elif cod_prop == "2":
            prop_desc = "BEV"
        elif cod_prop in ["3"]:
            prop_desc = "HEV"

    return {
        "fec": fec_mat,
        "mar": marca,
        "mod": modelo,
        "pro": prop_desc,
        "cil": cil,
        "cvf": cvf,
        "est": ind_nuevo_usado,
        "tit": persona_fj,
        "scoot": scoot
    }

def obtener_ultimo_periodo_existente():
    archivos = [f for f in os.listdir(CARPETA_MOTOS) if f.endswith('.json') and f != 'index.json']
    if not archivos:
        return 2014, 11  

    periodos = []
    for a in archivos:
        nombre = a.replace('.json', '')
        if len(nombre) == 7 and nombre[4] == '-':
            try:
                yr = int(nombre[:4])
                mo = int(nombre[5:])
                periodos.append((yr, mo))
            except ValueError:
                pass

    if not periodos:
        return 2014, 11

    periodos.sort()
    return periodos[-1]

def descargar_y_procesar_mes(year, month):
    month_padded = f"{month:02d}"
    month_raw = str(month)
    periodo_fmt = f"{year}-{month_padded}"
    json_filename = f"{periodo_fmt}.json"
    ruta_json_out = os.path.join(CARPETA_MOTOS, json_filename)

    url = f"https://www.dgt.es/microdatos/salida/{year}/{month_raw}/vehiculos/matriculaciones/export_mensual_mat_{year}{month_padded}.zip"
    
    print(f"Buscando {periodo_fmt} en la DGT...", end=" ", flush=True)

    try:
        res = requests.get(url, timeout=25)
        if res.status_code != 200:
            print(f"NO DISPONIBLE (HTTP {res.status_code})")
            return False

        print("¡Descargado! Procesando con limpieza y diccionarios...", end=" ", flush=True)

        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt') or f.endswith('.dat')]
            if not txt_files:
                print("Error: Sin archivo .txt interno.")
                return False

            with z.open(txt_files[0]) as f:
                contenido = f.read().decode('latin-1', errors='replace')
                lineas = contenido.splitlines()

        registros_motos = []
        for line in lineas:
            parsed = parse_linea_motos(line)
            if parsed:
                registros_motos.append(parsed)

        output_data = {
            "periodo": periodo_fmt,
            "total": len(registros_motos),
            "registros": registros_motos
        }

        with open(ruta_json_out, 'w', encoding='utf-8') as jf:
            json.dump(output_data, jf, ensure_ascii=False, separators=(',', ':'))

        print(f"¡OK! ({len(registros_motos):,} registros guardados)")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def regenerar_index_json():
    archivos = sorted([f for f in os.listdir(CARPETA_MOTOS) if f.endswith('.json') and f != 'index.json'])
    index_list = []

    for archivo in archivos:
        ruta = os.path.join(CARPETA_MOTOS, archivo)
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                index_list.append({
                    "periodo": data.get("periodo", archivo.replace('.json', '')),
                    "total": data.get("total", len(data.get("registros", []))),
                    "archivo": archivo
                })
        except Exception as e:
            print(f"Error leyendo {archivo} para index.json: {e}")

    index_list.sort(key=lambda x: x["periodo"])
    
    ruta_index = os.path.join(CARPETA_MOTOS, "index.json")
    with open(ruta_index, 'w', encoding='utf-8') as ij:
        json.dump(index_list, ij, ensure_ascii=False, indent=2)

    print(f"\n📁 'data_motos/index.json' actualizado con {len(index_list)} meses en total.")

def buscar_y_actualizar_faltantes():
    ultimo_yr, ultimo_mo = obtener_ultimo_periodo_existente()
    
    curr_yr = ultimo_yr
    curr_mo = ultimo_mo + 1
    if curr_mo > 12:
        curr_mo = 1
        curr_yr += 1

    now = datetime.now()
    max_yr = now.year
    max_mo = now.month

    print(f"=== ACTUALIZADOR INTELIGENTE DGT MOTO-SCOOTER ===")
    print(f"Último mes guardado: {ultimo_yr}-{ultimo_mo:02d}")
    print(f"Comprobando nuevos meses hasta la actualidad...\n")

    nuevos_añadidos = 0

    while (curr_yr < max_yr) or (curr_yr == max_yr and curr_mo <= max_mo):
        exito = descargar_y_procesar_mes(curr_yr, curr_mo)
        if exito:
            nuevos_añadidos += 1
            curr_mo += 1
            if curr_mo > 12:
                curr_mo = 1
                curr_yr += 1
        else:
            break

    if nuevos_añadidos > 0:
        regenerar_index_json()
        print(f"\n🎉 ¡Proceso completado! Se han añadido y optimizado {nuevos_añadidos} mes(es) nuevo(s).")
    else:
        print("\n✨ La base de datos ya está al día. No hay meses nuevos publicados por la DGT.")

if __name__ == "__main__":
    buscar_y_actualizar_faltantes()