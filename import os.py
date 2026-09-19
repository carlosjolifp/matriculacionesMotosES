import os
import requests
import time

# Configuración de fechas límites
AÑO_INICIO = 2014
MES_INICIO = 12

AÑO_FIN = 2026
MES_FIN = 8

# Carpeta de destino
CARPETA_DESTINO = "descargas_dgt"
os.makedirs(CARPETA_DESTINO, exist_ok=True)

def descargar_archivos_dgt():
    print(f"Iniciando descarga de históricos DGT ({MES_INICIO}/{AÑO_INICIO} -> {MES_FIN}/{AÑO_FIN})...\n")

    for año in range(AÑO_INICIO, AÑO_FIN + 1):
        # Determinar el rango de meses para el año actual
        m_inicio = MES_INICIO if año == AÑO_INICIO else 1
        m_fin = MES_FIN if año == AÑO_FIN else 12

        for mes in range(m_inicio, m_fin + 1):
            mes_padded = f"{mes:02d}"  # Formato con cero a la izquierda (ej: "05")
            mes_raw = str(mes)         # Formato sin cero (ej: "5")
            
            nombre_archivo = f"export_mensual_mat_{año}{mes_padded}.zip"
            ruta_local = os.path.join(CARPETA_DESTINO, nombre_archivo)

            # Evitar volver a descargar si ya existe
            if os.path.exists(ruta_local):
                print(f"  [OMITIDO] {nombre_archivo} ya existe.")
                continue

            # Construcción de la URL según la estructura oficial
            url = f"https://www.dgt.es/microdatos/salida/{año}/{mes_raw}/vehiculos/matriculaciones/{nombre_archivo}"

            print(f"Descargando: {nombre_archivo} ...", end=" ", flush=True)

            try:
                # Descarga por bloques (stream) para optimizar memoria
                res = requests.get(url, stream=True, timeout=20)
                
                if res.status_code == 200:
                    with open(ruta_local, 'wb') as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print("¡OK!")
                else:
                    print(f"FALLÓ (Código HTTP: {res.status_code})")

            except Exception as e:
                print(f"ERROR: {e}")

            # Pequeña pausa entre peticiones para ser respetuoso con el servidor de la DGT
            time.sleep(0.5)

    print(f"\n Proceso finalizado. Archivos guardados en: '{os.path.abspath(CARPETA_DESTINO)}'")

if __name__ == "__main__":
    descargar_archivos_dgt()