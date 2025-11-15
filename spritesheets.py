# Este es el script correcto, que usa la librería 'PIL'
import PIL.Image
import os
import json
import math
import pathlib
import sys

# Define el tamaño máximo de la textura de Roblox
SHEET_SIZE = (1024, 1024)

def pack_frames(frame_files, sheet_size):
    """
    Empaqueta los frames en hojas de sprites.
    """
    print(f"Empaquetando {len(frame_files)} frames...")
    sheets = []
    sheet_data = []
    
    current_sheet = PIL.Image.new("RGBA", sheet_size, (0, 0, 0, 0))
    current_x = 0
    current_y = 0
    max_row_height = 0
    
    frame_index = 0
    sheet_index = 0
    
    for frame_file in frame_files:
        frame_index += 1
        
        try:
            with PIL.Image.open(frame_file) as frame_img:
                frame_img.load()
                
            frame_width, frame_height = frame_img.size

            if current_x + frame_width > sheet_size[0]:
                # Mover a la siguiente fila
                current_x = 0
                current_y += max_row_height
                max_row_height = 0

            if current_y + frame_height > sheet_size[1]:
                # Mover a la siguiente hoja (sheet)
                print(f"Hoja {sheet_index} finalizada. Creando nueva hoja...")
                sheets.append(current_sheet)
                current_sheet = PIL.Image.new("RGBA", sheet_size, (0, 0, 0, 0))
                current_x = 0
                current_y = 0
                max_row_height = 0
                sheet_index += 1

            # Pegar el frame en la hoja actual
            current_sheet.paste(frame_img, (current_x, current_y))
            
            # Guardar datos del frame
            sheet_data.append({
                "sheet_index": sheet_index,
                "x": current_x,
                "y": current_y,
                "width": frame_width,
                "height": frame_height
            })

            current_x += frame_width
            if frame_height > max_row_height:
                max_row_height = frame_height

        except Exception as e:
            print(f"Error procesando el frame {frame_file}: {e}")
            
    sheets.append(current_sheet) # Añadir la última hoja
    print(f"Empaquetado completo. Total de hojas: {len(sheets)}")
    return sheets, sheet_data

def create_lua_data(sheet_data, fps, resolution, sheet_size_tuple, total_frames):
    """
    Genera el string del script de datos .lua.
    """
    print("Escribiendo datos Lua...")
    
    lua_output = []
    lua_output.append("return {")
    
    lua_output.append(f'\t["TotalFrames"] = {total_frames},')
    lua_output.append(f'\t["FPS"] = {fps},')
    
    lua_output.append('\t["Resolution"] = {')
    lua_output.append(f'\t\t["Width"] = {resolution[0]},')
    lua_output.append(f'\t\t["Height"] = {resolution[1]}')
    lua_output.append('\t},')
    
    lua_output.append('\t["SpriteSheetSize"] = {')
    lua_output.append(f'\t\t["Width"] = {sheet_size_tuple[0]},')
    lua_output.append(f'\t\t["Height"] = {sheet_size_tuple[1]}')
    lua_output.append('\t},')
    
    # Platzhalter für Bild-IDs (serán reemplazados en Roblox)
    lua_output.append('\t["Images"] = {')
    # Este script asume que las hojas se llamarán sheet_0, sheet_1, etc.
    # Necesitamos saber cuántas hojas hay.
    num_sheets = max(frame["sheet_index"] for frame in sheet_data) + 1
    for i in range(num_sheets):
        lua_output.append(f'\t\t"REPLACE_WITH_ASSET_ID_{i}",')
    lua_output.append('\t},')
    
    # Datos de los frames
    lua_output.append('\t["FrameData"] = {')
    frame_num = 1
    for frame in sheet_data:
        lua_output.append(f'\t\t[{frame_num}] = {{')
        lua_output.append(f'\t\t\t["ImageIndex"] = {frame["sheet_index"] + 1},') # Lua es 1-based
        lua_output.append(f'\t\t\t["Offset"] = {{["X"] = {frame["x"]}, ["Y"] = {frame["y"]}}},')
        lua_output.append(f'\t\t\t["Size"] = {{["X"] = {frame["width"]}, ["Y"] = {frame["height"]}}}')
        lua_output.append('\t\t},')
        frame_num += 1
        
    lua_output.append('\t}')
    lua_output.append('}')
    
    return "\n".join(lua_output)

def main():
    if len(sys.argv) < 2:
        print("Uso: python spritesheets.py <ruta_a_la_carpeta_de_frames>")
        return

    folder_path = pathlib.Path(sys.argv[1])
    if not folder_path.is_dir():
        print(f"Error: La ruta '{folder_path}' no es una carpeta válida.")
        return

    # Obtener todos los frames .png, ordenados
    print("Procesando frames...")
    try:
        frame_files = sorted(
            [f for f in folder_path.glob("*.png")],
            key=lambda f: int("".join(filter(str.isdigit, f.stem)))
        )
    except Exception as e:
        print(f"Error al ordenar los frames. Asegúrate de que se llamen 'frame_0001.png', etc. Error: {e}")
        return
        
    if not frame_files:
        print("No se encontraron archivos .png en la carpeta.")
        return

    # Obtener resolución del primer frame
    with PIL.Image.open(frame_files[0]) as img:
        resolution = img.size
    
    total_frames = len(frame_files)
    fps = 30 # Asumimos 30 FPS, ya que lo forzamos con ffmpeg
    
    # 1. Empaquetar frames en hojas
    sheets, sheet_data = pack_frames(frame_files, SHEET_SIZE)
    
    # 2. Guardar las hojas de sprites
    sheet_num = 0
    for sheet_img in sheets:
        sheet_filename = folder_path / f"sheet_{sheet_num}.png"
        sheet_img.save(sheet_filename)
        print(f"Hoja de sprites guardada: {sheet_filename}")
        sheet_num += 1
        
    # 3. Generar el archivo .lua
    lua_data = create_lua_data(sheet_data, fps, resolution, SHEET_SIZE, total_frames)
    
    # Guardar el archivo .lua
    lua_filename = folder_path / f"{folder_path.name}.lua"
    with open(lua_filename, "w") as f:
        f.write(lua_data)
        
    print(f"Script de datos Lua guardado: {lua_filename}")
    print("\n¡Proceso completado!")
    print(f"Sube los {len(sheets)} archivos 'sheet_X.png' a Roblox y actualiza el archivo .lua con sus IDs.")

if __name__ == "__main__":
    main()