# This is the correct script, which uses the 'PIL' library
import PIL.Image
import os
import json
import math
import pathlib
import sys

# Define Roblox's max texture size
SHEET_SIZE = (1024, 1024)

def pack_frames(frame_files, sheet_size):
    """
    Packs frames into sprite sheets.
    """
    print(f"Packing {len(frame_files)} frames...")
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
                # Move to the next row
                current_x = 0
                current_y += max_row_height
                max_row_height = 0

            if current_y + frame_height > sheet_size[1]:
                # Move to the next sheet
                print(f"Sheet {sheet_index} finished. Creating new sheet...")
                sheets.append(current_sheet)
                current_sheet = PIL.Image.new("RGBA", sheet_size, (0, 0, 0, 0))
                current_x = 0
                current_y = 0
                max_row_height = 0
                sheet_index += 1

            # Paste the frame onto the current sheet
            current_sheet.paste(frame_img, (current_x, current_y))
            
            # Save frame data
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
            print(f"Error processing frame {frame_file}: {e}")
            
    sheets.append(current_sheet) # Add the last sheet
    print(f"Packing complete. Total sheets: {len(sheets)}")
    return sheets, sheet_data

def create_lua_data(sheet_data, fps, resolution, sheet_size_tuple, total_frames):
    """
    Generates the .lua data script string.
    """
    print("Writing Lua data...")
    
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
    
    # Placeholders for Image IDs (to be replaced in Roblox)
    lua_output.append('\t["Images"] = {')
    num_sheets = max(frame["sheet_index"] for frame in sheet_data) + 1
    for i in range(num_sheets):
        lua_output.append(f'\t\t"REPLACE_WITH_ASSET_ID_{i}",')
    lua_output.append('\t},')
    
    # Frame data
    lua_output.append('\t["FrameData"] = {')
    frame_num = 1
    for frame in sheet_data:
        lua_output.append(f'\t\t[{frame_num}] = {{')
        lua_output.append(f'\t\t\t["ImageIndex"] = {frame["sheet_index"] + 1},') # Lua is 1-based
        lua_output.append(f'\t\t\t["Offset"] = {{["X"] = {frame["x"]}, ["Y"] = {frame["y"]}}},')
        lua_output.append(f'\t\t\t["Size"] = {{["X"] = {frame["width"]}, ["Y"] = {frame["height"]}}}')
        lua_output.append('\t\t},')
        frame_num += 1
        
    lua_output.append('\t}')
    lua_output.append('}')
    
    return "\n".join(lua_output)

def main():
    # --- MODIFICATION: Added [base_name] argument ---
    if len(sys.argv) < 2:
        print("Usage: python spritesheets.py <folder_path> [base_name]")
        print("Example: python spritesheets.py C:\\MyFrames\\intro_pngs vanity_intro")
        return

    folder_path = pathlib.Path(sys.argv[1])
    if not folder_path.is_dir():
        print(f"Error: Path '{folder_path}' is not a valid folder.")
        return

    # Check for the optional base_name argument
    if len(sys.argv) > 2:
        base_name = sys.argv[2]
    else:
        # Fallback to the folder's name if no base_name is provided
        base_name = folder_path.name 
    
    print(f"Processing frames from: {folder_path}")
    print(f"Using base name: {base_name}")
    # --- END MODIFICATION ---

    # Get all .png frames, sorted numerically
    print("Processing frames...")
    try:
        frame_files = sorted(
            [f for f in folder_path.glob("*.png")],
            key=lambda f: int("".join(filter(str.isdigit, f.stem)))
        )
    except Exception as e:
        print(f"Error sorting frames. Make sure they are named 'frame_0001.png', etc. Error: {e}")
        return
        
    if not frame_files:
        print("No .png files found in the folder.")
        return

    # Get resolution from the first frame
    with PIL.Image.open(frame_files[0]) as img:
        resolution = img.size
    
    total_frames = len(frame_files)
    fps = 30 # We assume 30 FPS, as forced by ffmpeg
    
    # 1. Pack frames into sheets
    sheets, sheet_data = pack_frames(frame_files, SHEET_SIZE)
    
    # 2. Save the sprite sheets
    sheet_num = 0
    for sheet_img in sheets:
        # --- MODIFICATION: Use base_name for the output file ---
        sheet_filename = folder_path / f"{base_name}_sheet_{sheet_num}.png"
        sheet_img.save(sheet_filename)
        print(f"Sprite sheet saved: {sheet_filename}")
        sheet_num += 1
        
    # 3. Generate the .lua file
    lua_data = create_lua_data(sheet_data, fps, resolution, SHEET_SIZE, total_frames)
    
    # Save the .lua file
    # --- MODIFICATION: Use base_name for the .lua file ---
    lua_filename = folder_path / f"{base_name}.lua"
    with open(lua_filename, "w") as f:
        f.write(lua_data)
        
    print(f"Lua data script saved: {lua_filename}")
    print("\nProcess complete!")
    print(f"Upload the {len(sheets)} '{base_name}_sheet_X.png' files to Roblox and update the .lua file with their IDs.")

if __name__ == "__main__":
    main()
