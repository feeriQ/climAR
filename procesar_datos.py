import json
import re

def procesar_coordenadas(archivo):
    """Procesa el archivo de coordenadas del SMN"""
    coordenadas = {}
    
    with open(archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Saltar las primeras 3 líneas (encabezados)
    for linea in lineas[3:]:
        if not linea.strip():
            continue
        
        # Extraer por posiciones fijas
        nombre = linea[0:35].strip()
        provincia = linea[35:55].strip()
        
        # Extraer latitud
        try:
            lat_str = linea[55:65].strip()
            lat_partes = lat_str.split()
            if len(lat_partes) >= 2:
                lat_g = float(lat_partes[0])
                lat_m = float(lat_partes[1])
                lat_dec = lat_g + (lat_m / 60) if lat_g >= 0 else lat_g - (lat_m / 60)
            else:
                continue
        except (ValueError, IndexError):
            continue
        
        # Extraer longitud
        try:
            lon_str = linea[65:75].strip()
            lon_partes = lon_str.split()
            if len(lon_partes) >= 2:
                lon_g = float(lon_partes[0])
                lon_m = float(lon_partes[1])
                lon_dec = lon_g + (lon_m / 60) if lon_g >= 0 else lon_g - (lon_m / 60)
            else:
                continue
        except (ValueError, IndexError):
            continue
        
        # Extraer altura
        try:
            altura_str = linea[75:85].strip()
            altura = int(altura_str) if altura_str else 0
        except ValueError:
            altura = 0
        
        coordenadas[nombre] = {
            'lat': lat_dec,
            'lng': lon_dec,
            'altura': altura,
            'provincia': provincia
        }
    
    return coordenadas

def leer_datos_climaticos(archivo):
    """Lee el archivo de datos climáticos"""
    datos = {}
    
    with open(archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    for linea in lineas:
        if not linea.strip() or 'Estación' in linea:
            continue
        
        partes = linea.strip().split('\t')
        
        if len(partes) < 14:
            continue
        
        estacion = partes[0].strip()
        variable = partes[1].strip()
        
        valores = []
        for i in range(2, 14):
            if i < len(partes):
                valor_str = partes[i].strip().replace(',', '.')
                try:
                    valor = float(valor_str) if valor_str else None
                except ValueError:
                    valor = None
                valores.append(valor)
        
        if estacion not in datos:
            datos[estacion] = {}
        datos[estacion][variable] = valores
    
    return datos

def combinar_datos(datos_climaticos, coordenadas):
    """Combina datos climáticos con coordenadas"""
    datos_combinados = []
    no_encontradas = []
    
    for estacion_clima, variables in datos_climaticos.items():
        estacion_busqueda = estacion_clima.strip().upper()
        coordenada_encontrada = None
        
        # Buscar coincidencia
        for nombre_coord, coord_data in coordenadas.items():
            nombre_coord_upper = nombre_coord.upper()
            
            if estacion_busqueda == nombre_coord_upper:
                coordenada_encontrada = coord_data
                break
            
            if estacion_busqueda in nombre_coord_upper or nombre_coord_upper in estacion_busqueda:
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
        for est in no_encontradas[:5]:
            print(f"   - {est}")
        if len(no_encontradas) > 5:
            print(f"   ... y {len(no_encontradas) - 5} más")
    
    return datos_combinados

def main():
    print("=" * 50)
    print("📊 PROCESANDO DATOS DEL SMN")
    print("=" * 50)
    
    # 1. Procesar coordenadas
    print("\n📍 Leyendo coordenadas...")
    coordenadas = procesar_coordenadas('Estaciones_smn.txt')
    print(f"   ✅ {len(coordenadas)} estaciones con coordenadas")
    
    # 2. Leer datos climáticos
    print("\n🌡️ Leyendo datos climáticos...")
    datos_climaticos = leer_datos_climaticos('Clima91-20.txt')
    print(f"   ✅ {len(datos_climaticos)} estaciones con datos climáticos")
    
    # 3. Combinar
    print("\n🔄 Combinando datos...")
    datos_final = combinar_datos(datos_climaticos, coordenadas)
    print(f"   ✅ {len(datos_final)} estaciones combinadas")
    
    # 4. Guardar
    with open('datos_completos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_final, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Archivo 'datos_completos.json' generado!")
    
    # 5. Estadísticas
    provincias = sorted(set(e['provincia'] for e in datos_final if e['provincia']))
    print(f"\n📊 Estadísticas finales:")
    print(f"   - Total estaciones: {len(datos_final)}")
    print(f"   - Provincias: {len(provincias)}")
    print(f"   - Ejemplo: {', '.join(provincias[:5])}...")
    
    print("\n🚀 ¡Listo! Ahora abre el archivo 'index.html' en tu navegador.")

if __name__ == "__main__":
    main()