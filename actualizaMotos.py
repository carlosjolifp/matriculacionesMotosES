import os
import zipfile
import io
import json
import requests
from datetime import datetime

# Carpeta de destino de los JSON de motos
CARPETA_MOTOS = "data_motos"
os.makedirs(CARPETA_MOTOS, exist_ok=True)

def parse_linea_motos(line):
    """Parsea la línea de la DGT y devuelve un objeto ultraligero solo si es Motocicleta."""
    if len(line) < 100:
        return None

    def get_val(start, length):
        if len(line) < start:
            return ""
        return line[start:start + length].strip()

    cod_clase_mat = get_val(8, 1)
    cod_tipo = get_val(91, 2)
    
    # Excluir Ciclomotores explícitamente (04, 05, clase 6) y mantener solo Motocicletas (50)
    is_ciclomotor = cod_tipo in ["04", "05"] or cod_clase_mat == "6"
    is_motocicleta = cod_tipo == "50"

    if not is_motocicleta or is_ciclomotor:
        return None

    fec_mat_raw = get_val(0, 8)
    fec_mat = f"{fec_mat_raw[4:8]}-{fec_mat_raw[2:4]}-{fec_mat_raw[0:2]}" if len(fec_mat_raw) == 8 else fec_mat_raw
    marca = get_val(17, 30) or "SIN MARCA"
    modelo = get_val(47, 22) or "SIN MODELO"
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
        "tit": persona_fj
    }

def obtener_ultimo_periodo_existente():
    """Escanea la carpeta data_motos/ y devuelve (año, mes) del último archivo JSON."""
    archivos = [f for f in os.listdir(CARPETA_MOTOS) if f.endswith('.json') and f != 'index.json']
    if not archivos:
        return 2014, 11  # Si está vacía, empezará en 2014-12

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
    """Descarga el .zip de un mes específico de la DGT y genera el .json si existe."""
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

        print("¡Descargado! Procesando...", end=" ", flush=True)

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

        # Guardar JSON ultraligero
        output_data = {
            "periodo": periodo_fmt,
            "total": len(registros_motos),
            "registros": registros_motos
        }

        with open(ruta_json_out, 'w', encoding='utf-8') as jf:
            json.dump(output_data, jf, ensure_ascii=False, separators=(',', ':'))

        print(f"¡OK! ({len(registros_motos):,} motos saved)")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def regenerar_index_json():
    """Reconstruye el index.json con todos los meses presentes en data_motos/."""
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

    print(f"\n 'data_motos/index.json' actualizado correctamente con {len(index_list)} meses en total.")

def buscar_y_actualizar_faltantes():
    ultimo_yr, ultimo_mo = obtener_ultimo_periodo_existente()
    
    # Siguiente mes a buscar
    curr_yr = ultimo_yr
    curr_mo = ultimo_mo + 1
    if curr_mo > 12:
        curr_mo = 1
        curr_yr += 1

    now = datetime.now()
    max_yr = now.year
    max_mo = now.month

    print(f"=== BUSCADOR DE NUEVOS MESES DE LA DGT ===")
    print(f"Último mes en 'data_motos/': {ultimo_yr}-{ultimo_mo:02d}")
    print(f"Comprobando desde: {curr_yr}-{curr_mo:02d} hasta hoy...\n")

    nuevos_añadidos = 0

    while (curr_yr < max_yr) or (curr_yr == max_yr and curr_mo <= max_mo):
        exito = descargar_y_procesar_mes(curr_yr, curr_mo)
        if exito:
            nuevos_añadidos += 1
            # Avanzar al siguiente mes
            curr_mo += 1
            if curr_mo > 12:
                curr_mo = 1
                curr_yr += 1
        else:
            # Si un mes falla (la DGT aún no lo ha publicado), detenemos la búsqueda
            break

    if nuevos_añadidos > 0:
        regenerar_index_json()
        print(f"\n Process completado: Se han añadido {nuevos_añadidos} mes(es) nuevo(s).")
    else:
        print("\n Tu base de datos de motos ya está al día. No hay meses nuevos publicados.")

if __name__ == "__main__":
    buscar_y_actualizar_faltantes()