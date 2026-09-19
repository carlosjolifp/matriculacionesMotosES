import os
import zipfile
import json

# Ruta fija donde están los .zip descargados
CARPETA_ZIP = r"C:\Users\Carlos\AppData\Local\Programs\Microsoft VS Code\descargas_dgt"

# Guardar la carpeta 'data' en el directorio actual donde se lanza el script
DIRECTORIO_ACTUAL = os.getcwd()
CARPETA_OUTPUT = os.path.join(DIRECTORIO_ACTUAL, "data")

os.makedirs(CARPETA_OUTPUT, exist_ok=True)

def parse_linea_dgt(line):
    """Parsea una línea de ancho fijo de la DGT al formato JSON compacto."""
    if len(line) < 100:
        return None

    def get_val(start, length):
        if len(line) < start:
            return ""
        return line[start:start + length].strip()

    fec_mat_raw = get_val(0, 8)
    if len(fec_mat_raw) == 8:
        fec_mat = f"{fec_mat_raw[4:8]}-{fec_mat_raw[2:4]}-{fec_mat_raw[0:2]}"
    else:
        fec_mat = fec_mat_raw

    cod_clase_mat = get_val(8, 1)
    marca = get_val(17, 30) or "SIN MARCA"
    modelo = get_val(47, 22) or "SIN MODELO"
    bastidor = get_val(70, 21)
    cod_tipo = get_val(91, 2)
    cod_prop = get_val(93, 1)
    
    try:
        cil = int(get_val(94, 5) or 0)
    except ValueError:
        cil = 0
        
    try:
        cvf = float(get_val(99, 6) or 0)
    except ValueError:
        cvf = 0.0

    localidad = get_val(128, 24) or "DESCONOCIDA"
    cod_prov_veh = get_val(152, 2) or "ND"
    ind_nuevo_usado = get_val(178, 1) or "N"
    persona_fj = get_val(179, 1) or "D"
    cat_elec = get_val(321, 5)

    # Clasificación de propulsión
    prop_desc = "GASOLINA"
    if cat_elec in ["BEV", "PHEV", "HEV"]:
        prop_desc = cat_elec
    else:
        if cod_prop == "1":
            prop_desc = "DIESEL"
        elif cod_prop == "2":
            prop_desc = "BEV"
        elif cod_prop == "6":
            prop_desc = "GLP"
        elif cod_prop == "7":
            prop_desc = "GNC"
        elif cod_prop in ["3"]:
            prop_desc = "HEV"

    # Clasificación de categoría/tipo
    tipo_group = "OTROS"
    if cod_tipo == "40":
        tipo_group = "TURISMO"
    elif cod_tipo == "50":
        tipo_group = "MOTOCICLETA"
    elif cod_tipo in ["20", "21"]:
        tipo_group = "FURGONETA"
    elif cod_tipo == "30":
        tipo_group = "CAMION"
    elif cod_tipo in ["04", "05"]:
        tipo_group = "CICLOMOTOR"
    elif cod_tipo in ["80", "81"]:
        tipo_group = "TRACTOR"

    return {
        "fecMat": fec_mat,
        "claseMat": cod_clase_mat,
        "marca": marca,
        "modelo": modelo,
        "tipoGroup": tipo_group,
        "codTipo": cod_tipo,
        "propulsion": prop_desc,
        "cil": cil,
        "cvf": cvf,
        "nuevoUsado": ind_nuevo_usado,
        "titular": persona_fj,
        "prov": cod_prov_veh,
        "loc": localidad,
        "vin": bastidor
    }

def procesar_todos_los_zips():
    if not os.path.exists(CARPETA_ZIP):
        print(f"Error: La carpeta de descargas '{CARPETA_ZIP}' no existe.")
        return

    archivos_zip = sorted([f for f in os.listdir(CARPETA_ZIP) if f.endswith('.zip')])
    print(f"Se encontraron {len(archivos_zip)} archivos .zip en:\n{CARPETA_ZIP}")
    print(f"Los ficheros JSON se guardarán en:\n{CARPETA_OUTPUT}\n")

    index_summary = []

    for archivo in archivos_zip:
        ruta_zip = os.path.join(CARPETA_ZIP, archivo)
        
        # Extraer Año y Mes del nombre (export_mensual_mat_AAAAMM.zip)
        periodo_raw = archivo.replace("export_mensual_mat_", "").replace(".zip", "")
        if len(periodo_raw) == 6:
            year = periodo_raw[:4]
            month = periodo_raw[4:]
            periodo_fmt = f"{year}-{month}"
        else:
            periodo_fmt = periodo_raw

        json_filename = f"{periodo_fmt}.json"
        ruta_json_out = os.path.join(CARPETA_OUTPUT, json_filename)

        if os.path.exists(ruta_json_out):
            print(f"  [OMITIDO] {json_filename} ya existe.")
            index_summary.append({"periodo": periodo_fmt, "archivo": json_filename})
            continue

        print(f"Procesando {archivo} -> {json_filename} ...", end=" ", flush=True)

        try:
            with zipfile.ZipFile(ruta_zip, 'r') as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt') or f.endswith('.dat')]
                if not txt_files:
                    print("OMITIDO (Sin .txt interno)")
                    continue

                with z.open(txt_files[0]) as f:
                    contenido = f.read().decode('latin-1', errors='replace')
                    lineas = contenido.splitlines()

            registros = []
            for line in lineas:
                parsed = parse_linea_dgt(line)
                if parsed:
                    registros.append(parsed)

            output_data = {
                "periodo": periodo_fmt,
                "total": len(registros),
                "registros": registros
            }

            with open(ruta_json_out, 'w', encoding='utf-8') as jf:
                json.dump(output_data, jf, ensure_ascii=False)

            index_summary.append({
                "periodo": periodo_fmt,
                "total": len(registros),
                "archivo": json_filename
            })

            print(f"¡OK! ({len(registros):,} registros)")

        except Exception as e:
            print(f"ERROR: {e}")

    # Archivo índice global de periodos
    ruta_index = os.path.join(CARPETA_OUTPUT, "index.json")
    with open(ruta_index, 'w', encoding='utf-8') as ij:
        json.dump(index_summary, ij, ensure_ascii=False, indent=2)

    print(f"\n Proceso completado. La carpeta 'data' se ha generado en:")
    print(CARPETA_OUTPUT)

if __name__ == "__main__":
    procesar_todos_los_zips()