import json
import re

import unicodedata

def normalizar(texto):
    """Quita tildes, diéresis y convierte a mayúsculas"""
    if not texto:
        return ''
    # Descompone caracteres acentuados y elimina los diacríticos
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    # Quita asteriscos y espacios extra
    texto = texto.replace('*', '').strip().upper()
    return texto

def procesar_coordenadas(archivo):
    """Procesa el archivo de coordenadas del SMN."""
    coordenadas = {}

    with open(archivo, "r", encoding="latin-1") as f:
        lineas = f.readlines()

    # El archivo tiene dos líneas de encabezado y columnas separadas por
    # dos o más espacios.
    for linea in lineas[2:]:
        if not linea.strip():
            continue

        partes = re.split(r"\s{2,}", linea.strip())
        if len(partes) < 6:
            continue

        try:
            nombre = partes[0].strip()
            provincia = partes[1].strip()
            lat_g = float(partes[2])
            lat_m = float(partes[3])
            lon_g = float(partes[4])
            lon_m = float(partes[5])
        except (ValueError, IndexError):
            continue

        lat_dec = lat_g - (lat_m / 60) if lat_g < 0 else lat_g + (lat_m / 60)
        lon_dec = lon_g - (lon_m / 60) if lon_g < 0 else lon_g + (lon_m / 60)

        try:
            altura = int(partes[6]) if len(partes) > 6 else 0
        except ValueError:
            altura = 0

        coordenadas[nombre] = {
            "lat": lat_dec,
            "lng": lon_dec,
            "altura": altura,
            "provincia": provincia,
        }

# Arreglo manual para estaciones con nombres rotos
coordenadas['PRESIDENCIA ROQUE SAENZ PEÑA AERO'] = {
    'lat': -26.7333,
    'lng': -60.4833,
    'altura': 93,
    'provincia': 'CHACO'
}

# Estaciones que no están en el archivo de coordenadas del SMN
coordenadas['EL TRÉBOL'] = {
    'lat': -32.202,
    'lng': -61.704 ,
    'altura': 96,
    'provincia': 'SANTA FE'
}
coordenadas['SAN MIGUEL'] = {
    'lat': -34.55569794177408, 
    'lng': -58.730781460405474,
    'altura': 26,
    'provincia': 'BUENOS AIRES'
}
coordenadas['CORONEL PRINGLES AERO'] = {
    'lat': -38.006449896918674, 
    'lng': -61.33192014759799,
    'altura': 233,
    'provincia': 'BUENOS AIRES'
}
    return coordenadas


def leer_datos_climaticos(archivo):
    """Lee el archivo de datos climáticos."""
    datos = {}

    with open(archivo, "r", encoding="latin-1") as f:
        lineas = f.readlines()

    for linea in lineas:
        if not linea.strip() or "Estaci" in linea:
            continue

        partes = linea.strip().split("\t")
        if len(partes) < 14:
            continue

        estacion = partes[0].strip()
        variable = partes[1].strip()

        valores = []
        for i in range(2, 14):
            if i < len(partes):
                valor_str = partes[i].strip().replace(",", ".")
                try:
                    valor = float(valor_str) if valor_str else None
                except ValueError:
                    valor = None
                valores.append(valor)

        if estacion not in datos:
            datos[estacion] = {}
        datos[estacion][variable] = valores

    return datos


def normalizar(texto):
    """Normaliza texto para comparación: mayúsculas y sin tildes."""
    replacements = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Ñ": "N",
        "ñ": "n",
    }
    for clave, valor in replacements.items():
        texto = texto.replace(clave, valor)
    return texto.upper().strip()


def combinar_datos(datos_climaticos, coordenadas):
    """Combina datos climáticos con coordenadas (normalizando tildes)"""
    datos_combinados = []
    no_encontradas = []
    
    for estacion_clima, variables in datos_climaticos.items():
        estacion_busqueda = normalizar(estacion_clima)
        coordenada_encontrada = None
        
        # Buscar coincidencia (con normalización)
        for nombre_coord, coord_data in coordenadas.items():
            nombre_coord_norm = normalizar(nombre_coord)
            
            if estacion_busqueda == nombre_coord_norm:
                coordenada_encontrada = coord_data
                break
            
            if estacion_busqueda in nombre_coord_norm or nombre_coord_norm in estacion_busqueda:
                coordenada_encontrada = coord_data
                break
        
        if coordenada_encontrada:
            datos_combinados.append({
                'nombre': estacion_clima,
                'lat': coordenada_encontrada['lat'],
                'lng': coordenada_encontrada['lng'],
                'altura': coordenada_encontrada['altura'],
                'provincia': coordenada_encontrada['provincia'],
                'variables': variables
            })
        else:
            no_encontradas.append(estacion_clima)
    
    if no_encontradas:
        print(f"\n⚠️ {len(no_encontradas)} estaciones sin coordenadas:")
        for est in no_encontradas:
            print(f"   - {est}")
    
    return datos_combinados


def main():
    print("=" * 50)
    print("📊 PROCESANDO DATOS DEL SMN")
    print("=" * 50)

    print("\n📍 Leyendo coordenadas...")
    coordenadas = procesar_coordenadas("Estaciones_smn.txt")
    print(f"   ✅ {len(coordenadas)} estaciones con coordenadas")

    print("\n🌡️ Leyendo datos climáticos...")
    datos_climaticos = leer_datos_climaticos("Clima91-20.txt")
    print(f"   ✅ {len(datos_climaticos)} estaciones con datos climáticos")

    print("\n🔄 Combinando datos...")
    datos_final = combinar_datos(datos_climaticos, coordenadas)
    print(f"   ✅ {len(datos_final)} estaciones combinadas")

    with open("datos_completos.json", "w", encoding="utf-8") as f:
        json.dump(datos_final, f, ensure_ascii=False, indent=2)

    print("\n✅ Archivo 'datos_completos.json' generado!")

    provincias = sorted(set(e["provincia"] for e in datos_final if e["provincia"]))
    print("\n📊 Estadísticas finales:")
    print(f"   - Total estaciones: {len(datos_final)}")
    print(f"   - Provincias: {len(provincias)}")
    if provincias:
        print(f"   - Ejemplo: {', '.join(provincias[:5])}...")

    print("\n🚀 ¡Listo! Archivo generado correctamente.")


if __name__ == "__main__":
    main()
